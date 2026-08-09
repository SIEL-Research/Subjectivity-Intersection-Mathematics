#!/usr/bin/env python3
"""Experiment 009 frozen constitutive-cell-closure runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

import core

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"

# These E009 confirmation seeds are disjoint from LIFE-004 development and
# confirmation seeds and must not be executed before the preregistration
# release and DOI are public and verified.
TRAIN_SEEDS = tuple(range(2026090900, 2026090916))
TEST_SEEDS = tuple(range(2026091900, 2026091932))
CONDITIONS = ("native", "joint_erased", "time_shifted", "reinjected", "nonliving")


class ProvenanceError(RuntimeError):
    """Raised when the public frozen package does not match its manifest."""


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_registration():
    with MANIFEST.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema") != "siel-experiment-009-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("confirmatory_seed_execution_performed") is not False:
        raise ProvenanceError("registration declares prior confirmatory execution")
    expected = manifest.get("source_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ProvenanceError("registration source hashes are missing")
    for relative, frozen_hash in sorted(expected.items()):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ProvenanceError("missing registered source: %s" % relative)
        if sha256_file(path) != frozen_hash:
            raise ProvenanceError("registered source hash mismatch: %s" % relative)
    return manifest


def ensemble(seeds, config, condition, amplitude=None):
    return [core.simulate(seed, config, condition, amplitude) for seed in seeds]


def ensemble_summary(lineages):
    return {
        "count": len(lineages),
        "alive_count": sum(item["alive"] for item in lineages),
        "alive_fraction": float(np.mean([item["alive"] for item in lineages])),
        "death_count": sum(item["death_time"] is not None for item in lineages),
        "median_divisions": float(np.median([item["divisions"] for item in lineages])),
        "median_recovery_ratio": np.median(
            [item["recovery_ratio"] for item in lineages], axis=0
        ).tolist(),
    }


def scaled_lineages(lineages, scales):
    copied = []
    for lineage in lineages:
        item = dict(lineage)
        item["modules"] = lineage["modules"] * np.asarray(scales)
        copied.append(item)
    return copied


def evaluate(minimal_cell_root: Path, train_seeds=TRAIN_SEEDS, test_seeds=TEST_SEEDS):
    anchors = core.verify_and_read_anchors(minimal_cell_root)
    config = core.DynamicsConfig()

    train = {
        condition: ensemble(train_seeds, config, condition)
        for condition in ("native", "joint_erased", "time_shifted")
    }
    heldout = {
        condition: ensemble(test_seeds, config, condition) for condition in CONDITIONS
    }
    heldout["native_severe"] = ensemble(
        test_seeds, config, "native", config.severe_damage_amplitude
    )
    heldout["native_undamaged"] = ensemble(test_seeds, config, "native", 0.0)

    mode = core.fit_cross_mode(train["native"], config)
    native_scores = core.predictor_scores(train["native"], heldout["native"], config)
    erased_scores = core.predictor_scores(
        train["joint_erased"], heldout["joint_erased"], config
    )
    shifted_scores = core.predictor_scores(
        train["time_shifted"], heldout["time_shifted"], config
    )
    scales = np.array([7.0, 0.2, 3.0])
    gauge_scores = core.predictor_scores(
        scaled_lineages(train["native"], scales),
        scaled_lineages(heldout["native"], scales),
        config,
    )
    gauge_difference = max(
        abs(left["cross_gain"] - right["cross_gain"])
        for left, right in zip(
            native_scores["component_scores"], gauge_scores["component_scores"]
        )
    )

    summaries = {name: ensemble_summary(items) for name, items in heldout.items()}
    native_gain = native_scores["minimum_cross_gain"]
    control_gain = max(
        erased_scores["minimum_cross_gain"], shifted_scores["minimum_cross_gain"]
    )
    core_source = Path(core.__file__).read_text().lower()
    optimization_tokens = ("linprog", "minimize(", "maximize(", "objective_function")
    gates = {
        "G1_no_o3_state_installed": "o3" not in {name.lower() for name in core.STATE_NAMES},
        "G2_no_optimization_objective": not any(
            token in core_source for token in optimization_tokens
        ),
        "G3_native_moderate_damage_recovery": summaries["native"]["alive_fraction"] >= 0.90,
        "G4_native_reproduction_after_recovery": summaries["native"]["median_divisions"] >= 1.0,
        "G5_joint_erasure_closure_loss": summaries["joint_erased"]["alive_fraction"] <= 0.10,
        "G6_time_shift_closure_loss": summaries["time_shifted"]["alive_fraction"] <= 0.10,
        "G7_relation_reinjection_rescue": summaries["reinjected"]["alive_fraction"] >= 0.90,
        "G8_severe_damage_death_transition": summaries["native_severe"]["alive_fraction"] <= 0.10,
        "G9_mode_has_all_module_loadings": float(np.min(mode["mode"])) >= 0.25,
        "G10_mode_is_distributed": mode["participation_ratio"] >= 1.50,
        "G11_mode_reenters_every_component": native_scores["minimum_cross_gain"] >= 0.10,
        "G12_cross_gain_exceeds_relation_controls": native_gain >= 2.0 * control_gain,
        "G13_gauge_rescaling_invariant": gauge_difference <= 1e-10,
        "G14_nonliving_control_fails_life_closure": (
            summaries["nonliving"]["alive_fraction"] <= 0.10
            and summaries["nonliving"]["median_divisions"] == 0.0
        ),
    }
    decision = (
        "REDUCED_MODEL_DYNAMIC_O3_SELF_REENTRY_CLOSURE_SUPPORTED"
        if all(gates.values())
        else "REDUCED_MODEL_DYNAMIC_O3_SELF_REENTRY_CLOSURE_NOT_SUPPORTED"
    )
    summary = {
        "experiment": "009_constitutive_cell_o3_closure",
        "decision": decision,
        "source": {
            "repository": "https://github.com/Luthey-Schulten-Lab/Minimal_Cell",
            "commit": core.SOURCE_COMMIT,
            "files_sha256": core.SOURCE_FILES,
            "anchors": anchors,
        },
        "model": {
            "state_names": core.STATE_NAMES,
            "o3_state_installed": False,
            "optimization_objective_used": False,
            "description": (
                "JCVI-syn3A-anchored reduced stochastic dynamics of boundary, nutrient, "
                "ATP, expression, repair, damage, and biomass."
            ),
        },
        "parameters": {
            **config.__dict__,
            "train_seeds": list(train_seeds),
            "heldout_test_seeds": list(test_seeds),
            "cross_lag_minutes": 1.0,
            "gauge_scales": scales.tolist(),
        },
        "results": {
            "conditions": summaries,
            "emergent_cross_mode": {
                "loadings_boundary_metabolism_information_repair": mode["mode"].tolist(),
                "cross_eigenvalue": mode["eigenvalue"],
                "participation_ratio": mode["participation_ratio"],
                "cross_matrix": mode["cross_matrix"].tolist(),
            },
            "native_self_reentry_prediction": native_scores,
            "joint_erased_prediction_control": erased_scores,
            "time_shifted_prediction_control": shifted_scores,
            "gauge_rescaled_prediction": gauge_scores,
            "maximum_gauge_cross_gain_difference": gauge_difference,
        },
        "confirmatory_gates": gates,
        "scope": {
            "constitutive_claim": (
                "A cell is constituted as one living whole when differentiated "
                "boundary, metabolic, and information-repair perspectives generate "
                "a distributed third perspective whose self-reentry remakes the "
                "conditions of their continued intersection."
            ),
            "supported_if_positive": (
                "Operational realization of the constitutive claim through natural "
                "emergence of a distributed cross-module mode, lagged re-entry into "
                "every component, and damage-recovery/death closure in the frozen "
                "reduced JCVI-syn3A-anchored model."
            ),
            "not_established": [
                "the same O3 in a full CME-ODE whole-cell execution",
                "empirical O3 in living JCVI-syn3A cells",
                "the ontology by this computation alone",
            ],
        },
    }
    return summary, heldout


def write_results(output: Path, summary: dict, heldout: dict):
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    with (output / "lineages.csv").open("w", newline="") as handle:
        fieldnames = [
            "condition", "seed", "damage_amplitude", "alive", "death_time",
            "divisions", "boundary_recovery", "metabolic_recovery",
            "information_repair_recovery",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for condition, lineages in heldout.items():
            for item in lineages:
                writer.writerow(
                    {
                        "condition": condition,
                        "seed": item["seed"],
                        "damage_amplitude": item["damage_amplitude"],
                        "alive": item["alive"],
                        "death_time": item["death_time"],
                        "divisions": item["divisions"],
                        "boundary_recovery": item["recovery_ratio"][0],
                        "metabolic_recovery": item["recovery_ratio"][1],
                        "information_repair_recovery": item["recovery_ratio"][2],
                    }
                )


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--minimal-cell-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    verify_registration()
    anchors = core.verify_and_read_anchors(args.minimal_cell_root)
    if args.validate_registration:
        print("E009_REGISTRATION_AND_SOURCE_LOCK_VALID")
        print(json.dumps(anchors, indent=2, sort_keys=True))
        return
    summary, heldout = evaluate(args.minimal_cell_root)
    write_results(args.output, summary, heldout)
    print(summary["decision"])
    print(json.dumps(summary["confirmatory_gates"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
