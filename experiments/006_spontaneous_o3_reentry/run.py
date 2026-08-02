#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 006 confirmatory spontaneous O3 re-entry audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing
import sys
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
E005_DIR = (
    REPOSITORY_ROOT
    / "experiments"
    / "005_emergent_relational_carrier_solution_class"
)
if str(E005_DIR) not in sys.path:
    sys.path.insert(0, str(E005_DIR))

from support import p015_reciprocal as P015  # noqa: E402

P014 = P015.P014
E010 = P015.E010
E009 = P015.E009

ARCHITECTURES = P015.ARCHITECTURES
INTERACTING_ARCHITECTURES = P015.INTERACTING_ARCHITECTURES
TRANSITIONS = (4, 5, 6)
SCHEMA = "siel-experiment-006-spontaneous-o3-reentry-v1"
DEVELOPMENT_SEEDS_EXCLUDED = tuple(range(300, 312))
CONFIRMATORY_SEEDS = tuple(range(2000, 2024))
REGISTRATION_CHECK_SEEDS = (1900,)
CONFIRMATORY_EVALUATION_SEEDS = (61630001, 61630002)
REGISTRATION_CHECK_EVALUATION_SEEDS = (61620001, 61620002)
STEPS = 4000
BATCH_SIZE = 256
LEARNING_RATE = 0.004
TEST_EPISODES = 4096
RANDOM_DRAWS = 64
TASK_COMPETENCE_THRESHOLD = 0.95
TOP_PERCENTILE = 0.95
MINIMUM_COMPETENT_SEEDS = 22
MINIMUM_SEED_PASSES_PER_ARCHITECTURE = 18
MINIMUM_POOLED_TRANSPORT_SEED_PASSES = 75
MINIMUM_TRANSPORT_FRACTION_MEDIAN = 0.75
MINIMUM_TRANSPORT_ALIGNMENT_MEDIAN = 0.60
MINIMUM_EXCHANGE_LOSS_MEDIAN = 0.25
MINIMUM_BILATERAL_MEDIAN = 0.95
MAXIMUM_INDEPENDENT_ACCURACY = 0.20
MAXIMUM_INDEPENDENT_COMPONENT = 1e-10
MAXIMUM_RECONSTRUCTION_ERROR = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("registration-check", "confirmatory"), required=True
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def advance(
    model: dict[str, Any], hidden: np.ndarray, input_step: np.ndarray
) -> np.ndarray:
    p = model["params"]
    return np.tanh(
        input_step @ p["inputs"].T
        + hidden @ p["recurrent"].T
        + p["bias"]
    )


def logits_from_hidden(model: dict[str, Any], hidden: np.ndarray) -> np.ndarray:
    p = model["params"]
    return (
        hidden @ p["outputs"].T + p["output_bias"]
    ).reshape(-1, 2, E009.CLASS_COUNT)


def continue_from_step(
    model: dict[str, Any],
    hidden: np.ndarray,
    x: np.ndarray,
    start_step: int,
) -> np.ndarray:
    current = hidden.copy()
    for position in range(start_step, E009.SEQUENCE_LENGTH):
        current = advance(model, current, x[:, position])
    return logits_from_hidden(model, current)


def directed_component_from_states(
    architecture: str, states: dict[str, np.ndarray]
) -> np.ndarray:
    return P014.directed_component(architecture, states)


def receiver_matched_direction(
    component: np.ndarray,
    architecture: str,
    rng: np.random.Generator,
) -> np.ndarray:
    randomized = np.zeros_like(component)
    for indices in P014.receiver_indices(architecture):
        direction = rng.normal(size=(component.shape[0], len(indices)))
        direction /= np.maximum(
            np.linalg.norm(direction, axis=1, keepdims=True), 1e-12
        )
        norm = np.linalg.norm(component[:, indices], axis=1, keepdims=True)
        randomized[:, indices] = direction * norm
    return randomized


def receiver_match_source_to_component(
    source: np.ndarray,
    component: np.ndarray,
    architecture: str,
) -> np.ndarray:
    matched = np.zeros_like(source)
    for indices in P014.receiver_indices(architecture):
        source_part = source[:, indices]
        source_norm = np.linalg.norm(source_part, axis=1, keepdims=True)
        target_norm = np.linalg.norm(component[:, indices], axis=1, keepdims=True)
        matched[:, indices] = (
            source_part
            / np.maximum(source_norm, 1e-12)
            * target_norm
        )
    return matched


