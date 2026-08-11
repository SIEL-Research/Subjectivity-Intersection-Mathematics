#!/usr/bin/env python3
"""Stress the molecular Hellinger re-entry claim across horizons and grids."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FACTORS = (1, 2, 4)
BASE_REMOVALS = (10, 20, 40, 80)
BASE_INITIAL_RETURN = 10
BASE_FINAL_RETURNS = (25, 50, 100, 200, 400)


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def hellinger_similarity(observed, target):
    distance = float(np.sqrt(0.5 * np.sum((np.sqrt(observed) - np.sqrt(target)) ** 2)))
    return 1.0 - distance


def main() -> None:
    base = load("e014_base_hellinger_stress", "run.py")
    grid = load("e014_grid_hellinger_stress", "run_grid_refinement_covariance.py")
    phase = load("e014_phase_hellinger_stress", "run_molecular_reentry_phase_map.py")
    physical = load("e014_physical_hellinger_stress", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    selection_source = json.loads((RESULTS / "grid_refinement_covariance_summary.json").read_text())
    selections = {(item["profile"], float(item["temperature"])): item for item in selection_source["selections"]}
    rows = []
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
            matrices = {
                "native": phase.transition(native, temperature),
                "reference": phase.transition(reference, temperature),
                "mismatch": phase.transition(mismatch, temperature),
            }
            initial = np.zeros(len(native), dtype=float)
            initial[max(np.flatnonzero(np.abs(native - float(np.min(native))) <= 1e-10).tolist())] = 1.0
            for base_removal in BASE_REMOVALS:
                removal = base_removal * factor * factor
                removed_at_return = phase.propagate(initial, matrices["reference"], removal)
                points = {}
                for base_return in (BASE_INITIAL_RETURN,) + BASE_FINAL_RETURNS:
                    returned = base_return * factor * factor
                    intact = phase.propagate(initial, matrices["native"], removal + returned)
                    distributions = {
                        "removed": phase.propagate(initial, matrices["reference"], removal + returned),
                        "mismatched_return": phase.propagate(removed_at_return, matrices["mismatch"], returned),
                        "correct_return": phase.propagate(removed_at_return, matrices["native"], returned),
                    }
                    points[base_return] = {condition: hellinger_similarity(distribution, intact) for condition, distribution in distributions.items()}
                start = points[BASE_INITIAL_RETURN]
                for endpoint in BASE_FINAL_RETURNS:
                    end = points[endpoint]
                    fractions = {
                        condition: (end[condition] - start[condition]) / max(1.0 - start[condition], 1e-12)
                        for condition in ("removed", "mismatched_return", "correct_return")
                    }
                    rows.append({
                        "profile": profile_name,
                        "temperature": temperature,
                        "factor": factor,
                        "base_removal_steps": base_removal,
                        "base_endpoint_return_steps": endpoint,
                        "alternative": selection["alternative"],
                        "initial_scores": start,
                        "endpoint_scores": end,
                        "headroom_normalized_recovery": fractions,
                        "correct_recovers": end["correct_return"] > start["correct_return"],
                        "persistent_specificity": (
                            start["correct_return"] > max(start["removed"], start["mismatched_return"])
                            and end["correct_return"] > max(end["removed"], end["mismatched_return"])
                        ),
                        "correct_interaction_exceeds_nulls": fractions["correct_return"] > max(fractions["removed"], fractions["mismatched_return"]),
                    })

    by_endpoint = {}
    for endpoint in BASE_FINAL_RETURNS:
        selected = [row for row in rows if row["base_endpoint_return_steps"] == endpoint]
        by_endpoint[str(endpoint)] = {
            "configurations": len(selected),
            "correct_recovers_fraction": float(np.mean([row["correct_recovers"] for row in selected])),
            "persistent_specificity_fraction": float(np.mean([row["persistent_specificity"] for row in selected])),
            "interaction_fraction": float(np.mean([row["correct_interaction_exceeds_nulls"] for row in selected])),
            "all_three_fraction": float(np.mean([
                row["correct_recovers"] and row["persistent_specificity"] and row["correct_interaction_exceeds_nulls"]
                for row in selected
            ])),
        }
    first_all_pass_endpoint = next((endpoint for endpoint in BASE_FINAL_RETURNS if by_endpoint[str(endpoint)]["all_three_fraction"] == 1.0), None)
    summary = {
        "schema": "siel-e014-hellinger-horizon-stress-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_temperature_pairs": len(selections),
            "grid_factors": list(FACTORS),
            "base_removal_steps": list(BASE_REMOVALS),
            "base_initial_return_steps": BASE_INITIAL_RETURN,
            "base_endpoint_return_steps": list(BASE_FINAL_RETURNS),
            "readout": "Hellinger similarity to matched intact distribution",
            "exact_transition_propagation": True,
        },
        "by_endpoint": by_endpoint,
        "first_endpoint_with_all_configurations_passing_all_three_conditions": first_all_pass_endpoint,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "Hellinger_readout_and_axes_selected_after_prior_exploration": True,
            "future_confirmation_requires_frozen_horizon_and_new_targets": True,
        },
    }
    (RESULTS / "hellinger_horizon_stress_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Hellinger re-entry horizon stress",
        "",
        f"First endpoint with universal recovery, specificity, and interaction: `{first_all_pass_endpoint}` base return steps.",
        "",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "HELLINGER_HORIZON_STRESS_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"by_endpoint": by_endpoint, "first_all_pass_endpoint": first_all_pass_endpoint}, sort_keys=True))


if __name__ == "__main__":
    main()
