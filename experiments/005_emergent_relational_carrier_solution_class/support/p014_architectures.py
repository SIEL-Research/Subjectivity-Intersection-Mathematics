#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Transfer pilot for the frozen local relation-carrier pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


from support import analysis_utils as E012
from support import e009_world as E009
from support import e010_directed as E010

NEW_ARCHITECTURE = "four_channel_crossbar"
ARCHITECTURES = (*E009.ARCHITECTURES, NEW_ARCHITECTURE)
INTERACTING_ARCHITECTURES = ARCHITECTURES[1:]
OPERATORS = E009.OPERATORS


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


def architecture_masks(name: str) -> dict[str, np.ndarray]:
    if name != NEW_ARCHITECTURE:
        return E009.architecture_masks(name)
    recurrent = np.zeros((E009.STATE_DIM, E009.STATE_DIM))
    inputs = np.zeros((E009.STATE_DIM, E009.INPUT_DIM))
    outputs = np.zeros((E009.OUTPUT_DIM, E009.STATE_DIM))

    # A local 0..7, B local 8..15, A-to-B 16..19, B-to-A 20..23.
    recurrent[0:8, 0:8] = 1.0
    recurrent[0:8, 20:24] = 1.0
    recurrent[8:16, 8:16] = 1.0
    recurrent[8:16, 16:20] = 1.0
    recurrent[16:20, 0:8] = 1.0
    recurrent[16:20, 16:20] = 1.0
    recurrent[20:24, 8:16] = 1.0
    recurrent[20:24, 20:24] = 1.0

    inputs[0:8, :4] = 1.0
    inputs[8:16, 4:] = 1.0
    inputs[16:20, :4] = 1.0
    inputs[20:24, 4:] = 1.0

    outputs[:3, 0:8] = 1.0
    outputs[:3, 20:24] = 1.0
    outputs[3:, 8:16] = 1.0
    outputs[3:, 16:20] = 1.0

    assert int(recurrent.sum()) == 288
    assert int(inputs.sum()) == 96
    assert int(outputs.sum()) == 72
    return {"recurrent": recurrent, "inputs": inputs, "outputs": outputs}


def active_parameter_count(name: str) -> int:
    return E009.active_parameter_count(architecture_masks(name))


def receiver_indices(architecture: str) -> tuple[np.ndarray, np.ndarray]:
    if architecture == NEW_ARCHITECTURE:
        a = np.concatenate((np.arange(0, 8), np.arange(20, 24)))
        b = np.concatenate((np.arange(8, 16), np.arange(16, 20)))
        return a, b
    return E010.receiver_indices(architecture)


def initialize(architecture: str, seed: int) -> dict[str, Any]:
    masks = architecture_masks(architecture)
    rng = np.random.default_rng(seed)
    params = {
        "recurrent": rng.normal(scale=0.18, size=(E009.STATE_DIM, E009.STATE_DIM))
        * masks["recurrent"],
        "inputs": rng.normal(scale=0.24, size=(E009.STATE_DIM, E009.INPUT_DIM))
        * masks["inputs"],
        "bias": np.zeros(E009.STATE_DIM),
        "outputs": rng.normal(scale=0.16, size=(E009.OUTPUT_DIM, E009.STATE_DIM))
        * masks["outputs"],
        "output_bias": np.zeros(E009.OUTPUT_DIM),
    }
    return {"name": architecture, "masks": masks, "params": params}


def checksum_target(private_a: np.ndarray, private_b: np.ndarray, rule: np.ndarray) -> np.ndarray:
    return (private_a + private_b + rule) % E009.CLASS_COUNT


