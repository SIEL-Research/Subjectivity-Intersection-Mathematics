#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Seed-robust reciprocal-recall pilot for the frozen carrier pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


from support import p014_architectures as P014
E012 = P014.E012
E010 = P014.E010
E009 = P014.E009

ARCHITECTURES = P014.ARCHITECTURES
INTERACTING_ARCHITECTURES = P014.INTERACTING_ARCHITECTURES
NEW_ARCHITECTURE = P014.NEW_ARCHITECTURE
OPERATORS = P014.OPERATORS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=3500)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.004)
    parser.add_argument("--training-seeds", type=int, default=5)
    parser.add_argument("--test-episodes", type=int, default=8192)
    parser.add_argument("--random-draws", type=int, default=8)
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args()


def make_inputs(
    private_a: np.ndarray,
    private_b: np.ndarray,
    pair: np.ndarray,
    profiles: dict[str, np.ndarray],
    rng: np.random.Generator | None,
) -> np.ndarray:
    time = np.arange(E009.SEQUENCE_LENGTH, dtype=np.float64)
    centre_a = 0.35 + private_a.astype(np.float64)
    centre_b = 0.35 + private_b.astype(np.float64)
    pulse_a = np.exp(-0.5 * ((time[None, :] - centre_a[:, None]) / 0.22) ** 2)
    pulse_b = np.exp(-0.5 * ((time[None, :] - centre_b[:, None]) / 0.22) ** 2)
    if rng is None:
        noise_a = noise_b = 0.0
    else:
        noise_a = 0.02 * rng.normal(size=pulse_a.shape)
        noise_b = 0.02 * rng.normal(size=pulse_b.shape)
    observed_a = profiles["gain_a"][pair, None] * pulse_a + profiles["bias_a"][pair, None] + noise_a
    observed_b = profiles["gain_b"][pair, None] * pulse_b + profiles["bias_b"][pair, None] + noise_b
    x = np.empty((private_a.shape[0], E009.SEQUENCE_LENGTH, E009.INPUT_DIM))
    normalized_time = time[None, :] / (E009.SEQUENCE_LENGTH - 1)
    x[:, :, 0] = observed_a
    x[:, :, 1] = normalized_time
    x[:, :, 2] = normalized_time * normalized_time
    x[:, :, 3] = 1.0
    x[:, :, 4] = observed_b
    x[:, :, 5] = normalized_time
    x[:, :, 6] = normalized_time * normalized_time
    x[:, :, 7] = 1.0
    return x


def sample_batch(
    seed: int,
    pairs: tuple[int, ...],
    count: int,
    profiles: dict[str, np.ndarray],
    noise: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    pair = rng.choice(np.asarray(pairs), size=count, replace=True)
    private_a = rng.integers(0, 3, size=count)
    private_b = rng.integers(0, 3, size=count)
    x = make_inputs(private_a, private_b, pair, profiles, rng if noise else None)
    # Receiver A reports B; receiver B reports A.
    y = np.stack((private_b, private_a), axis=1)
    return x, y, pair


def loss_and_grad(
    model: dict[str, Any], x: np.ndarray, y: np.ndarray
) -> tuple[float, dict[str, np.ndarray]]:
    logits, states = E009.forward(model, x)
    probabilities = E009.softmax(logits)
    targets = np.zeros_like(probabilities)
    rows = np.arange(y.shape[0])
    targets[rows, 0, y[:, 0]] = 1.0
    targets[rows, 1, y[:, 1]] = 1.0
    selected = probabilities[rows[:, None], np.arange(2)[None, :], y]
    loss = -float(np.mean(np.log(np.maximum(selected, 1e-12))))
    dlogits = (probabilities - targets) / (2.0 * y.shape[0])
    flat_dlogits = dlogits.reshape(-1, E009.OUTPUT_DIM)
    p = model["params"]
    grads = {key: np.zeros_like(value) for key, value in p.items()}
    grads["outputs"] = flat_dlogits.T @ states[-1]
    grads["output_bias"] = flat_dlogits.sum(axis=0)
    dh = flat_dlogits @ p["outputs"]
    for position in range(x.shape[1] - 1, -1, -1):
        current = states[position + 1]
        previous = states[position]
        dz = dh * (1.0 - current * current)
        grads["inputs"] += dz.T @ x[:, position]
        grads["recurrent"] += dz.T @ previous
        grads["bias"] += dz.sum(axis=0)
        dh = dz @ p["recurrent"]
    grads["inputs"] *= model["masks"]["inputs"]
    grads["recurrent"] *= model["masks"]["recurrent"]
    grads["outputs"] *= model["masks"]["outputs"]
    return loss, grads


def cross_entropy(logits: np.ndarray, y: np.ndarray) -> float:
    probabilities = E009.softmax(logits)
    rows = np.arange(y.shape[0])
    selected = probabilities[rows[:, None], np.arange(2)[None, :], y]
    return -float(np.mean(np.log(np.maximum(selected, 1e-12))))


def both_correct(logits: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.all(np.argmax(logits, axis=2) == y, axis=1)))


