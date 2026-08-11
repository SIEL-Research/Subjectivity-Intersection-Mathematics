#!/usr/bin/env python3
"""Representation covariance of the molecular return-identity interaction."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FACTORS = (1, 2, 4)
BASE_REMOVAL = 20
BASE_INITIAL_RETURN = 10
BASE_FINAL_RETURN = 100


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def similarities(fingerprint, observed, target, coordinates):
    hellinger = float(np.sqrt(0.5 * np.sum((np.sqrt(observed) - np.sqrt(target)) ** 2)))
    total_variation = 0.5 * float(np.sum(np.abs(observed - target)))
    widths = np.diff(coordinates)
    wasserstein = float(np.sum(np.abs(np.cumsum(observed)[:-1] - np.cumsum(target)[:-1]) * widths))
    return {
        "js_similarity": fingerprint.js_similarity(observed, target),
        "hellinger_similarity": 1.0 - hellinger,
        "total_variation_similarity": 1.0 - total_variation,
        "wasserstein_similarity": 1.0 - wasserstein / float(coordinates[-1] - coordinates[0]),
    }


def main() -> None:
    base = load("e014_base_interaction_covariance", "run.py")
    fingerprint = load("e014_fingerprint_interaction_covariance", "run_distributional_fingerprint.py")
    grid = load("e014_grid_interaction_covariance", "run_grid_refinement_covariance.py")
    phase = load("e014_phase_interaction_covariance", "run_molecular_reentry_phase_map.py")
    physical = load("e014_physical_interaction_covariance", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    selection_source = json.loads((RESULTS / "grid_refinement_covariance_summary.json").read_text())
    selections = {(item["profile"], float(item["temperature"])): item for item in selection_source["selections"]}
    rows = []
    methods = ("js_similarity", "hellinger_similarity", "total_variation_similarity", "wasserstein_similarity")
    for (profile_name, temperature), selection in sorted(selections.items()):
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
            mismatch = reference + grid.transformed_candidate(selection["alternative"], coordinates, candidate, factor, adjacent)
            removal = BASE_REMOVAL * factor * factor
            return_points = (BASE_INITIAL_RETURN * factor * factor, BASE_FINAL_RETURN * factor * factor)
            initial = np.zeros(len(native), dtype=float)
            initial[max(np.flatnonzero(np.abs(native - float(np.min(native))) <= 1e-10).tolist())] = 1.0
            matrices = {
                "native": phase.transition(native, temperature),
                "reference": phase.transition(reference, temperature),
                "mismatch": phase.transition(mismatch, temperature),
            }
            removed_at_return = phase.propagate(initial, matrices["reference"], removal)
            point_scores = []
            for returned in return_points:
                intact = phase.propagate(initial, matrices["native"], removal + returned)
                distributions = {
                    "removed": phase.propagate(initial, matrices["reference"], removal + returned),
                    "mismatched_return": phase.propagate(removed_at_return, matrices["mismatch"], returned),
                    "correct_return": phase.propagate(removed_at_return, matrices["native"], returned),
                }
                point_scores.append({condition: similarities(fingerprint, distribution, intact, coordinates) for condition, distribution in distributions.items()})
            interactions = {}
            for method in methods:
                fractions = {}
                for condition in ("removed", "mismatched_return", "correct_return"):
                    start = point_scores[0][condition][method]
                    end = point_scores[1][condition][method]
                    fractions[condition] = (end - start) / max(1.0 - start, 1e-12)
                interactions[method] = {
                    "headroom_normalized_recovery": fractions,
                    "correct_minus_mismatch": fractions["correct_return"] - fractions["mismatched_return"],
                    "correct_minus_removed": fractions["correct_return"] - fractions["removed"],
                    "pass": fractions["correct_return"] > max(fractions["mismatched_return"], fractions["removed"]),
                    "correct_recovers": point_scores[1]["correct_return"][method] > point_scores[0]["correct_return"][method],
                    "correct_dominates_mismatch_at_both_horizons": all(
                        point["correct_return"][method] > point["mismatched_return"][method]
                        for point in point_scores
                    ),
                    "correct_dominates_removed_at_both_horizons": all(
                        point["correct_return"][method] > point["removed"][method]
                        for point in point_scores
                    ),
                }
            rows.append({
                "profile": profile_name,
                "temperature": temperature,
                "factor": factor,
                "grid_points": len(native),
                "alternative": selection["alternative"],
                "initial_scores": point_scores[0],
                "final_scores": point_scores[1],
                "interactions": interactions,
            })

    by_method_factor = {}
    for method in methods:
        by_method_factor[method] = {}
        for factor in FACTORS:
            selected = [row["interactions"][method] for row in rows if row["factor"] == factor]
            by_method_factor[method][str(factor)] = {
                "configurations": len(selected),
                "pass_fraction": float(np.mean([item["pass"] for item in selected])),
                "minimum_correct_minus_mismatch": min(item["correct_minus_mismatch"] for item in selected),
                "minimum_correct_minus_removed": min(item["correct_minus_removed"] for item in selected),
                "recovery_and_persistent_dominance_fraction": float(np.mean([
                    item["correct_recovers"]
                    and item["correct_dominates_mismatch_at_both_horizons"]
                    and item["correct_dominates_removed_at_both_horizons"]
                    for item in selected
                ])),
                "final_specificity_fraction": float(np.mean([
                    row["final_scores"]["correct_return"][method]
                    > max(
                        row["final_scores"]["removed"][method],
                        row["final_scores"]["mismatched_return"][method],
                    )
                    for row in rows if row["factor"] == factor
                ])),
            }
    summary = {
        "schema": "siel-e014-interaction-representation-covariance-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "grid_factors": list(FACTORS),
            "readouts": list(methods),
            "exact_transition_propagation": True,
            "base_removal_steps": BASE_REMOVAL,
            "base_return_interval": [BASE_INITIAL_RETURN, BASE_FINAL_RETURN],
            "diffusive_time_scaling": "all durations multiplied by factor squared",
        },
        "all_methods_all_factors_all_configurations_pass": all(row["interactions"][method]["pass"] for row in rows for method in methods),
        "all_methods_all_factors_show_recovery_and_persistent_dominance": all(
            row["interactions"][method]["correct_recovers"]
            and row["interactions"][method]["correct_dominates_mismatch_at_both_horizons"]
            and row["interactions"][method]["correct_dominates_removed_at_both_horizons"]
            for row in rows for method in methods
        ),
        "by_method_factor": by_method_factor,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "readouts_and_horizon_selected_after_prior_exploration": True,
            "interpolated_grids_are_representation_controls_not_new_quantum_chemistry": True,
        },
    }
    (RESULTS / "interaction_representation_covariance_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Return-identity interaction representation covariance",
        "",
        f"All readouts, factors, and configurations pass: `{summary['all_methods_all_factors_all_configurations_pass']}`.",
        f"All show correct recovery plus persistent dominance: `{summary['all_methods_all_factors_show_recovery_and_persistent_dominance']}`.",
        "",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "INTERACTION_REPRESENTATION_COVARIANCE_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all_pass": summary["all_methods_all_factors_all_configurations_pass"],
        "all_recovery_and_dominance": summary["all_methods_all_factors_show_recovery_and_persistent_dominance"],
        "by_method_factor": by_method_factor,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
