#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Directed cross-influence carrier audit in the E009 event-order world."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


from support import e009_world as E009

ARCHITECTURES = E009.ARCHITECTURES
INTERACTING_ARCHITECTURES = E009.INTERACTING_ARCHITECTURES
OPERATORS = E009.OPERATORS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=3500)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.004)
    parser.add_argument("--training-seeds", type=int, default=5)
    parser.add_argument("--test-quartets", type=int, default=4096)
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args()


def receiver_indices(architecture: str) -> tuple[np.ndarray, np.ndarray]:
    if architecture in ("independent", "distributed"):
        a = np.arange(0, 12)
        b = np.arange(12, 24)
    elif architecture == "central_shared":
        a = np.concatenate((np.arange(0, 6), np.arange(12, 18)))
        b = np.concatenate((np.arange(6, 12), np.arange(18, 24)))
    elif architecture == "directional_relay":
        a = np.concatenate((np.arange(0, 9), np.arange(21, 24)))
        b = np.concatenate((np.arange(9, 18), np.arange(18, 21)))
    else:
        raise ValueError(architecture)
    assert len(set(a) & set(b)) == 0
    assert sorted(np.concatenate((a, b)).tolist()) == list(range(E009.STATE_DIM))
    return a, b


def flatten_quartet_batch(quartets: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    count = quartets["x"].shape[0]
    return {
        "x": quartets["x"].reshape(count * 4, E009.SEQUENCE_LENGTH, E009.INPUT_DIM),
        "y": quartets["y"].reshape(count * 4),
        "pair": np.repeat(quartets["pair"], 4),
    }


def baseline_variants(
    x: np.ndarray,
    pair: np.ndarray,
    profiles: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    ab = x.copy()
    a0 = x.copy()
    zero_b = profiles["bias_b"][pair, None]
    a0[:, :, 4] = zero_b
    zero_both = a0.copy()
    zero_a = profiles["bias_a"][pair, None]
    zero_both[:, :, 0] = zero_a
    zero_b = x.copy()
    zero_b[:, :, 0] = zero_a
    return {"ab": ab, "a0": a0, "0b": zero_b, "00": zero_both}


def prefix_state(
    model: dict[str, Any],
    x: np.ndarray,
    reverse_order: bool = False,
) -> np.ndarray:
    prefix = x[:, : E009.INTERVENTION_STEP].copy()
    if reverse_order:
        prefix[:, : E009.INTERVENTION_STEP - 1] = (
            prefix[:, : E009.INTERVENTION_STEP - 1][:, ::-1]
        )
    _, states = E009.forward(model, prefix)
    return states[-1]


def directed_cross_component(
    architecture: str,
    states: dict[str, np.ndarray],
) -> np.ndarray:
    """Receiver-indexed incoming influence from the opposite side.

    On A-receiver coordinates, retain the effect of restoring B while A is
    fixed. On B-receiver coordinates, retain the effect of restoring A while B
    is fixed. The component is exactly zero for the independent architecture.
    """
    a_indices, b_indices = receiver_indices(architecture)
    component = np.zeros_like(states["ab"])
    component[:, a_indices] = (
        states["ab"][:, a_indices] - states["a0"][:, a_indices]
    )
    component[:, b_indices] = (
        states["ab"][:, b_indices] - states["0b"][:, b_indices]
    )
    return component


def continue_from(
    model: dict[str, Any],
    hidden: np.ndarray,
    x: np.ndarray,
) -> np.ndarray:
    p = model["params"]
    suffix = x[:, E009.INTERVENTION_STEP :]
    for position in range(suffix.shape[1]):
        hidden = np.tanh(
            suffix[:, position] @ p["inputs"].T
            + hidden @ p["recurrent"].T
            + p["bias"]
        )
    logits = hidden @ p["outputs"].T + p["output_bias"]
    return logits.reshape(-1, 2, E009.CLASS_COUNT)


def cross_pair_donor(pair: np.ndarray) -> np.ndarray:
    donor = np.arange(pair.shape[0])
    unresolved = np.ones(pair.shape[0], dtype=bool)
    base = np.arange(pair.shape[0])
    for offset in range(1, pair.shape[0]):
        candidate = np.roll(base, offset)
        use = unresolved & (pair[candidate] != pair)
        donor[use] = candidate[use]
        unresolved[use] = False
        if not unresolved.any():
            break
    if unresolved.any():
        raise AssertionError("cross-pair donor construction failed")
    return donor


def both_correct(logits: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.all(np.argmax(logits, axis=2) == y[:, None], axis=1)))


def probability_response(logits: np.ndarray, normal: np.ndarray) -> np.ndarray:
    return E009.softmax(logits) - E009.softmax(normal)


def operator_audit(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    profiles: dict[str, np.ndarray],
    random_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray], dict[str, np.ndarray], float]:
    x, y, pair = episodes["x"], episodes["y"], episodes["pair"]
    variants = baseline_variants(x, pair, profiles)
    states = {
        name: prefix_state(model, value)
        for name, value in variants.items()
    }
    reversed_states = {
        name: prefix_state(model, value, reverse_order=True)
        for name, value in variants.items()
    }
    component = directed_cross_component(architecture, states)
    reversed_component = directed_cross_component(architecture, reversed_states)
    donor = cross_pair_donor(pair)
    normal_logits = continue_from(model, states["ab"].copy(), x)
    normal_loss = E009.cross_entropy(normal_logits, y)
    normal_accuracy = both_correct(normal_logits, y)

    intervened = {
        "delete": states["ab"] - component,
        "exchange": states["ab"] - component + component[donor],
        "sign_flip": states["ab"] - 2.0 * component,
        "compose": states["ab"] + component[donor],
        "temporal_reverse": states["ab"] - component + reversed_component,
    }
    rows = []
    responses = {}
    for operator in OPERATORS:
        logits = continue_from(model, intervened[operator].copy(), x)
        response = probability_response(logits, normal_logits)
        responses[operator] = response
        rows.append({
            "operator": operator,
            "normal_cross_entropy": normal_loss,
            "intervened_cross_entropy": E009.cross_entropy(logits, y),
            "cross_entropy_increase": E009.cross_entropy(logits, y) - normal_loss,
            "normal_both_correct": normal_accuracy,
            "intervened_both_correct": both_correct(logits, y),
            "accuracy_drop": normal_accuracy - both_correct(logits, y),
            "mean_absolute_probability_response": float(np.mean(np.abs(response))),
            "bilateral_response_fraction": float(
                np.mean(np.all(np.sum(np.abs(response), axis=2) > 1e-9, axis=1))
            ),
        })

    rng = np.random.default_rng(random_seed)
    norm = np.linalg.norm(component, axis=1, keepdims=True)
    random_direction = rng.normal(size=component.shape)
    random_direction /= np.maximum(
        np.linalg.norm(random_direction, axis=1, keepdims=True), 1e-12
    )
    random_component = random_direction * norm
    random_reverse_direction = rng.normal(size=component.shape)
    random_reverse_direction /= np.maximum(
        np.linalg.norm(random_reverse_direction, axis=1, keepdims=True), 1e-12
    )
    random_reverse = random_reverse_direction * norm
    random_intervened = {
        "delete": states["ab"] - random_component,
        "exchange": states["ab"] - random_component + random_component[donor],
        "sign_flip": states["ab"] - 2.0 * random_component,
        "compose": states["ab"] + random_component[donor],
        "temporal_reverse": states["ab"] - random_component + random_reverse,
    }
    random_responses = {
        operator: probability_response(
            continue_from(model, random_intervened[operator].copy(), x), normal_logits
        )
        for operator in OPERATORS
    }

    random_losses = []
    random_accuracies = []
    for _ in range(16):
        direction = rng.normal(size=component.shape)
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)
        random_delete = direction * norm
        logits = continue_from(model, (states["ab"] - random_delete).copy(), x)
        random_losses.append(E009.cross_entropy(logits, y) - normal_loss)
        random_accuracies.append(normal_accuracy - both_correct(logits, y))
    random_loss = float(np.median(random_losses))
    random_accuracy = float(np.median(random_accuracies))
    for row in rows:
        row["random_delete_cross_entropy_increase"] = random_loss
        row["random_delete_accuracy_drop"] = random_accuracy
        if row["operator"] == "delete":
            row["delete_vs_random_loss_selectivity"] = row["cross_entropy_increase"] - random_loss
            row["delete_vs_random_accuracy_selectivity"] = row["accuracy_drop"] - random_accuracy
        else:
            row["delete_vs_random_loss_selectivity"] = ""
            row["delete_vs_random_accuracy_selectivity"] = ""
    component_norm = float(
        np.mean(np.linalg.norm(component, axis=1) / math.sqrt(component.shape[1]))
    )
    return rows, responses, random_responses, component_norm


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "minimum": float(min(values)),
        "median": float(np.median(values)),
        "maximum": float(max(values)),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    if args.out_dir.exists():
        raise SystemExit("FAIL: output directory exists")
    if args.quick:
        args.steps = min(args.steps, 50)
        args.batch_size = min(args.batch_size, 32)
        args.training_seeds = min(args.training_seeds, 1)
        args.test_quartets = min(args.test_quartets, 128)

    counts = {
        architecture: E009.active_parameter_count(E009.architecture_masks(architecture))
        for architecture in ARCHITECTURES
    }
    profiles = E009.pair_profiles()
    episodes = flatten_quartet_batch(
        E009.build_temporal_quartets(1010001, args.test_quartets, profiles)
    )
    intervention_rows = []
    correlation_rows = []

    for training_seed in range(args.training_seeds):
        relation_responses = {}
        random_responses = {}
        for architecture in ARCHITECTURES:
            model = E009.train_model(
                architecture,
                training_seed,
                args.steps,
                args.batch_size,
                args.learning_rate,
                profiles,
            )
            rows, responses, null_responses, component_norm = operator_audit(
                architecture,
                model,
                episodes,
                profiles,
                1020000 + 100 * training_seed + ARCHITECTURES.index(architecture),
            )
            relation_responses[architecture] = responses
            random_responses[architecture] = null_responses
            for row in rows:
                intervention_rows.append({
                    "training_seed": training_seed,
                    "architecture": architecture,
                    "component_norm": component_norm,
                    **row,
                })

        architecture_pairs = (
            ("central_shared", "distributed"),
            ("central_shared", "directional_relay"),
            ("distributed", "directional_relay"),
        )
        for pair_index, (left_architecture, right_architecture) in enumerate(architecture_pairs):
            for component_index, (component_type, source) in enumerate((
                ("directed_cross", relation_responses),
                ("random_equal_norm", random_responses),
            )):
                for operator_index, operator in enumerate(OPERATORS):
                    for agent in range(2):
                        left = source[left_architecture][operator][:, agent, :].reshape(-1)
                        right = source[right_architecture][operator][:, agent, :].reshape(-1)
                        result = E009.permutation_correlation(
                            left,
                            right,
                            1030000
                            + 100000 * component_index
                            + 10000 * training_seed
                            + 1000 * pair_index
                            + 100 * operator_index
                            + agent,
                        )
                        correlation_rows.append({
                            "training_seed": training_seed,
                            "left_architecture": left_architecture,
                            "right_architecture": right_architecture,
                            "component_type": component_type,
                            "operator": operator,
                            "agent": "A" if agent == 0 else "B",
                            **result,
                        })

    args.out_dir.mkdir(parents=True)
    write_csv(args.out_dir / "intervention_metrics.csv", intervention_rows)
    write_csv(args.out_dir / "response_correlations.csv", correlation_rows)

    intervention_summary = {}
    for architecture in ARCHITECTURES:
        intervention_summary[architecture] = {}
        for operator in OPERATORS:
            chosen = [
                row for row in intervention_rows
                if row["architecture"] == architecture and row["operator"] == operator
            ]
            intervention_summary[architecture][operator] = {
                field: summarize([float(row[field]) for row in chosen])
                for field in (
                    "cross_entropy_increase",
                    "accuracy_drop",
                    "mean_absolute_probability_response",
                    "bilateral_response_fraction",
                )
            }
        delete_rows = [
            row for row in intervention_rows
            if row["architecture"] == architecture and row["operator"] == "delete"
        ]
        intervention_summary[architecture]["delete_selectivity"] = {
            field: summarize([float(row[field]) for row in delete_rows])
            for field in (
                "random_delete_cross_entropy_increase",
                "random_delete_accuracy_drop",
                "delete_vs_random_loss_selectivity",
                "delete_vs_random_accuracy_selectivity",
            )
        }
        intervention_summary[architecture]["component_norm"] = summarize(
            [float(row["component_norm"]) for row in delete_rows]
        )

    correlation_summary = {}
    for left_architecture, right_architecture in (
        ("central_shared", "distributed"),
        ("central_shared", "directional_relay"),
        ("distributed", "directional_relay"),
    ):
        key = left_architecture + "__" + right_architecture
        correlation_summary[key] = {}
        medians = {}
        for component_type in ("directed_cross", "random_equal_norm"):
            chosen = [
                row for row in correlation_rows
                if row["left_architecture"] == left_architecture
                and row["right_architecture"] == right_architecture
                and row["component_type"] == component_type
            ]
            values = [float(row["correlation"]) for row in chosen]
            medians[component_type] = float(np.median(values))
            correlation_summary[key][component_type] = {
                "response_correlation": summarize(values),
                "permutation_p_maximum": float(max(row["permutation_p"] for row in chosen)),
            }
        correlation_summary[key]["median_specificity"] = (
            medians["directed_cross"] - medians["random_equal_norm"]
        )

    checks = {
        "capacity_exact": set(counts.values()) == {486},
        "independent_component_zero": (
            intervention_summary["independent"]["component_norm"]["maximum"] < 1e-10
        ),
        "delete_selectivity_positive_all_seeds": all(
            intervention_summary[architecture]["delete_selectivity"]
            ["delete_vs_random_loss_selectivity"]["minimum"] > 0.0
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "bilateral_response_at_least_0_95": all(
            intervention_summary[architecture][operator]
            ["bilateral_response_fraction"]["minimum"] >= 0.95
            for architecture in INTERACTING_ARCHITECTURES
            for operator in OPERATORS
        ),
        "directed_response_correlation_minimum_above_0_20": all(
            correlation_summary[key]["directed_cross"]["response_correlation"]["minimum"] > 0.20
            for key in correlation_summary
        ),
        "directed_permutation_p_maximum_0_005": all(
            correlation_summary[key]["directed_cross"]["permutation_p_maximum"] <= 0.005
            for key in correlation_summary
        ),
        "random_response_median_absolute_below_0_10": all(
            abs(correlation_summary[key]["random_equal_norm"]["response_correlation"]["median"]) < 0.10
            for key in correlation_summary
        ),
        "median_specificity_above_0_20": all(
            correlation_summary[key]["median_specificity"] > 0.20
            for key in correlation_summary
        ),
    }
    readout = "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    summary = {
        "schema": "sio-local-e010-directed-cross-influence-v1",
        "status": "LOCAL_EXPLORATORY_COMPLETE",
        "directed_cross_readout": readout,
        "quick": bool(args.quick),
        "extractor": {
            "A_receiver": "state(AB)-state(A0) on A-receiver coordinates",
            "B_receiver": "state(AB)-state(0B) on B-receiver coordinates",
            "labels_used": False,
            "world": "identical to E009",
        },
        "capacity": {"active_parameter_counts": counts},
        "training": {
            "steps": args.steps,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "training_seeds": args.training_seeds,
        },
        "interventions": intervention_summary,
        "cross_architecture_response": correlation_summary,
        "acceptance_checks": checks,
        "claim_boundary": (
            "Post-E009 local follow-up. The world and models are held fixed while the extractor changes. "
            "The extractor uses architecture-declared receiver partitions and is therefore operationally "
            "portable but not topology-blind."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "sio-local-e010-output-manifest-v1",
        "files_sha256": {
            path.name: sha256_file(path)
            for path in sorted(args.out_dir.iterdir())
            if path.name != "output_manifest.json"
        },
    }
    (args.out_dir / "output_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": summary["status"],
        "directed_cross_readout": readout,
        "quick": summary["quick"],
        "cross_architecture_response": correlation_summary,
        "acceptance_checks": checks,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
