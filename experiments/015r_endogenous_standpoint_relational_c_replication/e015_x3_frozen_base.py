#!/usr/bin/env python3
"""E015-X3 local exploratory scouting runner.

The simulator retains provenance only for scoring. Agent-side attribution sees
an unordered event pair plus the observer's own motor-command history. A
relational component is extracted post hoc from reservoir states and is never a
target, register, third agent, or special loss term.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
DEVELOPMENT_SEEDS = tuple(range(91900, 91908))
DISCOVERY_SEEDS = tuple(range(92000, 92032))
STEPS = 96
SWAP_STEP = 48
READAPT_STEPS = 8
EVAL_START = 24
LESION_STEP = 64
HORIZON = 12
WINDOW = 8
TRAIN_EPISODES = 20
TEST_EPISODES = 12
STATE_DIM = 48
INPUT_DIM = 9
RIDGE = 1e-3
INTERACTION_STRENGTH = 0.80
LEAK = 0.35
REPRESENTATION_TRAINING_STEPS = 500
REPRESENTATION_LEARNING_RATE = 0.008
CANDIDATES = tuple((sign, delay) for sign in (-1, 1) for delay in range(1, 5))
A_COLUMNS = (0, 2, 3, 4, 5, 6, 7, 8)
B_COLUMNS = (1,)
RANDOM_LESIONS = 16


@dataclass(frozen=True)
class Episode:
    actions: np.ndarray
    values: np.ndarray
    sources: np.ndarray
    maps_before: tuple[tuple[int, int], tuple[int, int]]
    maps_after: tuple[tuple[int, int], tuple[int, int]]
    port_swap: bool


@dataclass(frozen=True)
class View:
    x: np.ndarray
    target: np.ndarray
    role_accuracy: float
    post_swap_accuracy: float
    fixed_position_accuracy: float
    episode_index: int
    observer: int


@dataclass(frozen=True)
class Reservoir:
    kind: str
    inputs: np.ndarray
    bias: np.ndarray


def input_mask(kind: str) -> np.ndarray:
    mask = np.zeros((STATE_DIM, INPUT_DIM), dtype=float)
    if kind == "connected":
        mask[:] = 1.0
    elif kind == "additive":
        half = STATE_DIM // 2
        mask[:half, A_COLUMNS] = 1.0
        mask[half:, B_COLUMNS] = 1.0
    else:
        raise ValueError(kind)
    return mask


def train_reservoir(seed: int, kind: str, views: list[View]) -> Reservoir:
    rng = np.random.default_rng(seed)
    x = np.vstack([view.x[EVAL_START:-1] for view in views])
    target = np.concatenate([view.target[EVAL_START:-1] for view in views])
    mask = input_mask(kind)
    inputs = rng.normal(0.0, 0.22, size=(STATE_DIM, INPUT_DIM)) * mask
    bias = np.zeros(STATE_DIM, dtype=float)
    readout = rng.normal(0.0, 0.08, size=STATE_DIM)
    intercept = 0.0
    parameters = [inputs, bias, readout, np.asarray([intercept], dtype=float)]
    first = [np.zeros_like(value) for value in parameters]
    second = [np.zeros_like(value) for value in parameters]
    beta1, beta2 = 0.9, 0.999

    for step in range(1, REPRESENTATION_TRAINING_STEPS + 1):
        batch_indices = rng.integers(0, len(x), size=min(384, len(x)))
        batch_x = x[batch_indices]
        batch_y = target[batch_indices]
        hidden = np.tanh(batch_x @ inputs.T + bias)
        prediction = hidden @ readout + parameters[3][0]
        error = (2.0 / len(batch_x)) * (prediction - batch_y)
        grad_readout = hidden.T @ error + 1e-5 * readout
        grad_intercept = np.asarray([float(np.sum(error))])
        grad_hidden = error[:, None] * readout[None, :]
        grad_activation = grad_hidden * (1.0 - hidden * hidden)
        grad_inputs = (grad_activation.T @ batch_x + 1e-5 * inputs) * mask
        grad_bias = np.sum(grad_activation, axis=0)
        gradients = [grad_inputs, grad_bias, grad_readout, grad_intercept]

        for index, (parameter, gradient) in enumerate(zip(parameters, gradients)):
            first[index] = beta1 * first[index] + (1.0 - beta1) * gradient
            second[index] = beta2 * second[index] + (1.0 - beta2) * gradient * gradient
            corrected_first = first[index] / (1.0 - beta1 ** step)
            corrected_second = second[index] / (1.0 - beta2 ** step)
            parameter -= REPRESENTATION_LEARNING_RATE * corrected_first / (np.sqrt(corrected_second) + 1e-8)
        inputs *= mask

    return Reservoir(kind=kind, inputs=inputs, bias=bias)


def reservoir_states(reservoir: Reservoir, x: np.ndarray, initial: np.ndarray | None = None) -> np.ndarray:
    state = np.zeros(STATE_DIM, dtype=float) if initial is None else np.asarray(initial, dtype=float).copy()
    states = np.empty((len(x), STATE_DIM), dtype=float)
    for index, row in enumerate(x):
        instantaneous = np.tanh(reservoir.inputs @ row + reservoir.bias)
        state = LEAK * state + (1.0 - LEAK) * instantaneous
        states[index] = state
    return states


def advance(reservoir: Reservoir, state: np.ndarray, row: np.ndarray) -> np.ndarray:
    instantaneous = np.tanh(reservoir.inputs @ row + reservoir.bias)
    return LEAK * state + (1.0 - LEAK) * instantaneous


def generate_episode(seed: int, port_swap: bool) -> Episode:
    rng = np.random.default_rng(seed)
    actions = rng.choice(np.array([-1, 0, 1], dtype=int), size=(2, STEPS))
    first = CANDIDATES[int(rng.integers(0, len(CANDIDATES)))]
    remaining = tuple(candidate for candidate in CANDIDATES if candidate != first)
    second = remaining[int(rng.integers(0, len(remaining)))]
    before = (first, second)
    after = (second, first) if port_swap else before
    values = np.empty((STEPS, 2), dtype=float)
    sources = np.empty((STEPS, 2), dtype=int)

    previous_generated = np.zeros(2, dtype=float)
    for t in range(STEPS):
        current = after if t >= SWAP_STEP else before
        generated = []
        for actor in (0, 1):
            sign, delay = current[actor]
            own_index = t - delay
            base = sign * float(actions[actor, own_index]) if own_index >= 0 else 0.0
            other = 1 - actor
            modulation = 1.0 + INTERACTION_STRENGTH * math.tanh(float(previous_generated[other]))
            generated.append(base * modulation + float(rng.uniform(-0.045, 0.045)))
        previous_generated = np.asarray(generated, dtype=float)
        order = rng.permutation(2)
        values[t] = np.asarray(generated)[order]
        sources[t] = order

    return Episode(
        actions=actions,
        values=values,
        sources=sources,
        maps_before=before,
        maps_after=after,
        port_swap=port_swap,
    )


def candidate_loss(actions: np.ndarray, values: np.ndarray, end_t: int, candidate: tuple[int, int]) -> float:
    sign, delay = candidate
    losses = []
    for t in range(max(0, end_t - WINDOW), end_t):
        source_index = t - delay
        if source_index < 0:
            continue
        prediction = sign * float(actions[source_index])
        losses.append(float(np.min((values[t] - prediction) ** 2)))
    return float(np.mean(losses)) if losses else float("inf")


def infer_mapping(actions: np.ndarray, values: np.ndarray, end_t: int) -> tuple[int, int]:
    losses = [candidate_loss(actions, values, end_t, candidate) for candidate in CANDIDATES]
    return CANDIDATES[min(range(len(CANDIDATES)), key=lambda index: (losses[index], index))]


def choose_event(values: np.ndarray, actions: np.ndarray, t: int, mapping: tuple[int, int]) -> int:
    sign, delay = mapping
    source_index = t - delay
    prediction = sign * float(actions[source_index]) if source_index >= 0 else 0.0
    distances = np.abs(values - prediction)
    return int(0 if distances[0] <= distances[1] else 1)


def build_view(episode: Episode, observer: int, episode_index: int) -> View:
    self_stream = np.empty(STEPS, dtype=float)
    other_stream = np.empty(STEPS, dtype=float)
    correct = np.zeros(STEPS, dtype=float)
    fixed = np.zeros(STEPS, dtype=float)
    inferred_sign = np.empty(STEPS, dtype=float)
    inferred_delay = np.empty(STEPS, dtype=float)
    expected_next = np.empty(STEPS, dtype=float)
    actions = episode.actions[observer]
    for t in range(STEPS):
        mapping = infer_mapping(actions, episode.values, t)
        inferred_sign[t] = float(mapping[0])
        inferred_delay[t] = (float(mapping[1]) - 2.5) / 1.5
        expected_index = t + 1 - mapping[1]
        expected_next[t] = (
            float(mapping[0]) * float(actions[expected_index])
            if 0 <= expected_index <= t
            else 0.0
        )
        chosen = choose_event(episode.values[t], actions, t, mapping)
        other = 1 - chosen
        self_stream[t] = episode.values[t, chosen]
        other_stream[t] = episode.values[t, other]
        correct[t] = float(episode.sources[t, chosen] == observer)
        fixed[t] = float(episode.sources[t, 0] == observer)

    x = np.zeros((STEPS, INPUT_DIM), dtype=float)
    x[:, 0] = self_stream
    x[:, 1] = other_stream
    for lag, column in enumerate((2, 3, 4, 5)):
        if lag == 0:
            x[:, column] = actions
        else:
            x[lag:, column] = actions[:-lag]
    x[:, 6] = inferred_sign
    x[:, 7] = inferred_delay
    x[:, 8] = expected_next
    target = np.roll(self_stream, -1)
    target[-1] = target[-2]
    post_start = SWAP_STEP + READAPT_STEPS
    post = float(np.mean(correct[post_start:])) if episode.port_swap else float(np.mean(correct[EVAL_START:]))
    return View(
        x=x,
        target=target,
        role_accuracy=float(np.mean(correct[EVAL_START:])),
        post_swap_accuracy=post,
        fixed_position_accuracy=float(np.mean(fixed[EVAL_START:])),
        episode_index=episode_index,
        observer=observer,
    )


def fit_readout(reservoir: Reservoir, views: list[View]) -> np.ndarray:
    design_rows = []
    targets = []
    for view in views:
        states = reservoir_states(reservoir, view.x)
        design_rows.append(states[EVAL_START:-1])
        targets.append(view.target[EVAL_START:-1])
    design = np.vstack(design_rows)
    target = np.concatenate(targets)
    augmented = np.column_stack([design, np.ones(len(design))])
    penalty = np.eye(STATE_DIM + 1) * RIDGE
    penalty[-1, -1] = 0.0
    return np.linalg.solve(augmented.T @ augmented + penalty, augmented.T @ target)


def predict(beta: np.ndarray, states: np.ndarray) -> np.ndarray:
    return states @ beta[:-1] + beta[-1]


def r_squared(target: np.ndarray, prediction: np.ndarray) -> float:
    denominator = float(np.sum((target - np.mean(target)) ** 2))
    return 1.0 - float(np.sum((target - prediction) ** 2)) / max(denominator, 1e-12)


def evaluate_predictions(reservoir: Reservoir, beta: np.ndarray, views: list[View]) -> float:
    targets = []
    predictions = []
    for view in views:
        states = reservoir_states(reservoir, view.x)
        targets.append(view.target[EVAL_START:-1])
        predictions.append(predict(beta, states)[EVAL_START:-1])
    return r_squared(np.concatenate(targets), np.concatenate(predictions))


def shuffled_other_r2(reservoir: Reservoir, beta: np.ndarray, views: list[View]) -> float:
    targets = []
    predictions = []
    for index, view in enumerate(views):
        donor = views[(index + 2) % len(views)]
        shuffled = view.x.copy()
        shuffled[:, 1] = donor.x[:, 1]
        states = reservoir_states(reservoir, shuffled)
        targets.append(view.target[EVAL_START:-1])
        predictions.append(predict(beta, states)[EVAL_START:-1])
    return r_squared(np.concatenate(targets), np.concatenate(predictions))


def four_history_states(reservoir: Reservoir, x: np.ndarray) -> dict[str, np.ndarray]:
    variants = {name: x.copy() for name in ("ab", "a0", "0b", "00")}
    variants["a0"][:, B_COLUMNS] = 0.0
    variants["0b"][:, A_COLUMNS] = 0.0
    variants["00"][:, :] = 0.0
    return {name: reservoir_states(reservoir, value) for name, value in variants.items()}


def component(states: dict[str, np.ndarray]) -> np.ndarray:
    return states["ab"] - states["a0"] - states["0b"] + states["00"]


def future_output(
    reservoir: Reservoir,
    beta: np.ndarray,
    initial: np.ndarray,
    x: np.ndarray,
    start: int,
    horizon: int,
) -> np.ndarray:
    state = initial.copy()
    outputs = []
    for t in range(start, min(len(x), start + horizon)):
        state = advance(reservoir, state, x[t])
        outputs.append(float(state @ beta[:-1] + beta[-1]))
    return np.asarray(outputs, dtype=float)


def view_component_record(
    reservoir: Reservoir,
    additive: Reservoir,
    beta: np.ndarray,
    view: View,
    rng: np.random.Generator,
) -> dict[str, object]:
    states = four_history_states(reservoir, view.x)
    c = component(states)
    additive_states = four_history_states(additive, view.x)
    additive_c = component(additive_states)
    c_t = c[LESION_STEP]
    baseline_state = states["ab"][LESION_STEP]
    baseline = future_output(reservoir, beta, baseline_state, view.x, LESION_STEP + 1, HORIZON)
    deleted = future_output(reservoir, beta, baseline_state - c_t, view.x, LESION_STEP + 1, HORIZON)
    scale = max(float(np.std(view.target[EVAL_START:])), 1e-9)
    deletion_effect = float(np.mean(np.abs(baseline - deleted)) / scale)

    random_effects = []
    c_norm = float(np.linalg.norm(c_t))
    for _ in range(RANDOM_LESIONS):
        direction = rng.normal(size=STATE_DIM)
        direction *= c_norm / max(float(np.linalg.norm(direction)), 1e-12)
        random_output = future_output(
            reservoir, beta, baseline_state - direction, view.x, LESION_STEP + 1, HORIZON
        )
        random_effects.append(float(np.mean(np.abs(baseline - random_output)) / scale))

    deleted_next = advance(reservoir, baseline_state - c_t, view.x[LESION_STEP + 1])
    baseline_next_c = c[LESION_STEP + 1]
    intervened_next_c = (
        deleted_next
        - states["a0"][LESION_STEP + 1]
        - states["0b"][LESION_STEP + 1]
        + states["00"][LESION_STEP + 1]
    )
    transported = baseline_next_c - intervened_next_c
    transport_fraction = float(np.linalg.norm(transported) / max(np.linalg.norm(baseline_next_c), 1e-12))
    return {
        "episode_index": view.episode_index,
        "observer": view.observer,
        "c": c_t,
        "baseline_state": baseline_state,
        "baseline_output": baseline,
        "output_scale": scale,
        "c_rms": float(np.linalg.norm(c_t) / math.sqrt(STATE_DIM)),
        "additive_c_rms": float(np.linalg.norm(additive_c[LESION_STEP]) / math.sqrt(STATE_DIM)),
        "deletion_effect": deletion_effect,
        "random_effect": float(np.mean(random_effects)),
        "transport_fraction": transport_fraction,
        "x": view.x,
    }


def add_exchange_effects(
    reservoir: Reservoir, beta: np.ndarray, records: list[dict[str, object]]
) -> None:
    for index, record in enumerate(records):
        donor = records[(index + 2) % len(records)]
        c = np.asarray(record["c"], dtype=float)
        donor_c = np.asarray(donor["c"], dtype=float)
        donor_c = donor_c * (np.linalg.norm(c) / max(np.linalg.norm(donor_c), 1e-12))
        baseline_state = np.asarray(record["baseline_state"], dtype=float)
        x = np.asarray(record["x"], dtype=float)
        exchanged = future_output(
            reservoir,
            beta,
            baseline_state - c + donor_c,
            x,
            LESION_STEP + 1,
            HORIZON,
        )
        baseline = np.asarray(record["baseline_output"], dtype=float)
        record["exchange_effect"] = float(
            np.mean(np.abs(baseline - exchanged)) / float(record["output_scale"])
        )


def evaluate_seed(seed: int) -> dict[str, float | int]:
    train_episodes = [
        generate_episode(seed * 1000 + 100 + index, port_swap=(index % 2 == 1))
        for index in range(TRAIN_EPISODES)
    ]
    test_episodes = [
        generate_episode(seed * 1000 + 500 + index, port_swap=(index % 2 == 1))
        for index in range(TEST_EPISODES)
    ]
    train_views = [
        build_view(episode, observer, index)
        for index, episode in enumerate(train_episodes)
        for observer in (0, 1)
    ]
    test_views = [
        build_view(episode, observer, index)
        for index, episode in enumerate(test_episodes)
        for observer in (0, 1)
    ]
    connected = train_reservoir(seed + 10_000_000, "connected", train_views)
    additive = train_reservoir(seed + 20_000_000, "additive", train_views)
    beta_connected = fit_readout(connected, train_views)
    beta_additive = fit_readout(additive, train_views)
    connected_r2 = evaluate_predictions(connected, beta_connected, test_views)
    additive_r2 = evaluate_predictions(additive, beta_additive, test_views)
    shuffled_r2 = shuffled_other_r2(connected, beta_connected, test_views)

    rng = np.random.default_rng(seed + 30_000_000)
    records = [
        view_component_record(connected, additive, beta_connected, view, rng)
        for view in test_views
    ]
    add_exchange_effects(connected, beta_connected, records)
    bilateral_minima = []
    for episode_index in range(TEST_EPISODES):
        pair = [float(row["deletion_effect"]) for row in records if row["episode_index"] == episode_index]
        bilateral_minima.append(min(pair))

    return {
        "seed": seed,
        "role_accuracy": float(np.mean([view.role_accuracy for view in test_views])),
        "post_swap_accuracy": float(
            np.mean([view.post_swap_accuracy for view in test_views if test_episodes[view.episode_index].port_swap])
        ),
        "fixed_position_accuracy": float(np.mean([view.fixed_position_accuracy for view in test_views])),
        "connected_r2": connected_r2,
        "additive_r2": additive_r2,
        "shuffled_other_r2": shuffled_r2,
        "connected_advantage": connected_r2 - additive_r2,
        "shuffle_drop": connected_r2 - shuffled_r2,
        "c_rms": float(np.mean([float(row["c_rms"]) for row in records])),
        "additive_c_rms": float(np.max([float(row["additive_c_rms"]) for row in records])),
        "deletion_effect": float(np.mean([float(row["deletion_effect"]) for row in records])),
        "random_effect": float(np.mean([float(row["random_effect"]) for row in records])),
        "deletion_specificity": float(
            np.mean([float(row["deletion_effect"]) - float(row["random_effect"]) for row in records])
        ),
        "bilateral_min_effect": float(np.mean(bilateral_minima)),
        "transport_fraction": float(np.mean([float(row["transport_fraction"]) for row in records])),
        "exchange_effect": float(np.mean([float(row["exchange_effect"]) for row in records])),
    }


def summarize(rows: list[dict[str, float | int]], phase: str) -> dict[str, object]:
    metric_names = [name for name in rows[0] if name != "seed"]
    means = {name: float(np.mean([float(row[name]) for row in rows])) for name in metric_names}
    heuristics = {
        "role_accuracy": means["role_accuracy"] >= 0.70,
        "post_swap_accuracy": means["post_swap_accuracy"] >= 0.68,
        "connected_competence": means["connected_r2"] >= 0.50,
        "additive_competence": means["additive_r2"] >= 0.30,
        "connected_advantage": means["connected_advantage"] >= 0.02,
        "shuffled_other_drop": means["shuffle_drop"] >= 0.02,
        "connected_c_present": means["c_rms"] >= 0.01,
        "additive_c_null": means["additive_c_rms"] <= 1e-10,
        "bilateral_deletion": means["bilateral_min_effect"] >= 0.005,
        "later_c_transport": means["transport_fraction"] >= 0.10,
        "c_specificity_over_random": means["deletion_specificity"] > 0.0,
        "fixed_position_leakage_null": 0.47 <= means["fixed_position_accuracy"] <= 0.53,
    }
    return {
        "experiment": "E015-X3",
        "phase": phase,
        "evidence_status": "Exploratory result",
        "qualifiers": ["local", "synthetic", "not preregistered", "not independently replicated"],
        "promising": all(heuristics.values()),
        "heuristics_passed": sum(bool(value) for value in heuristics.values()),
        "heuristics_total": len(heuristics),
        "heuristics": heuristics,
        "means": means,
        "seeds": [int(row["seed"]) for row in rows],
        "claim_boundary": (
            "This scout can only indicate whether the tested synthetic mechanism is worth a new confirmatory design. "
            "It is not an E015 result and cannot establish consciousness, qualia, ontological Intersection "
            "Subjectivity, nonseparable ontological C, or O3."
        ),
    }


def render_report(summary: dict[str, object]) -> str:
    means = summary["means"]
    heuristics = summary["heuristics"]
    lines = [
        f"# E015-X3 {summary['phase']} scouting result",
        "",
        f"- evidence status: **{summary['evidence_status']}**",
        f"- promising under pre-run scouting heuristics: **{str(summary['promising']).lower()}**",
        f"- heuristics passed: **{summary['heuristics_passed']}/{summary['heuristics_total']}**",
        f"- provenance accuracy: `{means['role_accuracy']:.9f}`",
        f"- post-swap accuracy: `{means['post_swap_accuracy']:.9f}`",
        f"- connected prediction R2: `{means['connected_r2']:.9f}`",
        f"- additive prediction R2: `{means['additive_r2']:.9f}`",
        f"- connected advantage: `{means['connected_advantage']:.9f}`",
        f"- shuffled-other drop: `{means['shuffle_drop']:.9f}`",
        f"- connected C RMS: `{means['c_rms']:.9f}`",
        f"- additive C RMS: `{means['additive_c_rms']:.3e}`",
        f"- bilateral minimum deletion effect: `{means['bilateral_min_effect']:.9f}`",
        f"- C deletion minus random lesion: `{means['deletion_specificity']:.9f}`",
        f"- later-C transport fraction: `{means['transport_fraction']:.9f}`",
        "",
        "## Scouting heuristics",
        "",
    ]
    lines.extend(f"- {name}: `{str(value).lower()}`" for name, value in heuristics.items())
    lines.extend(["", "## Claim boundary", "", str(summary["claim_boundary"]), ""])
    return "\n".join(lines)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def git_metadata() -> dict[str, object]:
    root = HERE.parents[4]
    def command(*args: str) -> str:
        return subprocess.check_output(args, cwd=root, text=True).strip()
    return {
        "root": str(root),
        "head": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "remote": command("git", "remote", "get-url", "origin"),
        "dirty": bool(command("git", "status", "--porcelain")),
    }


def run(phase: str, out_dir: Path) -> None:
    if out_dir.exists():
        raise SystemExit(f"output directory exists: {out_dir}")
    seeds = DEVELOPMENT_SEEDS if phase == "development" else DISCOVERY_SEEDS
    out_dir.mkdir(parents=True)
    started = time.time()
    rows = [evaluate_seed(seed) for seed in seeds]
    summary = summarize(rows, phase)
    (out_dir / "raw_seed_results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "RESULT.md").write_text(render_report(summary), encoding="utf-8")
    metadata = {
        "experiment": "E015-X3",
        "phase": phase,
        "started_unix": started,
        "finished_unix": time.time(),
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "pid": os.getpid(),
        "git": git_metadata(),
        "source_sha256": {
            "run_e015_x3.py": sha256(HERE / "run_e015_x3.py"),
            "SCOUTING_PLAN.md": sha256(HERE / "SCOUTING_PLAN.md"),
        },
        "deviations": [],
    }
    (out_dir / "execution_log.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("development", "discovery"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(arguments.phase, arguments.out_dir)
