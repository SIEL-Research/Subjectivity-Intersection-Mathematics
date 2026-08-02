#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Cross-world transfer audit for the relational carrier criterion.

The extraction and intervention rules are frozen from Local Exploration 008,
but the learning world is changed to a three-class temporal-order task with a
24-dimensional state, six action logits, and RMSProp optimization.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


STATE_DIM = 24
INPUT_DIM = 8
CLASS_COUNT = 3
OUTPUT_DIM = 2 * CLASS_COUNT
SEQUENCE_LENGTH = 8
INTERVENTION_STEP = 4
PAIR_COUNT = 128
TRAIN_PAIRS = tuple(range(0, PAIR_COUNT, 2))
HELDOUT_PAIRS = tuple(range(1, PAIR_COUNT, 2))
TRAIN_TOLERANCES = (0.35, 1.25)
HELDOUT_TOLERANCES = (0.80,)
ARCHITECTURES = ("independent", "distributed", "central_shared", "directional_relay")
INTERACTING_ARCHITECTURES = ARCHITECTURES[1:]
OPERATORS = ("delete", "exchange", "sign_flip", "compose", "temporal_reverse")
CORNER_SIGNS = np.asarray([1.0, -1.0, -1.0, 1.0], dtype=np.float64)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=3500)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.004)
    parser.add_argument("--training-seeds", type=int, default=5)
    parser.add_argument("--eval-per-pair", type=int, default=48)
    parser.add_argument("--test-quartets", type=int, default=4096)
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args()


def architecture_masks(name: str) -> dict[str, np.ndarray]:
    recurrent = np.zeros((STATE_DIM, STATE_DIM), dtype=np.float64)
    inputs = np.zeros((STATE_DIM, INPUT_DIM), dtype=np.float64)
    outputs = np.zeros((OUTPUT_DIM, STATE_DIM), dtype=np.float64)

    if name == "independent":
        recurrent[:12, :12] = 1.0
        recurrent[12:, 12:] = 1.0
        inputs[:12, :4] = 1.0
        inputs[12:, 4:] = 1.0
        outputs[:3, :12] = 1.0
        outputs[3:, 12:] = 1.0
    elif name == "distributed":
        for row in range(12):
            for delta in range(6):
                recurrent[row, (row + delta) % 12] = 1.0
                recurrent[row, 12 + (row + delta) % 12] = 1.0
        for local_row in range(12):
            row = 12 + local_row
            for delta in range(6):
                recurrent[row, 12 + (local_row + delta) % 12] = 1.0
                recurrent[row, (local_row + delta) % 12] = 1.0
        inputs[:12, :4] = 1.0
        inputs[12:, 4:] = 1.0
        outputs[:3, :12] = 1.0
        outputs[3:, 12:] = 1.0
    elif name == "central_shared":
        # A local 0..5, B local 6..11, shared 12..23.
        recurrent[0:6, 0:6] = 1.0
        recurrent[0:6, 12:18] = 1.0
        recurrent[6:12, 6:12] = 1.0
        recurrent[6:12, 18:24] = 1.0
        for shared_row in range(12):
            row = 12 + shared_row
            for delta in range(6):
                recurrent[row, 12 + (shared_row + delta) % 12] = 1.0
            for delta in range(3):
                recurrent[row, (shared_row + delta) % 6] = 1.0
                recurrent[row, 6 + (shared_row + delta + 1) % 6] = 1.0
        inputs[0:6, :4] = 1.0
        inputs[6:12, 4:] = 1.0
        inputs[12:, 0] = 1.0
        inputs[12:, 1] = 1.0
        inputs[12:, 4] = 1.0
        inputs[12:, 5] = 1.0
        outputs[:3, 0:6] = 1.0
        outputs[:3, 12:18] = 1.0
        outputs[3:, 6:12] = 1.0
        outputs[3:, 18:24] = 1.0
    elif name == "directional_relay":
        # A local 0..8, B local 9..17, A-to-B 18..20, B-to-A 21..23.
        recurrent[0:9, 0:9] = 1.0
        recurrent[0:9, 21:24] = 1.0
        recurrent[9:18, 9:18] = 1.0
        recurrent[9:18, 18:21] = 1.0
        recurrent[18:21, 0:9] = 1.0
        recurrent[18:21, 18:21] = 1.0
        recurrent[21:24, 9:18] = 1.0
        recurrent[21:24, 21:24] = 1.0
        inputs[0:9, :4] = 1.0
        inputs[9:18, 4:] = 1.0
        inputs[18:21, :4] = 1.0
        inputs[21:24, 4:] = 1.0
        outputs[:3, 0:9] = 1.0
        outputs[:3, 21:24] = 1.0
        outputs[3:, 9:18] = 1.0
        outputs[3:, 18:21] = 1.0
    else:
        raise ValueError(name)

    assert int(recurrent.sum()) == 288, (name, recurrent.sum())
    assert int(inputs.sum()) == 96, (name, inputs.sum())
    assert int(outputs.sum()) == 72, (name, outputs.sum())
    return {"recurrent": recurrent, "inputs": inputs, "outputs": outputs}


