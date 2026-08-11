#!/usr/bin/env python3
"""Exact transition-matrix grid covariance for the molecular re-entry topology."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FACTORS = (1, 2, 4)


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    base = load("e014_base_exact_grid", "run.py")
    fingerprint = load("e014_fingerprint_exact_grid", "run_distributional_fingerprint.py")
    grid = load("e014_grid_exact_grid", "run_grid_refinement_covariance.py")
    phase = load("e014_phase_exact_grid", "run_molecular_reentry_phase_map.py")
    profiles = base.load_profiles()
    stochastic = json.loads((RESULTS / "grid_refinement_covariance_summary.json").read_text())
    selection_lookup = {(item["profile"], float(item["temperature"])): item for item in stochastic["selections"]}
    physical = load("e014_physical_exact_grid", "run_physical_mismatch_audit.py")
    rows = []
    for (profile_name, temperature), selection in sorted(selection_lookup.items()):
        profile = profiles[profile_name]
        original_native = np.asarray(profile["native"], dtype=float)
        original_reference = np.asarray(profile["reference"], dtype=float)
        original_coordinates = np.asarray(profile["a_values"], dtype=float)
        original_alternative = physical.alternatives_for(profile_name, profile, profiles)[selection["alternative"]][0]
        adjacent_original = original_alternative if selection["alternative"].startswith("adjacent_b_") else None
        for factor in FACTORS:
            coordinates = np.linspace(original_coordinates[0], original_coordinates[-1], (len(original_coordinates) - 1) * factor + 1)
            native = grid.refine(original_native, factor)
            reference = grid.refine(original_reference, factor)
            candidate = native - reference
            adjacent = grid.refine(adjacent_original, factor) if adjacent_original is not None else None
            alternative_candidate = grid.transformed_candidate(selection["alternative"], coordinates, candidate, factor, adjacent)
            mismatch = reference + alternative_candidate
            removal_steps = 20 * factor * factor
            return_steps = 80 * factor * factor
            initial = np.zeros(len(native), dtype=float)
            initial[max(np.flatnonzero(np.abs(native - float(np.min(native))) <= 1e-10).tolist())] = 1.0
            native_matrix = phase.transition(native, temperature)
            reference_matrix = phase.transition(reference, temperature)
            mismatch_matrix = phase.transition(mismatch, temperature)
            intact = phase.propagate(initial, native_matrix, removal_steps + return_steps)
            removed = phase.propagate(initial, reference_matrix, removal_steps + return_steps)
            removed_state = phase.propagate(initial, reference_matrix, removal_steps)
            correct = phase.propagate(removed_state, native_matrix, return_steps)
            mismatched = phase.propagate(removed_state, mismatch_matrix, return_steps)
            scores = {
                "intact": 1.0,
                "removed": fingerprint.js_similarity(removed, intact),
                "mismatched_return": fingerprint.js_similarity(mismatched, intact),
                "correct_return": fingerprint.js_similarity(correct, intact),
            }
            causal = base.causal_metrics(scores)
            rows.append({
                "profile": profile_name,
                "basis": profile["basis"],
                "temperature": temperature,
                "factor": factor,
                "grid_points": len(native),
                "alternative": selection["alternative"],
                "scores": scores,
                "causal": causal,
            })
    by_factor = {
        str(factor): {
            "configurations": len(selected := [row for row in rows if row["factor"] == factor]),
            "pass_fraction": float(np.mean([row["causal"]["pass"] for row in selected])),
            "minimum_margin": min(row["causal"]["causal_margin"] for row in selected),
            "median_margin": float(np.median([row["causal"]["causal_margin"] for row in selected])),
        }
        for factor in FACTORS
    }
    summary = {
        "schema": "siel-e014-exact-grid-covariance-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "propagation": "exact finite-state transition matrices",
            "whole_fingerprint": "normalized Jensen-Shannon similarity to matched intact dynamics at equal total time",
            "grid_factors": list(FACTORS),
            "time_scaling": "removal and return steps multiplied by factor squared",
            "same_alternative_selections_as_stochastic_grid_audit": True,
        },
        "by_factor": by_factor,
        "all_configurations_pass": all(row["causal"]["pass"] for row in rows),
        "overall_minimum_margin": min(row["causal"]["causal_margin"] for row in rows),
        "stochastic_nonpass_count": sum(not row["causal"]["pass"] for row in stochastic["rows"]),
        "exact_nonpass_count": sum(not row["causal"]["pass"] for row in rows),
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "exact_followup_triggered_by_stochastic_nonpass": True,
            "linear_interpolation_is_only_a_representation_control": True,
        },
    }
    (RESULTS / "exact_grid_covariance_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Exact grid-refinement covariance exploration",
        "",
        f"All configurations pass: `{summary['all_configurations_pass']}`.",
        f"Overall minimum causal margin: `{summary['overall_minimum_margin']:.9f}`.",
        f"Stochastic nonpasses: `{summary['stochastic_nonpass_count']}`; exact nonpasses: `{summary['exact_nonpass_count']}`.",
        "",
        "This exact audit separates representation covariance from finite-seed classification noise.",
        "It remains result-informed local exploration.",
    ]
    (RESULTS / "EXACT_GRID_COVARIANCE_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all_configurations_pass": summary["all_configurations_pass"],
        "overall_minimum_margin": summary["overall_minimum_margin"],
        "stochastic_nonpass_count": summary["stochastic_nonpass_count"],
        "exact_nonpass_count": summary["exact_nonpass_count"],
        "by_factor": by_factor,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
