#!/usr/bin/env python3
"""Exploratory audit of an inclusion-exclusion relational synergy carrier."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from experiment_007_unity_pilot import (
    ARCHITECTURES, DUAL, INTERACTING, dual_masks, initialize_dual, load_e006,
    receiver_indices, rms, train_dual,
)


DEFAULT_REPO = Path(
    "/Users/satoru/Documents/Codex/2026-07-19/gitlab/"
    "Subjectivity-Intersection-Mathematics"
)
TRANSITIONS = (4, 5, 6)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(7100, 7108)))
    parser.add_argument("--steps", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--episodes", type=int, default=4096)
    parser.add_argument("--random-draws", type=int, default=32)
    return parser.parse_args()


def synergy(states):
    return states["ab"] - states["a0"] - states["0b"] + states["00"]


def at(trajectories, step):
    return {name: states[step] for name, states in trajectories.items()}


def next_synergy(natural_next, intervened_ab):
    states = dict(natural_next)
    states["ab"] = intervened_ab
    return synergy(states)


def random_receiver_matched(e006, architecture, component, rng):
    result = np.zeros_like(component)
    for indices in receiver_indices(e006, architecture):
        direction = rng.normal(size=(len(component), len(indices)))
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)
        norm = np.linalg.norm(component[:, indices], axis=1, keepdims=True)
        result[:, indices] = direction * norm
    return result


def percentile(value, null):
    null = np.asarray(null)
    return float((np.sum(null < value) + 0.5 * np.sum(null == value)) / len(null))


def probability_magnitude(e006, logits, reference):
    return float(np.mean(np.abs(e006.E009.softmax(logits) - e006.E009.softmax(reference))))


def bilateral(e006, logits, reference):
    response = np.abs(e006.E009.softmax(logits) - e006.E009.softmax(reference))
    return float(np.mean(np.all(np.sum(response, axis=2) > 1e-9, axis=1)))


def cross_pair_donor(pair):
    donor = np.arange(len(pair))
    unresolved = np.ones(len(pair), dtype=bool)
    base = np.arange(len(pair))
    for offset in range(1, len(pair)):
        candidate = np.roll(base, offset)
        use = unresolved & (pair[candidate] != pair)
        donor[use] = candidate[use]
        unresolved[use] = False
        if not unresolved.any():
            break
    if unresolved.any():
        raise AssertionError("donor construction failed")
    return donor


def audit_transition(e006, architecture, model, episodes, trajectories, transition, draws, seed):
    current = at(trajectories, transition)
    natural_next = at(trajectories, transition + 1)
    component = synergy(current)
    receiver_a, receiver_b = receiver_indices(e006, architecture)
    next_component = synergy(natural_next)
    x_step = episodes["x"][:, transition]
    removed_next_ab = e006.advance(model, current["ab"] - component, x_step)
    removed_next_component = next_synergy(natural_next, removed_next_ab)
    transported = next_component - removed_next_component
    reference_logits = e006.continue_from_step(
        model, natural_next["ab"], episodes["x"], transition + 1
    )
    removed_logits = e006.continue_from_step(
        model, removed_next_ab, episodes["x"], transition + 1
    )
    reference_loss = e006.P015.cross_entropy(reference_logits, episodes["y"])
    donor = cross_pair_donor(episodes["pair"])
    exchanged_ab = e006.advance(
        model, current["ab"] - component + component[donor], x_step
    )
    exchanged_logits = e006.continue_from_step(
        model, exchanged_ab, episodes["x"], transition + 1
    )
    transport_value = rms(transported)
    action_value = probability_magnitude(e006, removed_logits, reference_logits)
    rng = np.random.default_rng(seed)
    null_transport, null_action = [], []
    for _ in range(draws):
        random_component = random_receiver_matched(
            e006, architecture, component, rng
        )
        random_next_ab = e006.advance(
            model, current["ab"] - random_component, x_step
        )
        random_next_component = next_synergy(natural_next, random_next_ab)
        null_transport.append(rms(next_component - random_next_component))
        random_logits = e006.continue_from_step(
            model, random_next_ab, episodes["x"], transition + 1
        )
        null_action.append(probability_magnitude(e006, random_logits, reference_logits))
    return {
        "transition": f"{transition}_to_{transition + 1}",
        "component_norm": rms(component),
        "component_a_norm": rms(component[:, receiver_a]),
        "component_b_norm": rms(component[:, receiver_b]),
        "component_bilateral_support": float(np.mean(
            (np.linalg.norm(component[:, receiver_a], axis=1) > 1e-12)
            & (np.linalg.norm(component[:, receiver_b], axis=1) > 1e-12)
        )),
        "next_component_norm": rms(next_component),
        "transported_norm": transport_value,
        "transport_fraction": transport_value / max(rms(next_component), 1e-12),
        "transport_percentile": percentile(transport_value, null_transport),
        "probability_response": action_value,
        "probability_response_percentile": percentile(action_value, null_action),
        "erase_cross_entropy_increase": (
            e006.P015.cross_entropy(removed_logits, episodes["y"])-reference_loss
        ),
        "exchange_cross_entropy_increase": (
            e006.P015.cross_entropy(exchanged_logits, episodes["y"])-reference_loss
        ),
        "bilateral_fraction": bilateral(e006, removed_logits, reference_logits),
        "reconstruction_error": float(np.max(np.abs(
            (natural_next["ab"] - transported) - removed_next_ab
        ))),
    }


def median(rows, key):
    return float(np.median([float(row[key]) for row in rows]))


def main():
    args = parse_args()
    if args.out_dir.exists():
        raise SystemExit("output directory exists")
    e006 = load_e006(args.repo)
    profiles = e006.E009.pair_profiles()
    episodes = e006.P015.evaluation_episodes(61780001, args.episodes, profiles)
    performance_x, performance_y, _ = e006.P015.sample_batch(
        61780002, e006.E009.HELDOUT_PAIRS, args.episodes, profiles, noise=True
    )
    variants = e006.P014.baseline_variants(episodes, profiles)
    rows = []
    for seed in args.seeds:
        for ai, architecture in enumerate(ARCHITECTURES):
            print(f"training seed={seed} architecture={architecture}", flush=True)
            if architecture == DUAL:
                untrained = initialize_dual(e006, seed)
                model = train_dual(e006, seed, args.steps, args.batch_size, profiles)
            else:
                untrained = e006.P014.initialize(architecture, 1510000 + seed)
                model = e006.P015.train_model(
                    architecture, seed, args.steps, args.batch_size, 0.004, profiles
                )
            performance = e006.P015.evaluate(model, performance_x, performance_y)
            trajectories = {name: e006.E009.forward(model, x)[1] for name, x in variants.items()}
            untrained_trajectories = {
                name: e006.E009.forward(untrained, x)[1] for name, x in variants.items()
            }
            untrained_norm = median([
                {"v": rms(synergy(at(untrained_trajectories, t)))} for t in TRANSITIONS
            ], "v")
            for ti, transition in enumerate(TRANSITIONS):
                result = audit_transition(
                    e006, architecture, model, episodes, trajectories, transition,
                    args.random_draws, 61781000 + seed * 100 + ai * 10 + ti,
                )
                rows.append({
                    "seed": seed, "architecture": architecture,
                    "heldout_both_correct": performance["both_correct"],
                    "untrained_component_norm": untrained_norm,
                    **result,
                })
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["architecture"], row["seed"])].append(row)
    units = []
    for (architecture, seed), subset in sorted(grouped.items()):
        units.append({
            "architecture": architecture, "seed": seed,
            "heldout_both_correct": median(subset, "heldout_both_correct"),
            "component_norm": median(subset, "component_norm"),
            "untrained_component_norm": median(subset, "untrained_component_norm"),
            "trained_untrained_ratio": median(subset, "component_norm") / max(median(subset, "untrained_component_norm"), 1e-12),
            "transport_all_three": all(float(r["transport_percentile"]) >= .95 for r in subset),
            "action_two_of_three": sum(float(r["probability_response_percentile"]) >= .95 for r in subset) >= 2,
            "bilateral_fraction": median(subset, "bilateral_fraction"),
            "exchange_loss": median(subset, "exchange_cross_entropy_increase"),
            "transport_fraction": median(subset, "transport_fraction"),
        })
    inter = [u for u in units if u["architecture"] in INTERACTING]
    dual = [u for u in units if u["architecture"] == DUAL]
    checks = {
        "all_architectures_competent": all(
            median([u for u in units if u["architecture"] == a], "heldout_both_correct") >= .95
            for a in ARCHITECTURES
        ),
        "dual_component_zero": max(u["component_norm"] for u in dual) <= 1e-10,
        "interacting_component_nonzero_each_architecture": all(
            median([u for u in inter if u["architecture"] == a], "component_norm") > 1e-4
            for a in INTERACTING
        ),
        "transport_all_three_at_least_75_percent": sum(u["transport_all_three"] for u in inter) / len(inter) >= .75,
        "action_two_of_three_at_least_75_percent": sum(u["action_two_of_three"] for u in inter) / len(inter) >= .75,
        "bilateral_median_at_least_0_95": median(inter, "bilateral_fraction") >= .95,
        "positive_exchange_each_architecture": all(
            median([u for u in inter if u["architecture"] == a], "exchange_loss") > 0
            for a in INTERACTING
        ),
        "training_amplification": (
            median(inter, "trained_untrained_ratio") >= 1.5
            and sum(u["trained_untrained_ratio"] > 1 for u in inter) / len(inter) >= .75
        ),
    }
    passed = sum(checks.values())
    readout = (
        "STRONG_SYNERGY_CARRIER_SIGNAL" if passed == 8 else
        "PARTIAL_SYNERGY_CARRIER_SIGNAL" if passed >= 5 else
        "SYNERGY_CARRIER_NOT_ESTABLISHED"
    )
    summary = {
        "status": "EXPLORATORY_PILOT_COMPLETE", "readout": readout,
        "checks": checks, "passed_checks": passed,
        "configuration": {
            "seeds": args.seeds, "steps": args.steps, "batch_size": args.batch_size,
            "episodes": args.episodes, "random_draws": args.random_draws,
            "active_parameters_each": 486,
        },
        "interacting_medians": {
            key: median(inter, key) for key in (
                "heldout_both_correct", "component_norm", "untrained_component_norm",
                "trained_untrained_ratio", "bilateral_fraction", "exchange_loss",
                "transport_fraction",
            )
        },
        "counts": {
            "interacting_units": len(inter),
            "transport_all_three": sum(u["transport_all_three"] for u in inter),
            "action_two_of_three": sum(u["action_two_of_three"] for u in inter),
            "training_amplified": sum(u["trained_untrained_ratio"] > 1 for u in inter),
        },
        "dual": {
            "median_accuracy": median(dual, "heldout_both_correct"),
            "maximum_component_norm": max(u["component_norm"] for u in dual),
        },
        "by_architecture": {
            a: {
                key: median([u for u in units if u["architecture"] == a], key)
                for key in ("heldout_both_correct", "component_norm", "trained_untrained_ratio", "bilateral_fraction", "exchange_loss", "transport_fraction")
            } for a in ARCHITECTURES
        },
        "claim_boundary": "Exploratory operational synergy only; not O3 or subjectivity.",
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