def active_parameter_count(masks: dict[str, np.ndarray]) -> int:
    return int(
        masks["recurrent"].sum()
        + masks["inputs"].sum()
        + masks["outputs"].sum()
        + STATE_DIM
        + OUTPUT_DIM
    )


def pair_profiles() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(20261401)
    return {
        "gain_a": rng.uniform(0.72, 1.28, size=PAIR_COUNT),
        "gain_b": rng.uniform(0.72, 1.28, size=PAIR_COUNT),
        "bias_a": rng.uniform(-0.16, 0.16, size=PAIR_COUNT),
        "bias_b": rng.uniform(-0.16, 0.16, size=PAIR_COUNT),
    }


def event_times_for_classes(
    rng: np.random.Generator,
    classes: np.ndarray,
    tolerance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    count = classes.shape[0]
    event_a = np.empty(count)
    event_b = np.empty(count)
    for index in range(count):
        tol = float(tolerance[index])
        if classes[index] == 0:
            event_a[index] = rng.uniform(0.30, 0.85)
            event_b[index] = event_a[index] + rng.uniform(tol + 0.12, tol + 0.72)
        elif classes[index] == 2:
            event_b[index] = rng.uniform(0.30, 0.85)
            event_a[index] = event_b[index] + rng.uniform(tol + 0.12, tol + 0.72)
        else:
            centre = rng.uniform(0.65, 1.85)
            difference = rng.uniform(-0.78 * tol, 0.78 * tol)
            event_a[index] = centre - 0.5 * difference
            event_b[index] = centre + 0.5 * difference
    return event_a, event_b


def class_from_times(event_a: np.ndarray, event_b: np.ndarray, tolerance: np.ndarray) -> np.ndarray:
    difference = event_b - event_a
    out = np.ones(event_a.shape[0], dtype=np.int64)
    out[difference > tolerance] = 0
    out[difference < -tolerance] = 2
    return out


def make_inputs(
    event_a: np.ndarray,
    event_b: np.ndarray,
    pair: np.ndarray,
    tolerance: np.ndarray,
    profiles: dict[str, np.ndarray],
    rng: np.random.Generator | None,
) -> np.ndarray:
    time = np.arange(SEQUENCE_LENGTH, dtype=np.float64)
    pulse_a = np.exp(-0.5 * ((time[None, :] - event_a[:, None]) / 0.34) ** 2)
    pulse_b = np.exp(-0.5 * ((time[None, :] - event_b[:, None]) / 0.34) ** 2)
    if rng is None:
        noise_a = noise_b = 0.0
    else:
        noise_a = 0.025 * rng.normal(size=pulse_a.shape)
        noise_b = 0.025 * rng.normal(size=pulse_b.shape)
    observed_a = profiles["gain_a"][pair, None] * pulse_a + profiles["bias_a"][pair, None] + noise_a
    observed_b = profiles["gain_b"][pair, None] * pulse_b + profiles["bias_b"][pair, None] + noise_b
    x = np.empty((event_a.shape[0], SEQUENCE_LENGTH, INPUT_DIM), dtype=np.float64)
    x[:, :, 0] = observed_a
    x[:, :, 1] = time[None, :] / (SEQUENCE_LENGTH - 1)
    x[:, :, 2] = tolerance[:, None] / 1.5
    x[:, :, 3] = 1.0
    x[:, :, 4] = observed_b
    x[:, :, 5] = time[None, :] / (SEQUENCE_LENGTH - 1)
    x[:, :, 6] = tolerance[:, None] / 1.5
    x[:, :, 7] = 1.0
    return x


def sample_batch(
    seed: int,
    pairs: tuple[int, ...],
    tolerances: tuple[float, ...],
    batch_size: int,
    profiles: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    pair = rng.choice(np.asarray(pairs), size=batch_size, replace=True)
    tolerance = rng.choice(np.asarray(tolerances), size=batch_size, replace=True)
    requested_class = rng.integers(0, CLASS_COUNT, size=batch_size)
    event_a, event_b = event_times_for_classes(rng, requested_class, tolerance)
    y = class_from_times(event_a, event_b, tolerance)
    if not np.array_equal(y, requested_class):
        raise AssertionError("class sampler failed")
    x = make_inputs(event_a, event_b, pair, tolerance, profiles, rng)
    return x, y, pair, tolerance


def initialize(name: str, seed: int) -> dict[str, Any]:
    masks = architecture_masks(name)
    rng = np.random.default_rng(seed)
    params = {
        "recurrent": rng.normal(scale=0.18, size=(STATE_DIM, STATE_DIM)) * masks["recurrent"],
        "inputs": rng.normal(scale=0.24, size=(STATE_DIM, INPUT_DIM)) * masks["inputs"],
        "bias": np.zeros(STATE_DIM),
        "outputs": rng.normal(scale=0.16, size=(OUTPUT_DIM, STATE_DIM)) * masks["outputs"],
        "output_bias": np.zeros(OUTPUT_DIM),
    }
    return {"name": name, "masks": masks, "params": params}


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=-1, keepdims=True)


def forward(model: dict[str, Any], x: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    p = model["params"]
    hidden = np.zeros((x.shape[0], STATE_DIM), dtype=np.float64)
    states = [hidden]
    for position in range(x.shape[1]):
        hidden = np.tanh(x[:, position] @ p["inputs"].T + hidden @ p["recurrent"].T + p["bias"])
        states.append(hidden)
    logits = (hidden @ p["outputs"].T + p["output_bias"]).reshape(-1, 2, CLASS_COUNT)
    return logits, states


def loss_and_grad(
    model: dict[str, Any],
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, dict[str, np.ndarray]]:
    p = model["params"]
    logits, states = forward(model, x)
    probabilities = softmax(logits)
    targets = np.zeros_like(probabilities)
    targets[np.arange(y.shape[0]), 0, y] = 1.0
    targets[np.arange(y.shape[0]), 1, y] = 1.0
    loss = -float(np.mean(np.log(np.maximum(probabilities[np.arange(y.shape[0]), 0, y], 1e-12))))
    loss += -float(np.mean(np.log(np.maximum(probabilities[np.arange(y.shape[0]), 1, y], 1e-12))))
    loss *= 0.5
    dlogits = (probabilities - targets) / (2.0 * y.shape[0])
    flat_dlogits = dlogits.reshape(-1, OUTPUT_DIM)
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


def train_model(
    architecture: str,
    training_seed: int,
    steps: int,
    batch_size: int,
    learning_rate: float,
    profiles: dict[str, np.ndarray],
) -> dict[str, Any]:
    model = initialize(architecture, 910000 + training_seed)
    square_average = {key: np.zeros_like(value) for key, value in model["params"].items()}
    decay = 0.99
    for step in range(1, steps + 1):
        x, y, _, _ = sample_batch(
            920000 + 100000 * training_seed + step,
            TRAIN_PAIRS,
            TRAIN_TOLERANCES,
            batch_size,
            profiles,
        )
        _, grads = loss_and_grad(model, x, y)
        total_norm = math.sqrt(sum(float(np.sum(gradient * gradient)) for gradient in grads.values()))
        gradient_scale = min(1.0, 5.0 / (total_norm + 1e-12))
        for key, gradient in grads.items():
            gradient = gradient * gradient_scale
            square_average[key] = decay * square_average[key] + (1.0 - decay) * gradient * gradient
            model["params"][key] -= learning_rate * gradient / (np.sqrt(square_average[key]) + 1e-8)
        model["params"]["inputs"] *= model["masks"]["inputs"]
        model["params"]["recurrent"] *= model["masks"]["recurrent"]
        model["params"]["outputs"] *= model["masks"]["outputs"]
    return model


def cross_entropy(logits: np.ndarray, y: np.ndarray) -> float:
    probabilities = softmax(logits)
    flat_y = y.reshape(-1)
    repeated_y = np.repeat(flat_y, 2)
    selected = probabilities.reshape(-1, CLASS_COUNT)[
        np.arange(repeated_y.size), repeated_y
    ]
    return -float(np.mean(np.log(np.maximum(selected, 1e-12))))


def both_correct(logits: np.ndarray, y: np.ndarray) -> float:
    prediction = np.argmax(logits, axis=-1)
    return float(np.mean(np.all(prediction == y[:, :, None], axis=2)))


def evaluate(model: dict[str, Any], x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    logits, _ = forward(model, x)
    prediction = np.argmax(logits, axis=-1)
    return {
        "cross_entropy": cross_entropy(logits, y),
        "agent_accuracy": float(np.mean(prediction == y[:, None])),
        "both_correct": float(np.mean(np.all(prediction == y[:, None], axis=1))),
        "agreement": float(np.mean(prediction[:, 0] == prediction[:, 1])),
    }


def build_temporal_quartets(
    seed: int,
    count: int,
    profiles: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    pair = rng.choice(np.asarray(HELDOUT_PAIRS), size=count, replace=True)
    tolerance = rng.choice(np.asarray(HELDOUT_TOLERANCES), size=count, replace=True)
    event_a1 = rng.uniform(0.30, 2.25, size=count)
    event_a2 = rng.uniform(0.30, 2.25, size=count)
    event_b1 = rng.uniform(0.30, 2.25, size=count)
    event_b2 = rng.uniform(0.30, 2.25, size=count)
    event_corners = (
        (event_a1, event_b1),
        (event_a1, event_b2),
        (event_a2, event_b1),
        (event_a2, event_b2),
    )
    x = np.stack(
        [make_inputs(a, b, pair, tolerance, profiles, None) for a, b in event_corners],
        axis=1,
    )
    # Remove any pulse tail after the intervention boundary while retaining
    # pair-specific baselines. All four cases then receive an identical suffix.
    x[:, :, INTERVENTION_STEP - 1 :, 0] = profiles["bias_a"][pair, None, None]
    x[:, :, INTERVENTION_STEP - 1 :, 4] = profiles["bias_b"][pair, None, None]
    y = np.stack(
        [class_from_times(a, b, tolerance) for a, b in event_corners], axis=1
    )
    return {"x": x, "y": y, "pair": pair, "tolerance": tolerance}


def flatten_quartets(x: np.ndarray) -> np.ndarray:
    return x.reshape(x.shape[0] * x.shape[1], x.shape[2], x.shape[3])


def prefix_state(model: dict[str, Any], x: np.ndarray, reverse_order: bool = False) -> np.ndarray:
    prefix = flatten_quartets(x[:, :, :INTERVENTION_STEP]).copy()
    if reverse_order:
        prefix[:, : INTERVENTION_STEP - 1] = prefix[:, : INTERVENTION_STEP - 1][:, ::-1]
    _, states = forward(model, prefix)
    return states[-1].reshape(x.shape[0], x.shape[1], STATE_DIM)


def continue_from(model: dict[str, Any], hidden: np.ndarray, x: np.ndarray) -> np.ndarray:
    p = model["params"]
    flat_hidden = hidden.reshape(-1, STATE_DIM)
    suffix = flatten_quartets(x[:, :, INTERVENTION_STEP:])
    for position in range(suffix.shape[1]):
        flat_hidden = np.tanh(
            suffix[:, position] @ p["inputs"].T
            + flat_hidden @ p["recurrent"].T
            + p["bias"]
        )
    logits = flat_hidden @ p["outputs"].T + p["output_bias"]
    return logits.reshape(hidden.shape[0], hidden.shape[1], 2, CLASS_COUNT)


def carrier_view(architecture: str, state: np.ndarray) -> np.ndarray:
    if architecture == "central_shared":
        return state[:, :, 12:]
    return state


def factorial_relation(state: np.ndarray) -> np.ndarray:
    h11, h12, h21, h22 = [state[:, index] for index in range(4)]
    return 0.25 * (h11 - h12 - h21 + h22)


def embed_delta(architecture: str, hidden: np.ndarray, delta: np.ndarray) -> np.ndarray:
    out = hidden.copy()
    if architecture == "central_shared":
        out[:, :, 12:] += delta
    else:
        out += delta
    return out


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


def probability_response(logits: np.ndarray, normal_logits: np.ndarray) -> np.ndarray:
    return softmax(logits) - softmax(normal_logits)


def operator_audit(
    architecture: str,
    model: dict[str, Any],
    quartets: dict[str, np.ndarray],
    random_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray], dict[str, np.ndarray], float]:
    x, y, pair = quartets["x"], quartets["y"], quartets["pair"]
    hidden = prefix_state(model, x)
    reversed_hidden = prefix_state(model, x, reverse_order=True)
    relation = factorial_relation(carrier_view(architecture, hidden))
    reversed_relation = factorial_relation(carrier_view(architecture, reversed_hidden))
    signed = CORNER_SIGNS[None, :, None] * relation[:, None, :]
    reversed_signed = CORNER_SIGNS[None, :, None] * reversed_relation[:, None, :]
    donor = cross_pair_donor(pair)
    donor_signed = CORNER_SIGNS[None, :, None] * relation[donor, None, :]
    normal_logits = continue_from(model, hidden, x)
    normal_loss = cross_entropy(normal_logits, y)
    normal_accuracy = both_correct(normal_logits, y)
    intervened = {
        "delete": embed_delta(architecture, hidden, -signed),
        "exchange": embed_delta(architecture, hidden, -signed + donor_signed),
        "sign_flip": embed_delta(architecture, hidden, -2.0 * signed),
        "compose": embed_delta(architecture, hidden, donor_signed),
        "temporal_reverse": embed_delta(architecture, hidden, -signed + reversed_signed),
    }
    rows = []
    responses = {}
    for operator in OPERATORS:
        logits = continue_from(model, intervened[operator], x)
        response = probability_response(logits, normal_logits)
        responses[operator] = response
        rows.append({
            "operator": operator,
            "normal_cross_entropy": normal_loss,
            "intervened_cross_entropy": cross_entropy(logits, y),
            "cross_entropy_increase": cross_entropy(logits, y) - normal_loss,
            "normal_both_correct": normal_accuracy,
            "intervened_both_correct": both_correct(logits, y),
            "accuracy_drop": normal_accuracy - both_correct(logits, y),
            "mean_absolute_probability_response": float(np.mean(np.abs(response))),
            "bilateral_response_fraction": float(
                np.mean(np.all(np.sum(np.abs(response), axis=3) > 1e-9, axis=2))
            ),
        })

    rng = np.random.default_rng(random_seed)
    norm = np.linalg.norm(relation, axis=1, keepdims=True)
    random_direction = rng.normal(size=relation.shape)
    random_direction /= np.maximum(np.linalg.norm(random_direction, axis=1, keepdims=True), 1e-12)
    random_relation = random_direction * norm
    random_reverse_direction = rng.normal(size=relation.shape)
    random_reverse_direction /= np.maximum(
        np.linalg.norm(random_reverse_direction, axis=1, keepdims=True), 1e-12
    )
    random_reverse_relation = random_reverse_direction * norm
    random_signed = CORNER_SIGNS[None, :, None] * random_relation[:, None, :]
    random_donor_signed = CORNER_SIGNS[None, :, None] * random_relation[donor, None, :]
    random_reverse_signed = CORNER_SIGNS[None, :, None] * random_reverse_relation[:, None, :]
    random_intervened = {
        "delete": embed_delta(architecture, hidden, -random_signed),
        "exchange": embed_delta(architecture, hidden, -random_signed + random_donor_signed),
        "sign_flip": embed_delta(architecture, hidden, -2.0 * random_signed),
        "compose": embed_delta(architecture, hidden, random_donor_signed),
        "temporal_reverse": embed_delta(
            architecture, hidden, -random_signed + random_reverse_signed
        ),
    }
    random_responses = {
        operator: probability_response(
            continue_from(model, random_intervened[operator], x), normal_logits
        )
        for operator in OPERATORS
    }

    random_delete_losses = []
    random_delete_accuracies = []
    for _ in range(16):
        direction = rng.normal(size=relation.shape)
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)
        random_component = direction * norm
        random_component_signed = CORNER_SIGNS[None, :, None] * random_component[:, None, :]
        logits = continue_from(
            model, embed_delta(architecture, hidden, -random_component_signed), x
        )
        random_delete_losses.append(cross_entropy(logits, y) - normal_loss)
        random_delete_accuracies.append(normal_accuracy - both_correct(logits, y))
    random_loss = float(np.median(random_delete_losses))
    random_accuracy = float(np.median(random_delete_accuracies))
    for row in rows:
        row["random_delete_cross_entropy_increase"] = random_loss
        row["random_delete_accuracy_drop"] = random_accuracy
        if row["operator"] == "delete":
            row["delete_vs_random_loss_selectivity"] = row["cross_entropy_increase"] - random_loss
            row["delete_vs_random_accuracy_selectivity"] = row["accuracy_drop"] - random_accuracy
        else:
            row["delete_vs_random_loss_selectivity"] = ""
            row["delete_vs_random_accuracy_selectivity"] = ""
    relation_norm = float(np.mean(np.linalg.norm(relation, axis=1) / math.sqrt(relation.shape[1])))
    return rows, responses, random_responses, relation_norm


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / max(denominator, 1e-12))


def pearson(left: np.ndarray, right: np.ndarray) -> float:
    return cosine(left - left.mean(), right - right.mean())


def permutation_correlation(
    left: np.ndarray,
    right: np.ndarray,
    seed: int,
    repetitions: int = 199,
) -> dict[str, float]:
    observed = pearson(left, right)
    rng = np.random.default_rng(seed)
    null = [
        abs(pearson(left, right[rng.permutation(right.shape[0])]))
        for _ in range(repetitions)
    ]
    return {
        "correlation": observed,
        "permutation_p": float(
            (1 + sum(value >= abs(observed) for value in null)) / (repetitions + 1)
        ),
        "null_abs_95": float(np.quantile(null, 0.95)),
    }


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
        args.eval_per_pair = min(args.eval_per_pair, 3)
        args.test_quartets = min(args.test_quartets, 128)

    counts = {
        architecture: active_parameter_count(architecture_masks(architecture))
        for architecture in ARCHITECTURES
    }
    if set(counts.values()) != {486}:
        raise AssertionError(counts)

    profiles = pair_profiles()
    eval_x, eval_y, _, _ = sample_batch(
        930001,
        HELDOUT_PAIRS,
        HELDOUT_TOLERANCES,
        len(HELDOUT_PAIRS) * args.eval_per_pair,
        profiles,
    )
    quartets = build_temporal_quartets(930002, args.test_quartets, profiles)
    performance_rows = []
    intervention_rows = []
    correlation_rows = []

    for training_seed in range(args.training_seeds):
        relation_responses = {}
        random_responses = {}
        for architecture in ARCHITECTURES:
            model = train_model(
                architecture,
                training_seed,
                args.steps,
                args.batch_size,
                args.learning_rate,
                profiles,
            )
            performance_rows.append({
                "training_seed": training_seed,
                "architecture": architecture,
                **evaluate(model, eval_x, eval_y),
            })
            rows, responses, null_responses, relation_norm = operator_audit(
                architecture,
                model,
                quartets,
                940000 + 100 * training_seed + ARCHITECTURES.index(architecture),
            )
            relation_responses[architecture] = responses
            random_responses[architecture] = null_responses
            for row in rows:
                intervention_rows.append({
                    "training_seed": training_seed,
                    "architecture": architecture,
                    "relation_norm": relation_norm,
                    **row,
                })

        architecture_pairs = (
            ("central_shared", "distributed"),
            ("central_shared", "directional_relay"),
            ("distributed", "directional_relay"),
        )
        for pair_index, (left_architecture, right_architecture) in enumerate(architecture_pairs):
            for component_index, (component_type, source) in enumerate((
                ("relation", relation_responses),
                ("random_equal_norm", random_responses),
            )):
                for operator_index, operator in enumerate(OPERATORS):
                    for agent in range(2):
                        left = source[left_architecture][operator][:, :, agent, :].reshape(-1)
                        right = source[right_architecture][operator][:, :, agent, :].reshape(-1)
                        result = permutation_correlation(
                            left,
                            right,
                            950000
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
    write_csv(args.out_dir / "performance.csv", performance_rows)
    write_csv(args.out_dir / "intervention_metrics.csv", intervention_rows)
    write_csv(args.out_dir / "response_correlations.csv", correlation_rows)

    performance_summary = {}
    for architecture in ARCHITECTURES:
        chosen = [row for row in performance_rows if row["architecture"] == architecture]
        performance_summary[architecture] = {
            field: summarize([float(row[field]) for row in chosen])
            for field in ("cross_entropy", "agent_accuracy", "both_correct", "agreement")
        }

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
        intervention_summary[architecture]["relation_norm"] = summarize(
            [float(row["relation_norm"]) for row in delete_rows]
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
        for component_type in ("relation", "random_equal_norm"):
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
            medians["relation"] - medians["random_equal_norm"]
        )

    # Frozen local exploratory acceptance criteria, specified before the full
    # run. Failure of any criterion prevents a cross-world transfer readout.
    checks = {
        "capacity_exact": set(counts.values()) == {486},
        "interacting_baseline_both_correct_median_above_0_55": all(
            performance_summary[architecture]["both_correct"]["median"] > 0.55
            for architecture in INTERACTING_ARCHITECTURES
        ),
        "independent_relation_zero": (
            intervention_summary["independent"]["relation_norm"]["maximum"] < 1e-10
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
        "relation_response_correlation_minimum_above_0_20": all(
            correlation_summary[key]["relation"]["response_correlation"]["minimum"] > 0.20
            for key in correlation_summary
        ),
        "relation_permutation_p_maximum_0_005": all(
            correlation_summary[key]["relation"]["permutation_p_maximum"] <= 0.005
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
        "schema": "sio-local-e009-cross-world-transfer-v1",
        "status": "LOCAL_EXPLORATORY_COMPLETE",
        "cross_world_transfer_readout": readout,
        "quick": bool(args.quick),
        "world_changes": {
            "task": "three-class temporal event-order coordination",
            "state_dimension": STATE_DIM,
            "action": "two three-class softmax outputs",
            "optimizer": "RMSProp",
            "sequence_length": SEQUENCE_LENGTH,
            "heldout_tolerance": list(HELDOUT_TOLERANCES),
        },
        "capacity": {"active_parameter_counts": counts},
        "training": {
            "steps": args.steps,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "training_seeds": args.training_seeds,
        },
        "performance": performance_summary,
        "interventions": intervention_summary,
        "cross_architecture_response": correlation_summary,
        "acceptance_checks": checks,
        "claim_boundary": (
            "Synthetic local stress transfer. The task family, state dimension, action representation, "
            "optimizer, and topology are changed together. A failed readout would require factorial "
            "decomposition; a supported readout does not isolate which change is individually sufficient."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "sio-local-e009-output-manifest-v1",
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
        "cross_world_transfer_readout": readout,
        "quick": summary["quick"],
        "performance": performance_summary,
        "cross_architecture_response": correlation_summary,
        "acceptance_checks": checks,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