def make_inputs(
    private_a: np.ndarray,
    private_b: np.ndarray,
    rule: np.ndarray,
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
    x[:, :, 0] = observed_a
    x[:, :, 1] = time[None, :] / (E009.SEQUENCE_LENGTH - 1)
    x[:, :, 2] = rule[:, None] / 2.0
    x[:, :, 3] = 1.0
    x[:, :, 4] = observed_b
    x[:, :, 5] = time[None, :] / (E009.SEQUENCE_LENGTH - 1)
    x[:, :, 6] = rule[:, None] / 2.0
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
    rule = rng.integers(0, 3, size=count)
    y = checksum_target(private_a, private_b, rule)
    x = make_inputs(private_a, private_b, rule, pair, profiles, rng if noise else None)
    return x, y, pair


def train_model(
    architecture: str,
    training_seed: int,
    steps: int,
    batch_size: int,
    learning_rate: float,
    profiles: dict[str, np.ndarray],
) -> dict[str, Any]:
    model = initialize(architecture, 1410000 + training_seed)
    square_average = {key: np.zeros_like(value) for key, value in model["params"].items()}
    decay = 0.99
    for step in range(1, steps + 1):
        x, y, _ = sample_batch(
            1420000 + 100000 * training_seed + step,
            E009.TRAIN_PAIRS,
            batch_size,
            profiles,
            noise=True,
        )
        _, grads = E009.loss_and_grad(model, x, y)
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
    seed: int,
    count: int,
    profiles: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    x, y, pair = sample_batch(seed, E009.HELDOUT_PAIRS, count, profiles, noise=False)
    # Only pair-specific baselines remain after the intervention boundary.
    x[:, E009.INTERVENTION_STEP - 1 :, 0] = profiles["bias_a"][pair, None]
    x[:, E009.INTERVENTION_STEP - 1 :, 4] = profiles["bias_b"][pair, None]
    return {"x": x, "y": y, "pair": pair}


def baseline_variants(
    episodes: dict[str, np.ndarray], profiles: dict[str, np.ndarray]
) -> dict[str, np.ndarray]:
    x, pair = episodes["x"], episodes["pair"]
    ab = x.copy()
    a0 = x.copy()
    a0[:, :, 4] = profiles["bias_b"][pair, None]
    zero_b = x.copy()
    zero_b[:, :, 0] = profiles["bias_a"][pair, None]
    zero_both = a0.copy()
    zero_both[:, :, 0] = profiles["bias_a"][pair, None]
    return {"ab": ab, "a0": a0, "0b": zero_b, "00": zero_both}


def prefix_state(model: dict[str, Any], x: np.ndarray, reverse_order: bool = False) -> np.ndarray:
    prefix = x[:, : E009.INTERVENTION_STEP].copy()
    if reverse_order:
        prefix[:, : E009.INTERVENTION_STEP - 1] = (
            prefix[:, : E009.INTERVENTION_STEP - 1][:, ::-1]
        )
    _, states = E009.forward(model, prefix)
    return states[-1]


def directed_component(architecture: str, states: dict[str, np.ndarray]) -> np.ndarray:
    a_indices, b_indices = receiver_indices(architecture)
    component = np.zeros_like(states["ab"])
    component[:, a_indices] = states["ab"][:, a_indices] - states["a0"][:, a_indices]
    component[:, b_indices] = states["ab"][:, b_indices] - states["0b"][:, b_indices]
    return component


def response_for_components(
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    normal_logits: np.ndarray,
    base: np.ndarray,
    component: np.ndarray,
    donor: np.ndarray,
    reverse_component: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    hidden = {
        "delete": base - component,
        "exchange": base - component + component[donor],
        "sign_flip": base - 2.0 * component,
        "compose": base + component[donor],
        "temporal_reverse": base - component + reverse_component,
    }
    logits = {
        operator: E010.continue_from(model, state.copy(), episodes["x"])
        for operator, state in hidden.items()
    }
    responses = {
        operator: E010.probability_response(value, normal_logits)
        for operator, value in logits.items()
    }
    return logits, responses


def audit(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    profiles: dict[str, np.ndarray],
    random_seed: int,
    random_draws: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray], list[dict[str, np.ndarray]]]:
    variants = baseline_variants(episodes, profiles)
    states = {name: prefix_state(model, value) for name, value in variants.items()}
    reversed_states = {
        name: prefix_state(model, value, reverse_order=True)
        for name, value in variants.items()
    }
    component = directed_component(architecture, states)
    reverse_component = directed_component(architecture, reversed_states)
    donor = E010.cross_pair_donor(episodes["pair"])
    normal_logits = E010.continue_from(model, states["ab"].copy(), episodes["x"])
    normal_loss = E009.cross_entropy(normal_logits, episodes["y"])
    relation_logits, relation_responses = response_for_components(
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
        random_logits, fields = response_for_components(
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
            E009.cross_entropy(random_logits["delete"], episodes["y"]) - normal_loss
        )

    delete_loss_increase = (
        E009.cross_entropy(relation_logits["delete"], episodes["y"]) - normal_loss
    )
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
        "normal_both_correct": E010.both_correct(normal_logits, episodes["y"]),
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

    counts = {architecture: active_parameter_count(architecture) for architecture in ARCHITECTURES}
    profiles = E009.pair_profiles()
    episodes = evaluation_episodes(1430001, args.test_episodes, profiles)
    performance_x, performance_y, _ = sample_batch(
        1430002, E009.HELDOUT_PAIRS, args.test_episodes, profiles, noise=True
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
            performance = E009.evaluate(model, performance_x, performance_y)
            metrics, relation[architecture], random[architecture] = audit(
                architecture,
                model,
                episodes,
                profiles,
                1440000 + 100 * training_seed + architecture_index,
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
                left = E012.field_matrix(relation[left_architecture])
                right = E012.field_matrix(relation[right_architecture])
                relation_cka = E012.linear_cka(left, right)
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
        "interacting_accuracy_minimum_0_85": all(
            architecture_summary[architecture]["heldout_both_correct"]["minimum"] >= 0.85
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "independent_accuracy_maximum_0_45": (
            architecture_summary["independent"]["heldout_both_correct"]["maximum"] <= 0.45
        ),
        "independent_component_zero": (
            architecture_summary["independent"]["component_norm"]["maximum"] < 1e-10
        ),
        "interacting_component_norm_minimum_above_0_01": all(
            architecture_summary[architecture]["component_norm"]["minimum"] > 0.01
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "delete_loss_increase_median_at_least_0_10": all(
            architecture_summary[architecture]["delete_cross_entropy_increase"]["median"] >= 0.10
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "delete_selectivity_median_at_least_0_05": all(
            architecture_summary[architecture]["delete_selectivity"]["median"] >= 0.05
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "positive_selectivity_at_least_four_seeds": all(
            architecture_summary[architecture]["positive_selectivity_seed_count"] >= 4
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
        "schema": "sio-local-p014-confirmation-pipeline-transfer-v1",
        "status": "LOCAL_PILOT_COMPLETE",
        "pilot_readout": readout,
        "quick": bool(args.quick),
        "task": "delayed three-valued checksum coordination",
        "target_rule": "(private_A + private_B + rule) mod 3",
        "new_architecture": NEW_ARCHITECTURE,
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
            "A supported pilot establishes pipeline feasibility in one additional synthetic "
            "world and architecture. It is not confirmatory evidence for Experiment 005."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "sio-local-p014-output-manifest-v1",
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
