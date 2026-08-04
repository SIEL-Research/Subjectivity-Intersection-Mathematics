#!/usr/bin/env python3
"""Exploratory Experiment 007 pilot: distributed unity vs two directed traces."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_REPO = Path(
    "/Users/satoru/Documents/Codex/2026-07-19/gitlab/"
    "Subjectivity-Intersection-Mathematics"
)
DUAL = "dual_independent_relay"
INTERACTING = (
    "distributed", "central_shared", "directional_relay",
    "four_channel_crossbar",
)
ARCHITECTURES = (*INTERACTING, DUAL)
TRANSITIONS = (4, 5, 6)


def load_e006(repo: Path):
    source = repo / "experiments/006_spontaneous_o3_reentry/run.py"
    spec = importlib.util.spec_from_file_location("e007_pilot_e006", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(7000, 7008)))
    parser.add_argument("--steps", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--episodes", type=int, default=4096)
    parser.add_argument("--random-draws", type=int, default=32)
    parser.add_argument("--matched-draws", type=int, default=4)
    return parser.parse_args()


def dual_masks(e006):
    d, inp, out = e006.E009.STATE_DIM, e006.E009.INPUT_DIM, e006.E009.OUTPUT_DIM
    recurrent = np.zeros((d, d))
    inputs = np.zeros((d, inp))
    outputs = np.zeros((out, d))
    # 0:12 is B -> A. 12:24 is A -> B. No path joins the blocks.
    recurrent[:12, :12] = 1.0
    recurrent[12:, 12:] = 1.0
    inputs[:12, 4:] = 1.0
    inputs[12:, :4] = 1.0
    outputs[:3, :12] = 1.0
    outputs[3:, 12:] = 1.0
    assert int(recurrent.sum()) == 288
    assert int(inputs.sum()) == 96
    assert int(outputs.sum()) == 72
    return {"recurrent": recurrent, "inputs": inputs, "outputs": outputs}


def initialize_dual(e006, seed: int):
    masks = dual_masks(e006)
    rng = np.random.default_rng(1510000 + seed)
    params = {
        "recurrent": rng.normal(scale=0.18, size=(24, 24)) * masks["recurrent"],
        "inputs": rng.normal(scale=0.24, size=(24, 8)) * masks["inputs"],
        "bias": np.zeros(24),
        "outputs": rng.normal(scale=0.16, size=(6, 24)) * masks["outputs"],
        "output_bias": np.zeros(6),
    }
    return {"name": DUAL, "masks": masks, "params": params}


def train_dual(e006, seed, steps, batch_size, profiles):
    model = initialize_dual(e006, seed)
    square_average = {key: np.zeros_like(value) for key, value in model["params"].items()}
    for step in range(1, steps + 1):
        x, y, _ = e006.P015.sample_batch(
            1520000 + 100000 * seed + step,
            e006.E009.TRAIN_PAIRS, batch_size, profiles, noise=True,
        )
        _, grads = e006.P015.loss_and_grad(model, x, y)
        total_norm = math.sqrt(sum(float(np.sum(g * g)) for g in grads.values()))
        scale = min(1.0, 5.0 / (total_norm + 1e-12))
        for key, gradient in grads.items():
            gradient = gradient * scale
            square_average[key] = 0.99 * square_average[key] + 0.01 * gradient * gradient
            model["params"][key] -= 0.004 * gradient / (np.sqrt(square_average[key]) + 1e-8)
        for key in ("inputs", "recurrent", "outputs"):
            model["params"][key] *= model["masks"][key]
    return model


def receiver_indices(e006, architecture):
    if architecture == DUAL:
        return np.arange(12), np.arange(12, 24)
    return e006.P014.receiver_indices(architecture)


def component_from_states(e006, architecture, states):
    ia, ib = receiver_indices(e006, architecture)
    component = np.zeros_like(states["ab"])
    component[:, ia] = states["ab"][:, ia] - states["a0"][:, ia]
    component[:, ib] = states["ab"][:, ib] - states["0b"][:, ib]
    return component


def relation_states(trajectories, step):
    return {name: states[step] for name, states in trajectories.items()}


def next_component(e006, architecture, natural_next, intervened_ab):
    states = dict(natural_next)
    states["ab"] = intervened_ab
    return component_from_states(e006, architecture, states)


def split_component(e006, architecture, component):
    ia, ib = receiver_indices(e006, architecture)
    ca = np.zeros_like(component)
    cb = np.zeros_like(component)
    ca[:, ia] = component[:, ia]
    cb[:, ib] = component[:, ib]
    return ca, cb


def rms(value):
    return float(np.mean(np.linalg.norm(value, axis=1) / math.sqrt(value.shape[1])))


def conditioned_donors(pair, y):
    n = len(pair)
    first, second = np.arange(n), np.arange(n)
    valid = np.zeros(n, dtype=bool)
    base = np.arange(n)
    for i in range(n):
        candidates = base[(pair != pair[i]) & np.all(y == y[i], axis=1)]
        if len(candidates):
            d1 = candidates[0]
            other = candidates[pair[candidates] != pair[d1]]
            if len(other):
                first[i], second[i], valid[i] = d1, other[0], True
    if not np.all(valid):
        raise AssertionError("answer-matched three-pair donor construction failed")
    return first, second


def ridge_mse(x_train, y_train, x_test, y_test, alpha=1e-3):
    mean = x_train.mean(axis=0, keepdims=True)
    scale = x_train.std(axis=0, keepdims=True)
    scale[scale < 1e-9] = 1.0
    xt = (x_train - mean) / scale
    xv = (x_test - mean) / scale
    xt = np.column_stack((np.ones(len(xt)), xt))
    xv = np.column_stack((np.ones(len(xv)), xv))
    penalty = np.eye(xt.shape[1]) * alpha
    penalty[0, 0] = 0.0
    weights = np.linalg.solve(xt.T @ xt + penalty, xt.T @ y_train)
    prediction = xv @ weights
    return float(np.mean((prediction - y_test) ** 2))


def prediction_gains(e006, architecture, current_ab, next_relation, seed):
    ia, ib = receiver_indices(e006, architecture)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(current_ab))
    train, test = order[: len(order) // 2], order[len(order) // 2 :]
    gains = []
    for own, target in ((ia, ia), (ib, ib)):
        sep = ridge_mse(
            current_ab[train][:, own], next_relation[train][:, target],
            current_ab[test][:, own], next_relation[test][:, target],
        )
        joint = ridge_mse(
            current_ab[train], next_relation[train][:, target],
            current_ab[test], next_relation[test][:, target],
        )
        gains.append((sep - joint) / max(sep, 1e-12))
    return gains


def jacobian_matched_percentile(e006, architecture, model, natural_next_ab, component_half, source_indices, target_indices, rng, draws, closest):
    recurrent = model["params"]["recurrent"]
    derivative = 1.0 - natural_next_ab * natural_next_ab
    actual_linear = (component_half @ recurrent.T) * derivative
    actual_same = np.linalg.norm(actual_linear[:, source_indices], axis=1)
    actual_cross = np.linalg.norm(actual_linear[:, target_indices], axis=1)
    n, width = component_half.shape[0], len(source_indices)
    direction = rng.normal(size=(draws, n, width))
    direction /= np.maximum(np.linalg.norm(direction, axis=2, keepdims=True), 1e-12)
    target_norm = np.linalg.norm(component_half[:, source_indices], axis=1)
    direction *= target_norm[None, :, None]
    full = np.zeros((draws, n, 24))
    full[:, :, source_indices] = direction
    linear = np.einsum("kni,ji->knj", full, recurrent) * derivative[None, :, :]
    same = np.linalg.norm(linear[:, :, source_indices], axis=2)
    cross = np.linalg.norm(linear[:, :, target_indices], axis=2)
    distance = np.abs(np.log((same + 1e-12) / (actual_same[None, :] + 1e-12)))
    selected = np.argpartition(distance, kth=closest - 1, axis=0)[:closest]
    episode = np.arange(n)[None, :]
    matched_cross = cross[selected, episode]
    return float(np.mean(np.mean(actual_cross[None, :] > matched_cross, axis=0)))


def audit_transition(e006, architecture, model, episodes, trajectories, transition, random_draws, matched_draws, seed):
    current = relation_states(trajectories, transition)
    natural_next = relation_states(trajectories, transition + 1)
    component = component_from_states(e006, architecture, current)
    relation_next = component_from_states(e006, architecture, natural_next)
    ca, cb = split_component(e006, architecture, component)
    ia, ib = receiver_indices(e006, architecture)
    x_step = episodes["x"][:, transition]
    ab_a = e006.advance(model, current["ab"] - ca, x_step)
    ab_b = e006.advance(model, current["ab"] - cb, x_step)
    ab_both = e006.advance(model, current["ab"] - component, x_step)
    miss_a = relation_next - next_component(e006, architecture, natural_next, ab_a)
    miss_b = relation_next - next_component(e006, architecture, natural_next, ab_b)
    miss_both = relation_next - next_component(e006, architecture, natural_next, ab_both)
    factorial = miss_both - miss_a - miss_b

    donor1, donor2 = conditioned_donors(episodes["pair"], episodes["y"])
    coherent_state = current["ab"] - component + ca[donor1] + cb[donor1]
    chimera_state = current["ab"] - component + ca[donor1] + cb[donor2]
    coherent_next = e006.advance(model, coherent_state, x_step)
    chimera_next = e006.advance(model, chimera_state, x_step)
    coherent_relation = next_component(e006, architecture, natural_next, coherent_next)
    chimera_relation = next_component(e006, architecture, natural_next, chimera_next)
    coherent_change = rms(relation_next - coherent_relation)
    chimera_change = rms(relation_next - chimera_relation)
    coherent_logits = e006.continue_from_step(
        model, coherent_next, episodes["x"], transition + 1
    )
    chimera_logits = e006.continue_from_step(
        model, chimera_next, episodes["x"], transition + 1
    )
    gain_a, gain_b = prediction_gains(
        e006, architecture, current["ab"], relation_next, seed + 1
    )
    rng = np.random.default_rng(seed + 2)
    pct_a = jacobian_matched_percentile(
        e006, architecture, model, natural_next["ab"], ca, ia, ib,
        rng, random_draws, matched_draws,
    )
    pct_b = jacobian_matched_percentile(
        e006, architecture, model, natural_next["ab"], cb, ib, ia,
        rng, random_draws, matched_draws,
    )
    return {
        "transition": f"{transition}_to_{transition + 1}",
        "component_norm": rms(component),
        "a_to_next_b": rms(miss_a[:, ib]),
        "b_to_next_a": rms(miss_b[:, ia]),
        "factorial_fraction": rms(factorial) / max(rms(miss_both), 1e-12),
        "coherent_relation_change": coherent_change,
        "chimera_relation_change": chimera_change,
        "coherent_relation_advantage": chimera_change - coherent_change,
        "coherent_relation_advantage_fraction": (
            (chimera_change - coherent_change) / max(chimera_change, 1e-12)
        ),
        "coherent_cross_entropy": e006.P015.cross_entropy(coherent_logits, episodes["y"]),
        "chimera_cross_entropy": e006.P015.cross_entropy(chimera_logits, episodes["y"]),
        "coherent_task_advantage": (
            e006.P015.cross_entropy(chimera_logits, episodes["y"])
            - e006.P015.cross_entropy(coherent_logits, episodes["y"])
        ),
        "joint_prediction_gain_a": gain_a,
        "joint_prediction_gain_b": gain_b,
        "jacobian_matched_cross_percentile_a": pct_a,
        "jacobian_matched_cross_percentile_b": pct_b,
    }


def median(rows, key):
    return float(np.median([float(row[key]) for row in rows]))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    args = parse_args()
    if args.out_dir.exists():
        raise SystemExit("output directory exists")
    e006 = load_e006(args.repo)
    profiles = e006.E009.pair_profiles()
    episodes = e006.P015.evaluation_episodes(61770001, args.episodes, profiles)
    performance_x, performance_y, _ = e006.P015.sample_batch(
        61770002, e006.E009.HELDOUT_PAIRS, args.episodes, profiles, noise=True
    )
    variants = e006.P014.baseline_variants(episodes, profiles)
    rows = []
    for seed in args.seeds:
        for ai, architecture in enumerate(ARCHITECTURES):
            print(f"training seed={seed} architecture={architecture}", flush=True)
            if architecture == DUAL:
                model = train_dual(e006, seed, args.steps, args.batch_size, profiles)
            else:
                model = e006.P015.train_model(
                    architecture, seed, args.steps, args.batch_size, 0.004, profiles
                )
            performance = e006.P015.evaluate(model, performance_x, performance_y)
            trajectories = {
                name: e006.E009.forward(model, value)[1]
                for name, value in variants.items()
            }
            for ti, transition in enumerate(TRANSITIONS):
                result = audit_transition(
                    e006, architecture, model, episodes, trajectories, transition,
                    args.random_draws, args.matched_draws,
                    61771000 + seed * 100 + ai * 10 + ti,
                )
                rows.append({
                    "seed": seed,
                    "architecture": architecture,
                    "heldout_both_correct": performance["both_correct"],
                    **result,
                })

    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["architecture"], row["seed"])].append(row)
    seed_units = [{
        "architecture": architecture,
        "seed": seed,
        **{key: median(subset, key) for key in (
            "heldout_both_correct", "coherent_relation_advantage_fraction",
            "joint_prediction_gain_a", "joint_prediction_gain_b",
            "jacobian_matched_cross_percentile_a",
            "jacobian_matched_cross_percentile_b", "factorial_fraction",
        )},
    } for (architecture, seed), subset in sorted(grouped.items())]
    interacting = [row for row in seed_units if row["architecture"] in INTERACTING]
    dual = [row for row in seed_units if row["architecture"] == DUAL]
    competent = all(
        median([r for r in seed_units if r["architecture"] == architecture], "heldout_both_correct") >= 0.95
        for architecture in ARCHITECTURES
    )
    interacting_coherent_median = median(interacting, "coherent_relation_advantage_fraction")
    checks = {
        "all_architectures_competent": competent,
        "coherent_binding": (
            interacting_coherent_median >= 0.05
            and sum(r["coherent_relation_advantage_fraction"] > 0 for r in interacting)
            / len(interacting) >= 0.75
        ),
        "joint_prediction_both_directions": (
            median(interacting, "joint_prediction_gain_a") >= 0.05
            and median(interacting, "joint_prediction_gain_b") >= 0.05
        ),
        "jacobian_matched_cross_both_directions": (
            median(interacting, "jacobian_matched_cross_percentile_a") >= 0.95
            and median(interacting, "jacobian_matched_cross_percentile_b") >= 0.95
        ),
        "dual_joint_prediction_absent": (
            median(dual, "joint_prediction_gain_a") <= 0.01
            and median(dual, "joint_prediction_gain_b") <= 0.01
        ),
        "dual_coherent_binding_at_most_half": (
            median(dual, "coherent_relation_advantage_fraction")
            <= 0.5 * interacting_coherent_median
        ),
    }
    unity_passes = sum(checks[name] for name in checks if name != "all_architectures_competent")
    if checks["all_architectures_competent"] and unity_passes == 5:
        readout = "STRONG_UNITY_SIGNAL"
    elif checks["all_architectures_competent"] and unity_passes >= 3:
        readout = "PARTIAL_UNITY_SIGNAL"
    else:
        readout = "NOT_DISTINGUISHED_FROM_TWO_DIRECTED_TRACES"
    summary = {
        "status": "EXPLORATORY_PILOT_COMPLETE",
        "readout": readout,
        "checks": checks,
        "configuration": {
            "seeds": args.seeds, "steps": args.steps,
            "batch_size": args.batch_size, "episodes": args.episodes,
            "random_draws": args.random_draws,
            "matched_draws": args.matched_draws,
            "architectures": ARCHITECTURES,
            "active_parameters_each": 486,
        },
        "interacting_seed_units": len(interacting),
        "dual_seed_units": len(dual),
        "interacting_medians": {
            key: median(interacting, key) for key in seed_units[0]
            if key not in ("architecture", "seed")
        },
        "dual_medians": {
            key: median(dual, key) for key in seed_units[0]
            if key not in ("architecture", "seed")
        },
        "by_architecture": {
            architecture: {
                key: median(
                    [r for r in seed_units if r["architecture"] == architecture], key
                )
                for key in seed_units[0] if key not in ("architecture", "seed")
            }
            for architecture in ARCHITECTURES
        },
        "source_hashes": {
            "protocol": sha256(Path(__file__).with_name("EXPERIMENT_007_PILOT_PROTOCOL.md")),
            "runner": sha256(Path(__file__)),
        },
        "claim_boundary": (
            "This post-005 exploratory pilot can identify evidence for functional "
            "distributed unity, but cannot establish ontological unity or subjectivity."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
