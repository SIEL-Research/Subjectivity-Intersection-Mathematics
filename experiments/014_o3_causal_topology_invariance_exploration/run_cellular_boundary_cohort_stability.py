#!/usr/bin/env python3
"""Independent-cohort stability around reserved cellular boundary targets."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REPO_ROOT = ROOT.parents[1]
AMPLITUDES = (0.650, 0.700, 0.800, 0.850)
RESERVED_UNEXECUTED_AMPLITUDES = (0.675, 0.825)
REINJECTION_MINUTES = (45.0, 50.0)
COHORT_STARTS = (2026187001, 2026187033, 2026187065, 2026187097)
COHORT_SIZE = 32


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e014_boundary_cohorts", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def alive_fraction(core, config, condition, seeds):
    return float(np.mean([core.simulate(seed, config, condition)["alive"] for seed in seeds]))


def main() -> None:
    if any(value in AMPLITUDES for value in RESERVED_UNEXECUTED_AMPLITUDES):
        raise RuntimeError("reserved target entered stability execution")
    core = load_cell_core()
    rows = []
    for amplitude in AMPLITUDES:
        for cohort_number, start in enumerate(COHORT_STARTS, 1):
            seeds = tuple(range(start, start + COHORT_SIZE))
            base = core.DynamicsConfig(moderate_damage_amplitude=amplitude)
            null_scores = {
                "removed": alive_fraction(core, base, "joint_erased", seeds),
                "mismatched_return": alive_fraction(core, base, "time_shifted", seeds),
            }
            for reinjection in REINJECTION_MINUTES:
                config = core.DynamicsConfig(moderate_damage_amplitude=amplitude, reinjection_minutes=reinjection)
                correct = alive_fraction(core, config, "reinjected", seeds)
                margin = correct - max(null_scores.values())
                rows.append({
                    "damage_amplitude": amplitude,
                    "cohort": cohort_number,
                    "seed_range": [start, start + COHORT_SIZE - 1],
                    "reinjection_minutes": reinjection,
                    "correct_alive_fraction": correct,
                    "removed_alive_fraction": null_scores["removed"],
                    "mismatched_alive_fraction": null_scores["mismatched_return"],
                    "specificity_margin": margin,
                    "specificity_pass": margin > 0.0,
                })
    expected = []
    for row in rows:
        predicted_pass = row["reinjection_minutes"] == 45.0
        expected.append(row["specificity_pass"] == predicted_pass)
    summary = {
        "schema": "siel-e014-cellular-boundary-cohort-stability-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "executed_amplitudes": list(AMPLITUDES),
            "reserved_unexecuted_amplitudes": list(RESERVED_UNEXECUTED_AMPLITUDES),
            "reinjection_minutes": list(REINJECTION_MINUTES),
            "cohort_starts": list(COHORT_STARTS),
            "cohort_size": COHORT_SIZE,
            "expected_neighbour_pattern": "45-minute specificity pass and 50-minute specificity nonpass",
        },
        "all_amplitude_cohort_cells_match_expected_pattern": all(expected),
        "matching_cells": sum(expected),
        "total_cells": len(expected),
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "reserved_amplitudes_not_executed": True,
            "cohort_stress_selected_after_neighbour_map": True,
            "reduced_model_not_living_cell_confirmation": True,
        },
    }
    (RESULTS / "cellular_boundary_cohort_stability_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cellular boundary cohort stability",
        "",
        f"Cells matching 45-pass/50-nonpass pattern: `{summary['matching_cells']}/{summary['total_cells']}`.",
        f"Reserved amplitudes remained unexecuted: `{list(RESERVED_UNEXECUTED_AMPLITUDES)}`.",
        "",
        "This is result-informed local exploration in the frozen reduced E009 model.",
    ]
    (RESULTS / "CELLULAR_BOUNDARY_COHORT_STABILITY_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all_match": summary["all_amplitude_cohort_cells_match_expected_pattern"],
        "matching_cells": summary["matching_cells"],
        "total_cells": summary["total_cells"],
        "rows": rows,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
