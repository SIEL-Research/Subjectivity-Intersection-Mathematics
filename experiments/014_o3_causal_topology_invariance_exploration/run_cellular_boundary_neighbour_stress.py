#!/usr/bin/env python3
"""Stress cellular boundary neighbours while preserving 0.675 and 0.825 as untouched candidates."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REPO_ROOT = ROOT.parents[1]
AMPLITUDES = (0.625, 0.650, 0.700, 0.800, 0.850, 0.875)
RESERVED_UNEXECUTED_AMPLITUDES = (0.675, 0.825)
REINJECTION_MINUTES = (43.0, 45.0, 50.0, 55.0, 60.0)
SEEDS = tuple(range(2026186001, 2026186065))


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e014_boundary_stress", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def score(lineages):
    return {
        "alive_fraction": float(np.mean([item["alive"] for item in lineages])),
        "alive_count": int(sum(item["alive"] for item in lineages)),
        "lineage_count": len(lineages),
    }


def main() -> None:
    if any(value in AMPLITUDES for value in RESERVED_UNEXECUTED_AMPLITUDES):
        raise RuntimeError("reserved amplitude entered executable stress registry")
    core = load_cell_core()
    rows = []
    for amplitude in AMPLITUDES:
        base_config = core.DynamicsConfig(moderate_damage_amplitude=amplitude)
        nulls = {
            "intact": score([core.simulate(seed, base_config, "native") for seed in SEEDS]),
            "removed": score([core.simulate(seed, base_config, "joint_erased") for seed in SEEDS]),
            "mismatched_return": score([core.simulate(seed, base_config, "time_shifted") for seed in SEEDS]),
        }
        for reinjection in REINJECTION_MINUTES:
            config = core.DynamicsConfig(moderate_damage_amplitude=amplitude, reinjection_minutes=reinjection)
            correct = score([core.simulate(seed, config, "reinjected") for seed in SEEDS])
            values = {
                "intact": nulls["intact"]["alive_fraction"],
                "removed": nulls["removed"]["alive_fraction"],
                "mismatched_return": nulls["mismatched_return"]["alive_fraction"],
                "correct_return": correct["alive_fraction"],
            }
            margin = values["correct_return"] - max(values["removed"], values["mismatched_return"])
            rows.append({
                "damage_amplitude": amplitude,
                "reinjection_minutes": reinjection,
                "scores": values,
                "correct_alive_count": correct["alive_count"],
                "specificity_margin": margin,
                "specificity_pass": margin > 0.0,
            })
    boundaries = []
    for amplitude in AMPLITUDES:
        selected = [row for row in rows if row["damage_amplitude"] == amplitude]
        passing = [row["reinjection_minutes"] for row in selected if row["specificity_pass"]]
        boundaries.append({
            "damage_amplitude": amplitude,
            "latest_passing_reinjection": max(passing) if passing else None,
            "earliest_failing_reinjection": min((row["reinjection_minutes"] for row in selected if not row["specificity_pass"]), default=None),
            "passing_reinjections": passing,
        })
    numeric_boundaries = [item for item in boundaries if item["latest_passing_reinjection"] is not None]
    x = np.asarray([item["damage_amplitude"] for item in numeric_boundaries])
    y = np.asarray([item["latest_passing_reinjection"] for item in numeric_boundaries])
    slope, intercept = np.polyfit(x, y, 1)
    reserved_predictions = {
        str(value): float(intercept + slope * value) for value in RESERVED_UNEXECUTED_AMPLITUDES
    }
    summary = {
        "schema": "siel-e014-cellular-boundary-neighbour-stress-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "executed_amplitudes": list(AMPLITUDES),
            "reserved_unexecuted_amplitudes": list(RESERVED_UNEXECUTED_AMPLITUDES),
            "reinjection_minutes": list(REINJECTION_MINUTES),
            "seeds": list(SEEDS),
            "primary_readout": "unchanged E009 alive criterion",
        },
        "boundaries": boundaries,
        "least_squares_boundary": {"slope": float(slope), "intercept": float(intercept)},
        "reserved_amplitude_predictions_without_execution": reserved_predictions,
        "monotone_nonincreasing_latest_boundary": all(
            right["latest_passing_reinjection"] is None
            or left["latest_passing_reinjection"] is None
            or right["latest_passing_reinjection"] <= left["latest_passing_reinjection"]
            for left, right in zip(boundaries, boundaries[1:])
        ),
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "reserved_amplitudes_not_executed": True,
            "new_seed_stress_selected_after_prior_boundary_map": True,
            "reduced_model_not_living_cell_confirmation": True,
        },
    }
    (RESULTS / "cellular_boundary_neighbour_stress_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cellular boundary-neighbour stress",
        "",
        f"Reserved amplitudes remained unexecuted: `{list(RESERVED_UNEXECUTED_AMPLITUDES)}`.",
        f"Boundary is monotone nonincreasing: `{summary['monotone_nonincreasing_latest_boundary']}`.",
        f"Reserved predictions: `{reserved_predictions}`.",
        "",
        "This is result-informed local exploration in the frozen reduced E009 model.",
    ]
    (RESULTS / "CELLULAR_BOUNDARY_NEIGHBOUR_STRESS_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "boundaries": boundaries,
        "monotone": summary["monotone_nonincreasing_latest_boundary"],
        "fit": summary["least_squares_boundary"],
        "reserved_predictions": reserved_predictions,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