def rms_norm(value: np.ndarray) -> float:
    return float(np.mean(
        np.linalg.norm(value, axis=1) / math.sqrt(value.shape[1])
    ))


def mean_cosine(left: np.ndarray, right: np.ndarray) -> float:
    numerator = np.sum(left * right, axis=1)
    denominator = (
        np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    )
    valid = denominator > 1e-12
    if not np.any(valid):
        return 0.0
    return float(np.mean(numerator[valid] / denominator[valid]))


def bilateral_fraction(
    logits: np.ndarray, reference: np.ndarray
) -> float:
    response = np.abs(E009.softmax(logits) - E009.softmax(reference))
    return float(np.mean(np.all(np.sum(response, axis=2) > 1e-9, axis=1)))


def mean_absolute_probability_response(
    logits: np.ndarray, reference: np.ndarray
) -> float:
    return float(np.mean(np.abs(E009.softmax(logits) - E009.softmax(reference))))


def relation_states_at(
    trajectories: dict[str, list[np.ndarray]], step: int
) -> dict[str, np.ndarray]:
    return {name: states[step] for name, states in trajectories.items()}


def next_component_after_ab_intervention(
    architecture: str,
    natural_next: dict[str, np.ndarray],
    intervened_ab_next: np.ndarray,
) -> np.ndarray:
    states = dict(natural_next)
    states["ab"] = intervened_ab_next
    return directed_component_from_states(architecture, states)


