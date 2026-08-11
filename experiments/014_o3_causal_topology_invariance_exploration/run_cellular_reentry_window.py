#!/usr/bin/env python3
"""Cellular O3 reinjection-window exploration using the frozen E009 viability readout."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REPO_ROOT = ROOT.parents[1]
DAMAGE_AMPLITUDES = (0.45, 0.60, 0.75, 0.90, 1.05)
REINJECTION_MINUTES = (43.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0)
SEEDS = tuple(range(2026182001, 2026182033))


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e014_window", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def lineage_continuous_score(lineage: dict) -> float:
    if lineage["death_time"] is not None:
        return 0.0
    module_recovery = float(np.min(np.clip(lineage["recovery_ratio"], 0.0, 1.0)))
    late = lineage["times"] >= 100.0
    late_damage = float(np.median(lineage["states"][late, 5]))
    damage_factor = float(np.exp(-max(late_damage - 0.02, 0.0) / 0.08))
    return min(module_recovery, damage_factor)


def summarize(lineages):
    return {
        "alive_fraction": float(np.mean([item["alive"] for item in lineages])),
        "continuous_recovery_score": float(np.mean([lineage_continuous_score(item) for item in lineages])),
        "death_fraction": float(np.mean([item["death_time"] is not None for item in lineages])),
        "mean_minimum_module_recovery": float(np.mean([np.min(item["recovery_ratio"]) for item in lineages])),
    }


def main() -> None:
    core = load_cell_core()
    rows = []
    baseline_cache = {}
    for amplitude in DAMAGE_AMPLITUDES:
        base_config = core.DynamicsConfig(moderate_damage_amplitude=amplitude)
        baseline_cache[amplitude] = {
            condition: summarize([core.simulate(seed, base_config, condition) for seed in SEEDS])
            for condition in ("native", "joint_erased", "time_shifted")
        }
        for reinjection in REINJECTION_MINUTES:
            config = core.DynamicsConfig(
                moderate_damage_amplitude=amplitude,
                reinjection_minutes=reinjection,
            )
            reinjected = summarize([core.simulate(seed, config, "reinjected") for seed in SEEDS])
            records = {
                "intact": baseline_cache[amplitude]["native"],
                "removed": baseline_cache[amplitude]["joint_erased"],
                "mismatched_return": baseline_cache[amplitude]["time_shifted"],
                "correct_return": reinjected,
            }
            metrics = {}
            for readout in ("alive_fraction", "continuous_recovery_score"):
                values = {condition: record[readout] for condition, record in records.items()}
                edges = {
                    "intact_gt_removed": values["intact"] > values["removed"],
                    "intact_gt_mismatch": values["intact"] > values["mismatched_return"],
                    "correct_gt_removed": values["correct_return"] > values["removed"],
                    "correct_gt_mismatch": values["correct_return"] > values["mismatched_return"],
                }
                metrics[readout] = {
                    "values": values,
                    "edges": edges,
                    "causal_pass": all(edges.values()),
                    "causal_margin": min(values["intact"], values["correct_return"]) - max(values["removed"], values["mismatched_return"]),
                }
            rows.append({
                "damage_amplitude": amplitude,
                "reinjection_minutes": reinjection,
                "joint_erasure_duration_minutes": reinjection - base_config.damage_start_minutes,
                "post_reinjection_duration_minutes": base_config.duration_minutes - reinjection,
                "conditions": records,
                "metrics": metrics,
            })

    windows = []
    for amplitude in DAMAGE_AMPLITUDES:
        selected = [row for row in rows if row["damage_amplitude"] == amplitude]
        for readout in ("alive_fraction", "continuous_recovery_score"):
            passing = [row["reinjection_minutes"] for row in selected if row["metrics"][readout]["causal_pass"]]
            windows.append({
                "damage_amplitude": amplitude,
                "readout": readout,
                "passing_reinjection_minutes": passing,
                "latest_passing_reinjection_minutes": max(passing) if passing else None,
                "earliest_nonpassing_reinjection_minutes": min((row["reinjection_minutes"] for row in selected if not row["metrics"][readout]["causal_pass"]), default=None),
            })

    def aggregate(readout):
        return {
            "configurations": len(rows),
            "pass_fraction": float(np.mean([row["metrics"][readout]["causal_pass"] for row in rows])),
            "minimum_margin": min(row["metrics"][readout]["causal_margin"] for row in rows),
            "maximum_margin": max(row["metrics"][readout]["causal_margin"] for row in rows),
        }
    summary = {
        "schema": "siel-e014-cellular-reentry-window-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "engine": "frozen E009 reduced stochastic cell dynamics",
            "seeds": list(SEEDS),
            "damage_amplitudes": list(DAMAGE_AMPLITUDES),
            "reinjection_minutes": list(REINJECTION_MINUTES),
            "primary_readout": "unchanged E009 alive criterion",
            "secondary_readout": "continuous module-recovery and late-damage diagnostic selected for exploration",
        },
        "alive_fraction": aggregate("alive_fraction"),
        "continuous_recovery_score": aggregate("continuous_recovery_score"),
        "windows": windows,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "seeds_and_phase_axes_selected_after_E009": True,
            "continuous_score_not_previously_registered": True,
            "reduced_model_not_living_cell_confirmation": True,
        },
    }
    (RESULTS / "cellular_reentry_window_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cellular O3 reinjection-window exploration",
        "",
        f"Alive-readout pass fraction: `{summary['alive_fraction']['pass_fraction']:.6f}`.",
        f"Continuous-readout pass fraction: `{summary['continuous_recovery_score']['pass_fraction']:.6f}`.",
        "",
        "All passing and nonpassing damage/reinjection combinations are retained. This is result-informed local exploration in the frozen reduced E009 model.",
    ]
    (RESULTS / "CELLULAR_REENTRY_WINDOW_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "alive_fraction": summary["alive_fraction"],
        "continuous_recovery_score": summary["continuous_recovery_score"],
        "windows": windows,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