def evaluate(model: dict[str, Any], x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    logits, _ = E009.forward(model, x)
    prediction = np.argmax(logits, axis=2)
    return {
        "cross_entropy": cross_entropy(logits, y),
        "agent_accuracy": float(np.mean(prediction == y)),
        "both_correct": float(np.mean(np.all(prediction == y, axis=1))),
    }


def train_model(
    architecture: str,
    training_seed: int,
    steps: int,
    batch_size: int,
    learning_rate: float,
    profiles: dict[str, np.ndarray],
) -> dict[str, Any]:
    model = P014.initialize(architecture, 1510000 + training_seed)
    square_average = {key: np.zeros_like(value) for key, value in model["params"].items()}
    decay = 0.99
    for step in range(1, steps + 1):
        x, y, _ = sample_batch(
            1520000 + 100000 * training_seed + step,
            E009.TRAIN_PAIRS,
            batch_size,
            profiles,
            noise=True,
        )
        _, grads = loss_and_grad(model, x, y)
        total_norm = math.sqrt(
            sum(float(np.sum(gradient * gradient)) for gradient in grads.values())
        )
        gradient_scale = min(1.0, 5.0 / (total_norm + 1e-12))
        for key, gradient in grads.items():
            gradient = gradient * gradient_scale
            square_average[key] = (
                decay * square_average[key] + (1.0 - decay) * gradient * gradient
            )
            model["params"][key] -= learning_rate * gradient / (
                np.sqrt(square_average[key]) + 1e-8
            )
        model["params"]["inputs"] *= model["masks"]["inputs"]
        model["params"]["recurrent"] *= model["masks"]["recurrent"]
        model["params"]["outputs"] *= model["masks"]["outputs"]
    return model


def evaluation_episodes(
    seed: int, count: int, profiles: dict[str, np.ndarray]
) -> dict[str, np.ndarray]:
    x, y, pair = sample_batch(seed, E009.HELDOUT_PAIRS, count, profiles, noise=False)
    x[:, E009.INTERVENTION_STEP - 1 :, 0] = profiles["bias_a"][pair, None]
    x[:, E009.INTERVENTION_STEP - 1 :, 4] = profiles["bias_b"][pair, None]
    return {"x": x, "y": y, "pair": pair}


def audit(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    profiles: dict[str, np.ndarray],
    random_seed: int,
    random_draws: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray], list[dict[str, np.ndarray]]]:
    variants = P014.baseline_variants(episodes, profiles)
    states = {name: P014.prefix_state(model, value) for name, value in variants.items()}
    reversed_states = {
        name: P014.prefix_state(model, value, reverse_order=True)
        for name, value in variants.items()
    }
    component = P014.directed_component(architecture, states)
    reverse_component = P014.directed_component(architecture, reversed_states)
    donor = E010.cross_pair_donor(episodes["pair"])
    normal_logits = E010.continue_from(model, states["ab"].copy(), episodes["x"])
    normal_loss = cross_entropy(normal_logits, episodes["y"])
    relation_logits, relation_responses = P014.response_for_components(
        model,
        episodes,
        normal_logits,
        states["ab"],
        component,
        donor,
        reverse_component,
    )
    rng = np.random.default_rng(random_seed)
    norm = np.linalg.norm(component, axis=1, keepdims=True)
    random_responses = []
    random_delete_loss_increases = []
    for _ in range(random_draws):
        direction = rng.normal(size=component.shape)
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)
        random_component = direction * norm
        reverse_direction = rng.normal(size=component.shape)
        reverse_direction /= np.maximum(
            np.linalg.norm(reverse_direction, axis=1, keepdims=True), 1e-12
        )
        random_reverse = reverse_direction * norm
        random_logits, fields = P014.response_for_components(
            model,
            episodes,
            normal_logits,
            states["ab"],
            random_component,
            donor,
            random_reverse,
        )
        random_responses.append(fields)
        random_delete_loss_increases.append(
            cross_entropy(random_logits["delete"], episodes["y"]) - normal_loss
        )
    delete_loss_increase = cross_entropy(
        relation_logits["delete"], episodes["y"]
    ) - normal_loss
    bilateral = {
        operator: float(np.mean(np.all(
            np.sum(np.abs(response), axis=2) > 1e-9, axis=1
        )))
        for operator, response in relation_responses.items()
    }
    metrics = {
        "component_norm": float(np.mean(
            np.linalg.norm(component, axis=1) / math.sqrt(component.shape[1])
        )),
        "normal_cross_entropy": normal_loss,
        "normal_both_correct": both_correct(normal_logits, episodes["y"]),
        "delete_cross_entropy_increase": delete_loss_increase,
        "random_delete_cross_entropy_increase_median": float(
            np.median(random_delete_loss_increases)
        ),
        "delete_selectivity": delete_loss_increase
        - float(np.median(random_delete_loss_increases)),
        "bilateral_response_minimum": min(bilateral.values()),
    }
    return metrics, relation_responses, random_responses