def audit_transition(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    trajectories: dict[str, list[np.ndarray]],
    transition: int,
    random_seed: int,
    random_draws: int,
) -> dict[str, Any]:
    current = relation_states_at(trajectories, transition)
    natural_next = relation_states_at(trajectories, transition + 1)
    component = directed_component_from_states(architecture, current)
    next_component = directed_component_from_states(architecture, natural_next)
    input_step = episodes["x"][:, transition]

    ab_without_relation = advance(
        model, current["ab"] - component, input_step
    )
    next_without_relation = next_component_after_ab_intervention(
        architecture, natural_next, ab_without_relation
    )
    transported = next_component - next_without_relation

    own_history = np.zeros_like(component)
    receiver_a, receiver_b = P014.receiver_indices(architecture)
    own_history[:, receiver_a] = (
        current["a0"][:, receiver_a] - current["00"][:, receiver_a]
    )
    own_history[:, receiver_b] = (
        current["0b"][:, receiver_b] - current["00"][:, receiver_b]
    )
    own_history = receiver_match_source_to_component(
        own_history, component, architecture
    )
    ab_without_own = advance(
        model, current["ab"] - own_history, input_step
    )
    next_without_own = next_component_after_ab_intervention(
        architecture, natural_next, ab_without_own
    )
    own_transport_effect = rms_norm(next_component - next_without_own)

    reference_logits = continue_from_step(
        model,
        natural_next["ab"],
        episodes["x"],
        transition + 1,
    )
    erased_logits = continue_from_step(
        model,
        ab_without_relation,
        episodes["x"],
        transition + 1,
    )
    own_erased_logits = continue_from_step(
        model,
        ab_without_own,
        episodes["x"],
        transition + 1,
    )
    donor = E010.cross_pair_donor(episodes["pair"])
    exchanged_hidden = (
        natural_next["ab"] - transported + transported[donor]
    )
    exchanged_logits = continue_from_step(
        model,
        exchanged_hidden,
        episodes["x"],
        transition + 1,
    )

    relation_transport = rms_norm(transported)
    reference_loss = P015.cross_entropy(reference_logits, episodes["y"])
    relation_action_loss = (
        P015.cross_entropy(erased_logits, episodes["y"]) - reference_loss
    )
    own_action_loss = (
        P015.cross_entropy(own_erased_logits, episodes["y"]) - reference_loss
    )
    exchange_action_loss = (
        P015.cross_entropy(exchanged_logits, episodes["y"]) - reference_loss
    )
    relation_action_magnitude = mean_absolute_probability_response(
        erased_logits, reference_logits
    )
    rng = np.random.default_rng(random_seed)
    random_transport: list[float] = []
    random_bilateral: list[float] = []
    random_action_losses: list[float] = []
    random_action_magnitudes: list[float] = []
    for _ in range(random_draws):
        random_component = receiver_matched_direction(
            component, architecture, rng
        )
        random_next_ab = advance(
            model, current["ab"] - random_component, input_step
        )
        random_next_component = next_component_after_ab_intervention(
            architecture, natural_next, random_next_ab
        )
        random_transport.append(rms_norm(
            next_component - random_next_component
        ))
        random_logits = continue_from_step(
            model,
            random_next_ab,
            episodes["x"],
            transition + 1,
        )
        random_bilateral.append(
            bilateral_fraction(random_logits, reference_logits)
        )
        random_action_losses.append(
            P015.cross_entropy(random_logits, episodes["y"]) - reference_loss
        )
        random_action_magnitudes.append(
            mean_absolute_probability_response(random_logits, reference_logits)
        )
    null = np.asarray(random_transport)
    action_null = np.asarray(random_action_losses)
    magnitude_null = np.asarray(random_action_magnitudes)
    percentile = float(
        (np.sum(null < relation_transport)
         + 0.5 * np.sum(null == relation_transport))
        / null.size
    ) if null.size else 0.0
    action_percentile = float(
        (np.sum(action_null < relation_action_loss)
         + 0.5 * np.sum(action_null == relation_action_loss))
        / action_null.size
    ) if action_null.size else 0.0
    magnitude_percentile = float(
        (np.sum(magnitude_null < relation_action_magnitude)
         + 0.5 * np.sum(magnitude_null == relation_action_magnitude))
        / magnitude_null.size
    ) if magnitude_null.size else 0.0

    next_norm = rms_norm(next_component)
    return {
        "transition": f"{transition}_to_{transition + 1}",
        "component_norm": rms_norm(component),
        "next_component_norm": next_norm,
        "transported_component_norm": relation_transport,
        "transport_fraction_of_next": (
            relation_transport / next_norm if next_norm > 1e-12 else 0.0
        ),
        "transport_alignment_with_next": mean_cosine(
            transported, next_component
        ),
        "random_transport_median": float(np.median(null)) if null.size else 0.0,
        "transport_selectivity_over_random": (
            relation_transport - float(np.median(null)) if null.size
            else relation_transport
        ),
        "transport_percentile": percentile,
        "matched_own_history_transport": own_transport_effect,
        "transport_selectivity_over_own_history": (
            relation_transport - own_transport_effect
        ),
        "erase_cross_entropy_increase": relation_action_loss,
        "random_action_loss_median": float(np.median(action_null)),
        "action_loss_selectivity_over_random": (
            relation_action_loss - float(np.median(action_null))
        ),
        "action_loss_percentile": action_percentile,
        "matched_own_history_action_loss": own_action_loss,
        "action_loss_selectivity_over_own_history": (
            relation_action_loss - own_action_loss
        ),
        "erase_probability_response": relation_action_magnitude,
        "random_probability_response_median": float(np.median(magnitude_null)),
        "probability_response_selectivity_over_random": (
            relation_action_magnitude - float(np.median(magnitude_null))
        ),
        "probability_response_percentile": magnitude_percentile,
        "exchange_cross_entropy_increase": exchange_action_loss,
        "erase_bilateral_fraction": bilateral_fraction(
            erased_logits, reference_logits
        ),
        "exchange_bilateral_fraction": bilateral_fraction(
            exchanged_logits, reference_logits
        ),
        "random_bilateral_median": float(np.median(random_bilateral)),
        "reentry_state_reconstruction_error": float(np.max(np.abs(
            (natural_next["ab"] - transported) - ab_without_relation
        ))),
    }


_CONTEXT: dict[str, Any] = {}


def run_seed(training_seed: int) -> list[dict[str, Any]]:
    args = _CONTEXT["args"]
    profiles = _CONTEXT["profiles"]
    episodes = _CONTEXT["episodes"]
    performance_x = _CONTEXT["performance_x"]
    performance_y = _CONTEXT["performance_y"]
    variants = P014.baseline_variants(episodes, profiles)
    rows: list[dict[str, Any]] = []

    for architecture_index, architecture in enumerate(ARCHITECTURES):
        model = P015.train_model(
            architecture,
            training_seed,
            args.steps,
            args.batch_size,
            args.learning_rate,
            profiles,
        )
        performance = P015.evaluate(model, performance_x, performance_y)
        trajectories = {
            name: E009.forward(model, x)[1]
            for name, x in variants.items()
        }
        for transition_index, transition in enumerate(TRANSITIONS):
            metrics = audit_transition(
                architecture,
                model,
                episodes,
                trajectories,
                transition,
                1660000
                + 10000 * training_seed
                + 100 * architecture_index
                + transition_index,
                args.random_draws,
            )
            rows.append({
                "training_seed": training_seed,
                "architecture": architecture,
                "heldout_both_correct": performance["both_correct"],
                "task_competent": (
                    performance["both_correct"] >= TASK_COMPETENCE_THRESHOLD
                ),
                **metrics,
            })
    return rows


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "minimum": float(np.min(values)),
        "median": float(np.median(values)),
        "maximum": float(np.max(values)),
    }


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


