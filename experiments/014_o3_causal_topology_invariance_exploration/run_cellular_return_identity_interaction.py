#!/usr/bin/env python3
"""Cellular return-identity by recovery-opportunity interaction exploration."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REPO_ROOT = ROOT.parents[1]
SEEDS = tuple(range(2026184001, 2026184033))
SCENARIOS = (
    {"damage_amplitude": 0.60, "reinjection_minutes": 50.0},
    {"damage_amplitude": 0.75, "reinjection_minutes": 45.0},
    {"damage_amplitude": 0.90, "reinjection_minutes": 43.0},
)


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e014_identity_interaction", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def paired_state_similarity(native_lineages, condition_lineages, index):
    distances = []
    for native, condition in zip(native_lineages, condition_lineages):
        native_modules = native["modules"][index]
        condition_modules = condition["modules"][index]
        native_damage = native["states"][index, 5]
        condition_damage = condition["states"][index, 5]
        native_biomass = native["states"][index, 6]
        condition_biomass = condition["states"][index, 6]
        difference = np.concatenate((
            condition_modules - native_modules,
            [(condition_damage - native_damage) / 0.10],
            [condition_biomass - native_biomass],
        ))
        distances.append(float(np.linalg.norm(difference) / np.sqrt(len(difference))))
    return float(np.exp(-np.mean(distances)))


def main() -> None:
    core = load_cell_core()
    rows = []
    interactions = []
    for scenario in SCENARIOS:
        amplitude = scenario["damage_amplitude"]
        reinjection = scenario["reinjection_minutes"]
        config = core.DynamicsConfig(
            moderate_damage_amplitude=amplitude,
            reinjection_minutes=reinjection,
        )
        lineages = {
            condition: [core.simulate(seed, config, condition) for seed in SEEDS]
            for condition in ("native", "joint_erased", "time_shifted", "reinjected")
        }
        horizon_candidates = (reinjection + 1.0, reinjection + 3.0, reinjection + 5.0, reinjection + 10.0, reinjection + 20.0, reinjection + 40.0, 150.0)
        horizons = sorted({min(150.0, value) for value in horizon_candidates})
        scenario_rows = []
        for horizon in horizons:
            index = int(round(horizon / config.dt_minutes))
            scores = {
                "intact": 1.0,
                "removed": paired_state_similarity(lineages["native"], lineages["joint_erased"], index),
                "mismatched_return": paired_state_similarity(lineages["native"], lineages["time_shifted"], index),
                "correct_return": paired_state_similarity(lineages["native"], lineages["reinjected"], index),
            }
            record = {
                "damage_amplitude": amplitude,
                "reinjection_minutes": reinjection,
                "observation_minutes": horizon,
                "post_reinjection_minutes": horizon - reinjection,
                "scores": scores,
                "causal_margin": scores["correct_return"] - max(scores["removed"], scores["mismatched_return"]),
            }
            rows.append(record)
            scenario_rows.append(record)
        first, last = scenario_rows[0], scenario_rows[-1]
        fractions = {}
        for condition in ("removed", "mismatched_return", "correct_return"):
            initial = first["scores"][condition]
            final = last["scores"][condition]
            fractions[condition] = (final - initial) / max(1.0 - initial, 1e-12)
        interactions.append({
            "damage_amplitude": amplitude,
            "reinjection_minutes": reinjection,
            "initial_horizon": first["observation_minutes"],
            "final_horizon": last["observation_minutes"],
            "headroom_normalized_recovery": fractions,
            "correct_exceeds_mismatch": fractions["correct_return"] > fractions["mismatched_return"],
            "correct_exceeds_removed": fractions["correct_return"] > fractions["removed"],
            "correct_final_specificity": last["scores"]["correct_return"] > max(last["scores"]["removed"], last["scores"]["mismatched_return"]),
        })

    summary = {
        "schema": "siel-e014-cellular-return-identity-interaction-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "engine": "frozen E009 reduced stochastic cell dynamics",
            "scenarios": list(SCENARIOS),
            "seeds": list(SEEDS),
            "fingerprint": "paired five-component state fingerprint: three module observables, damage scaled by the E009 death scale, and biomass",
            "interaction": "fraction of remaining similarity headroom closed between the first post-reinjection horizon and 150 minutes",
        },
        "all_scenarios_correct_exceeds_mismatch": all(item["correct_exceeds_mismatch"] for item in interactions),
        "all_scenarios_correct_exceeds_removed": all(item["correct_exceeds_removed"] for item in interactions),
        "all_scenarios_final_specificity": all(item["correct_final_specificity"] for item in interactions),
        "interactions": interactions,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "scenarios_selected_from_prior_reinjection_window": True,
            "paired_state_fingerprint_selected_for_this_exploration": True,
            "reduced_model_not_living_cell_confirmation": True,
        },
    }
    (RESULTS / "cellular_return_identity_interaction_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cellular return-identity interaction exploration",
        "",
        f"Correct headroom-normalized recovery exceeds mismatch in every scenario: `{summary['all_scenarios_correct_exceeds_mismatch']}`.",
        f"Correct recovery exceeds removal in every scenario: `{summary['all_scenarios_correct_exceeds_removed']}`.",
        f"Final correct-return specificity holds in every scenario: `{summary['all_scenarios_final_specificity']}`.",
        "",
        "This is result-informed local exploration in the frozen reduced E009 model.",
    ]
    (RESULTS / "CELLULAR_RETURN_IDENTITY_INTERACTION_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all_correct_gt_mismatch": summary["all_scenarios_correct_exceeds_mismatch"],
        "all_correct_gt_removed": summary["all_scenarios_correct_exceeds_removed"],
        "all_final_specificity": summary["all_scenarios_final_specificity"],
        "interactions": interactions,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