def summarize(values: list[float]) -> dict[str, float]:
    return E012.summarize(values)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


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
        args.test_episodes = min(args.test_episodes, 256)
        args.random_draws = min(args.random_draws, 2)

    counts = {
        architecture: P014.active_parameter_count(architecture)
        for architecture in ARCHITECTURES
    }
    profiles = E009.pair_profiles()
    episodes = evaluation_episodes(1530001, args.test_episodes, profiles)
    performance_x, performance_y, _ = sample_batch(
        1530002, E009.HELDOUT_PAIRS, args.test_episodes, profiles, noise=True
    )
    metric_rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []

    for training_seed in range(args.training_seeds):
        relation: dict[str, dict[str, np.ndarray]] = {}
        random: dict[str, list[dict[str, np.ndarray]]] = {}
        for architecture_index, architecture in enumerate(ARCHITECTURES):
            model = train_model(
                architecture,
                training_seed,
                args.steps,
                args.batch_size,
                args.learning_rate,
                profiles,
            )
            performance = evaluate(model, performance_x, performance_y)
            metrics, relation[architecture], random[architecture] = audit(
                architecture,
                model,
                episodes,
                profiles,
                1540000 + 100 * training_seed + architecture_index,
                args.random_draws,
            )
            metric_rows.append({
                "training_seed": training_seed,
                "architecture": architecture,
                "heldout_both_correct": performance["both_correct"],
                **metrics,
            })

        for left_index, left_architecture in enumerate(INTERACTING_ARCHITECTURES):
            for right_architecture in INTERACTING_ARCHITECTURES[left_index + 1 :]:
                relation_cka = E012.linear_cka(
                    E012.field_matrix(relation[left_architecture]),
                    E012.field_matrix(relation[right_architecture]),
                )
                random_values = [
                    E012.linear_cka(
                        E012.field_matrix(random[left_architecture][draw]),
                        E012.field_matrix(random[right_architecture][draw]),
                    )
                    for draw in range(args.random_draws)
                ]
                context_rows.append({
                    "training_seed": training_seed,
                    "left_architecture": left_architecture,
                    "right_architecture": right_architecture,
                    "involves_new_architecture": (
                        left_architecture == NEW_ARCHITECTURE
                        or right_architecture == NEW_ARCHITECTURE
                    ),
                    "relation_context_cka": relation_cka,
                    "random_context_cka_median": float(np.median(random_values)),
                    "context_cka_specificity": relation_cka
                    - float(np.median(random_values)),
                })

    args.out_dir.mkdir(parents=True)
    write_csv(args.out_dir / "local_carrier_metrics.csv", metric_rows)
    write_csv(args.out_dir / "context_correspondence.csv", context_rows)

    architecture_summary: dict[str, Any] = {}
    for architecture in ARCHITECTURES:
        chosen = [row for row in metric_rows if row["architecture"] == architecture]
        architecture_summary[architecture] = {
            field: summarize([float(row[field]) for row in chosen])
            for field in (
                "heldout_both_correct",
                "component_norm",
                "delete_cross_entropy_increase",
                "random_delete_cross_entropy_increase_median",
                "delete_selectivity",
                "bilateral_response_minimum",
            )
        }
        architecture_summary[architecture]["positive_selectivity_seed_count"] = sum(
            float(row["delete_selectivity"]) > 0.0 for row in chosen
        )

    new_pair_summary: dict[str, Any] = {}
    for other_architecture in E009.INTERACTING_ARCHITECTURES:
        chosen = [
            row for row in context_rows
            if {row["left_architecture"], row["right_architecture"]}
            == {other_architecture, NEW_ARCHITECTURE}
        ]
        new_pair_summary[other_architecture + "__" + NEW_ARCHITECTURE] = {
            "relation_context_cka": summarize([
                float(row["relation_context_cka"]) for row in chosen
            ]),
            "random_context_cka_median": summarize([
                float(row["random_context_cka_median"]) for row in chosen
            ]),
            "context_cka_specificity": summarize([
                float(row["context_cka_specificity"]) for row in chosen
            ]),
        }

    checks = {
        "capacity_exact_486": set(counts.values()) == {486},
        "interacting_accuracy_minimum_0_95": all(
            architecture_summary[architecture]["heldout_both_correct"]["minimum"] >= 0.95
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "independent_accuracy_maximum_0_20": (
            architecture_summary["independent"]["heldout_both_correct"]["maximum"] <= 0.20
        ),
        "independent_component_zero": (
            architecture_summary["independent"]["component_norm"]["maximum"] < 1e-10
        ),
        "interacting_component_norm_minimum_above_0_01": all(
            architecture_summary[architecture]["component_norm"]["minimum"] > 0.01
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "delete_loss_increase_median_at_least_0_50": all(
            architecture_summary[architecture]["delete_cross_entropy_increase"]["median"] >= 0.50
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "delete_selectivity_median_at_least_0_20": all(
            architecture_summary[architecture]["delete_selectivity"]["median"] >= 0.20
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "positive_selectivity_all_five_seeds": all(
            architecture_summary[architecture]["positive_selectivity_seed_count"] == 5
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "bilateral_response_minimum_0_95": all(
            architecture_summary[architecture]["bilateral_response_minimum"]["minimum"] >= 0.95
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "new_architecture_context_cka_median_at_least_0_35": all(
            item["relation_context_cka"]["median"] >= 0.35
            for item in new_pair_summary.values()
        ),
        "new_architecture_context_specificity_median_at_least_0_15": all(
            item["context_cka_specificity"]["median"] >= 0.15
            for item in new_pair_summary.values()
        ),
    }
    readout = "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    summary = {
        "schema": "sio-local-p015-seed-robust-reciprocal-recall-v1",
        "status": "LOCAL_PILOT_COMPLETE",
        "pilot_readout": readout,
        "quick": bool(args.quick),
        "task": "delayed reciprocal recall",
        "targets": {"receiver_A": "private_B", "receiver_B": "private_A"},
        "capacity": counts,
        "training": {
            "steps": args.steps,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "training_seeds": args.training_seeds,
        },
        "evaluation": {
            "test_episodes": args.test_episodes,
            "random_draws": args.random_draws,
            "heldout_pairs": "E009 odd HELDOUT_PAIRS",
        },
        "local_carrier": architecture_summary,
        "new_architecture_correspondence": new_pair_summary,
        "acceptance_checks": checks,
        "experiment_005_firewall": (
            "This pilot task, architecture, seeds, thresholds, and outputs are excluded "
            "from Public Experiment 005 confirmatory data."
        ),
        "claim_boundary": (
            "A supported result establishes seed-robust pipeline feasibility for delayed "
            "reciprocal recall. It is not Public Experiment 005 confirmation."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "sio-local-p015-output-manifest-v1",
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
        "pilot_readout": readout,
        "quick": summary["quick"],
        "acceptance_checks": checks,
        "local_carrier": architecture_summary,
        "new_architecture_correspondence": new_pair_summary,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