def verify_registration_manifest() -> dict[str, Any]:
    manifest_path = HERE / "registration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("source_sha256", {})
    if not expected:
        raise SystemExit("FAIL: registration manifest has no source hashes")
    observed: dict[str, str] = {}
    mismatches: list[str] = []
    for relative_path, expected_hash in sorted(expected.items()):
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file():
            mismatches.append(relative_path + ":missing")
            continue
        observed_hash = sha256_file(path)
        observed[relative_path] = observed_hash
        if observed_hash != expected_hash:
            mismatches.append(relative_path + ":hash")
    if mismatches:
        raise SystemExit(
            "FAIL: frozen registration source mismatch: " + ", ".join(mismatches)
        )
    return {
        "manifest": str(manifest_path.relative_to(REPOSITORY_ROOT)),
        "source_count": len(expected),
        "all_source_hashes_match": True,
        "observed_source_sha256": observed,
    }


def render_result(summary: dict[str, Any]) -> str:
    lines = [
        "# Experiment 006 Result",
        "",
        "## Spontaneous Operational O3 Re-entry",
        "",
        f"Status: {summary['status']}",
        f"Primary readout: {summary['primary_readout']}",
        "",
        "| Architecture | Competent | Transport all 3 | Action 2 of 3 | Own-history 2 of 3 |",
        "|---|---:|---:|---:|---:|",
    ]
    for architecture in INTERACTING_ARCHITECTURES:
        item = summary["architectures"][architecture]
        lines.append(
            f"| {architecture} | {item['competent_seed_count']} | "
            f"{item['transport_all_three_seed_count']} | "
            f"{item['action_two_of_three_seed_count']} | "
            f"{item['own_history_two_of_three_seed_count']} |"
        )
    lines.extend([
        "",
        "## Registered acceptance checks",
        "",
    ])
    for name, passed in summary["acceptance_checks"].items():
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        summary["claim_boundary"],
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    registration_verification = (
        verify_registration_manifest() if args.check else {
            "all_source_hashes_match": None,
            "check_requested": False,
        }
    )
    if args.out_dir.exists():
        raise SystemExit("FAIL: output directory exists")
    if args.workers < 1:
        raise SystemExit("FAIL: worker count must be positive")
    if args.mode == "confirmatory":
        training_seeds = CONFIRMATORY_SEEDS
        evaluation_seeds = CONFIRMATORY_EVALUATION_SEEDS
        args.steps = STEPS
        args.batch_size = BATCH_SIZE
        args.learning_rate = LEARNING_RATE
        args.test_episodes = TEST_EPISODES
        args.random_draws = RANDOM_DRAWS
    else:
        training_seeds = REGISTRATION_CHECK_SEEDS
        evaluation_seeds = REGISTRATION_CHECK_EVALUATION_SEEDS
        args.steps = 40
        args.batch_size = 32
        args.learning_rate = LEARNING_RATE
        args.test_episodes = 128
        args.random_draws = 4

    profiles = E009.pair_profiles()
    episodes = P015.evaluation_episodes(
        evaluation_seeds[0], args.test_episodes, profiles
    )
    performance_x, performance_y, _ = P015.sample_batch(
        evaluation_seeds[1],
        E009.HELDOUT_PAIRS,
        args.test_episodes,
        profiles,
        noise=True,
    )
    _CONTEXT.update({
        "args": args,
        "profiles": profiles,
        "episodes": episodes,
        "performance_x": performance_x,
        "performance_y": performance_y,
    })

    rows: list[dict[str, Any]] = []
    workers = min(args.workers, len(training_seeds))
    if workers > 1:
        with multiprocessing.get_context("fork").Pool(workers) as pool:
            for seed_rows in pool.imap(run_seed, training_seeds):
                rows.extend(seed_rows)
    else:
        for training_seed in training_seeds:
            rows.extend(run_seed(training_seed))

    args.out_dir.mkdir(parents=True)
    write_csv(args.out_dir / "transition_metrics.csv", rows)

    summary: dict[str, Any] = {
        "schema": SCHEMA,
        "status": (
            "CONFIRMATORY_COMPLETE"
            if args.mode == "confirmatory"
            else "REGISTRATION_CHECK_COMPLETE"
        ),
        "mode": args.mode,
        "task": "delayed reciprocal recall",
        "training_seeds": list(training_seeds),
        "development_training_seeds_excluded": list(DEVELOPMENT_SEEDS_EXCLUDED),
        "public_e005_confirmatory_seeds_reused": bool(
            set(training_seeds) & set(range(1000, 1024))
        ),
        "training": {
            "steps": args.steps,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
        },
        "evaluation": {
            "episodes": args.test_episodes,
            "random_draws": args.random_draws,
            "transitions": list(TRANSITIONS),
            "evaluation_seeds": list(evaluation_seeds),
        },
        "architectures": {},
        "registration_verification": registration_verification,
        "claim_boundary": (
            "A supported result establishes an operational spontaneous O3 re-entry "
            "solution class: a learned directed relation component is causally "
            "transported into later relation states and bilateral action without an "
            "explicit O3 state, target, or loss. It does not identify the learned "
            "state with ontological subjectivity or prove a unique physical mechanism."
        ),
    }
    fields = (
        "heldout_both_correct",
        "component_norm",
        "next_component_norm",
        "transported_component_norm",
        "transport_fraction_of_next",
        "transport_alignment_with_next",
        "random_transport_median",
        "transport_selectivity_over_random",
        "transport_percentile",
        "matched_own_history_transport",
        "transport_selectivity_over_own_history",
        "erase_cross_entropy_increase",
        "random_action_loss_median",
        "action_loss_selectivity_over_random",
        "action_loss_percentile",
        "matched_own_history_action_loss",
        "action_loss_selectivity_over_own_history",
        "erase_probability_response",
        "random_probability_response_median",
        "probability_response_selectivity_over_random",
        "probability_response_percentile",
        "exchange_cross_entropy_increase",
        "erase_bilateral_fraction",
        "exchange_bilateral_fraction",
        "random_bilateral_median",
        "reentry_state_reconstruction_error",
    )
    for architecture in ARCHITECTURES:
        selected = [row for row in rows if row["architecture"] == architecture]
        item = {
            field: summarize([float(row[field]) for row in selected])
            for field in fields
        }
        item["competent_seed_count"] = len({
            int(row["training_seed"])
            for row in selected if row["task_competent"]
        })
        item["top_0_95_transition_count"] = sum(
            float(row["transport_percentile"]) >= 0.95
            for row in selected if row["task_competent"]
        )
        item["positive_over_own_count"] = sum(
            float(row["transport_selectivity_over_own_history"]) > 0.0
            for row in selected if row["task_competent"]
        )
        item["top_0_95_action_loss_count"] = sum(
            float(row["action_loss_percentile"]) >= 0.95
            for row in selected if row["task_competent"]
        )
        item["top_0_95_action_magnitude_count"] = sum(
            float(row["probability_response_percentile"]) >= 0.95
            for row in selected if row["task_competent"]
        )
        item["positive_action_over_own_count"] = sum(
            float(row["action_loss_selectivity_over_own_history"]) > 0.0
            for row in selected if row["task_competent"]
        )
        seed_rows: dict[int, list[dict[str, Any]]] = {}
        for row in selected:
            if row["task_competent"]:
                seed_rows.setdefault(int(row["training_seed"]), []).append(row)
        item["transport_all_three_seed_count"] = sum(
            len(seed_values) == len(TRANSITIONS)
            and all(
                float(row["transport_percentile"]) >= TOP_PERCENTILE
                for row in seed_values
            )
            for seed_values in seed_rows.values()
        )
        item["action_two_of_three_seed_count"] = sum(
            sum(
                float(row["action_loss_percentile"]) >= TOP_PERCENTILE
                for row in seed_values
            ) >= 2
            for seed_values in seed_rows.values()
        )
        item["action_magnitude_two_of_three_seed_count"] = sum(
            sum(
                float(row["probability_response_percentile"]) >= TOP_PERCENTILE
                for row in seed_values
            ) >= 2
            for seed_values in seed_rows.values()
        )
        item["own_history_two_of_three_seed_count"] = sum(
            sum(
                float(row["transport_selectivity_over_own_history"]) > 0.0
                for row in seed_values
            ) >= 2
            for seed_values in seed_rows.values()
        )
        summary["architectures"][architecture] = item

    interacting = {
        name: summary["architectures"][name]
        for name in INTERACTING_ARCHITECTURES
    }
    pooled_transport_seed_passes = sum(
        item["transport_all_three_seed_count"] for item in interacting.values()
    )
    checks = {
        "capacity_exact_486": {
            P014.active_parameter_count(name) for name in ARCHITECTURES
        } == {486},
        "competence_at_least_22_of_24_each_interacting_architecture": all(
            item["competent_seed_count"] >= MINIMUM_COMPETENT_SEEDS
            for item in interacting.values()
        ),
        "transport_all_three_at_least_18_of_24_each_architecture": all(
            item["transport_all_three_seed_count"]
            >= MINIMUM_SEED_PASSES_PER_ARCHITECTURE
            for item in interacting.values()
        ),
        "pooled_transport_seed_passes_at_least_75_of_96": (
            pooled_transport_seed_passes >= MINIMUM_POOLED_TRANSPORT_SEED_PASSES
        ),
        "action_loss_two_of_three_at_least_18_of_24_each_architecture": all(
            item["action_two_of_three_seed_count"]
            >= MINIMUM_SEED_PASSES_PER_ARCHITECTURE
            for item in interacting.values()
        ),
        "action_magnitude_two_of_three_at_least_18_of_24_each_architecture": all(
            item["action_magnitude_two_of_three_seed_count"]
            >= MINIMUM_SEED_PASSES_PER_ARCHITECTURE
            for item in interacting.values()
        ),
        "relation_over_own_history_two_of_three_at_least_18_of_24_each": all(
            item["own_history_two_of_three_seed_count"]
            >= MINIMUM_SEED_PASSES_PER_ARCHITECTURE
            for item in interacting.values()
        ),
        "median_transport_fraction_at_least_0_75_each_architecture": all(
            item["transport_fraction_of_next"]["median"]
            >= MINIMUM_TRANSPORT_FRACTION_MEDIAN
            for item in interacting.values()
        ),
        "median_transport_alignment_at_least_0_60_each_architecture": all(
            item["transport_alignment_with_next"]["median"]
            >= MINIMUM_TRANSPORT_ALIGNMENT_MEDIAN
            for item in interacting.values()
        ),
        "median_exchange_loss_at_least_0_25_each_architecture": all(
            item["exchange_cross_entropy_increase"]["median"]
            >= MINIMUM_EXCHANGE_LOSS_MEDIAN
            for item in interacting.values()
        ),
        "median_bilateral_erasure_at_least_0_95_each_architecture": all(
            item["erase_bilateral_fraction"]["median"]
            >= MINIMUM_BILATERAL_MEDIAN
            for item in interacting.values()
        ),
        "independent_accuracy_at_most_0_20": (
            summary["architectures"]["independent"]
            ["heldout_both_correct"]["maximum"]
            <= MAXIMUM_INDEPENDENT_ACCURACY
        ),
        "independent_component_zero": (
            summary["architectures"]["independent"]
            ["component_norm"]["maximum"]
            <= MAXIMUM_INDEPENDENT_COMPONENT
        ),
        "reentry_reconstruction_error_at_most_1e_12": all(
            item["reentry_state_reconstruction_error"]["maximum"]
            <= MAXIMUM_RECONSTRUCTION_ERROR
            for item in summary["architectures"].values()
        ),
    }
    readout = (
        "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    ) if args.mode == "confirmatory" else "NOT_APPLICABLE"
    summary["pooled_transport_seed_passes"] = pooled_transport_seed_passes
    summary["acceptance_checks"] = checks
    summary["primary_readout"] = readout

    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "RESULT.md").write_text(
        render_result(summary), encoding="utf-8"
    )
    output_manifest = {
        "schema": "siel-experiment-006-output-manifest-v1",
        "mode": args.mode,
        "files_sha256": {
            path.name: sha256_file(path)
            for path in sorted(args.out_dir.iterdir())
            if path.name != "output_manifest.json"
        },
    }
    (args.out_dir / "output_manifest.json").write_text(
        json.dumps(output_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": summary["status"],
        "primary_readout": readout,
        "pooled_transport_seed_passes": pooled_transport_seed_passes,
        "acceptance_checks": checks,
        "architectures": {
            name: {
                "competent_seed_count": item["competent_seed_count"],
                "transport_all_three_seed_count": item["transport_all_three_seed_count"],
                "action_two_of_three_seed_count": item["action_two_of_three_seed_count"],
                "own_history_two_of_three_seed_count": item["own_history_two_of_three_seed_count"],
            }
            for name, item in interacting.items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
