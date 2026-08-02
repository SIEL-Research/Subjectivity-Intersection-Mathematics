#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 005 confirmatory emergent relational-carrier audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
from typing import Any

import numpy as np


from support import p015_reciprocal as P015
P014 = P015.P014
E012 = P015.E012
E010 = P015.E010
E009 = P015.E009

ARCHITECTURES = P015.ARCHITECTURES
INTERACTING_ARCHITECTURES = P015.INTERACTING_ARCHITECTURES
NEW_ARCHITECTURE = P015.NEW_ARCHITECTURE

SCHEMA = "siel-experiment-005-emergent-relational-carrier-v1"
CONFIRMATORY_SEEDS = tuple(range(1000, 1024))
REGISTRATION_CHECK_SEEDS = (900,)
CONFIRMATORY_EVALUATION_SEEDS = (51630001, 51630002)
REGISTRATION_CHECK_EVALUATION_SEEDS = (41630001, 41630002)
STEPS = 4000
BATCH_SIZE = 256
LEARNING_RATE = 0.004
TEST_EPISODES = 4096
DELETION_RANDOM_DRAWS = 64
CONTEXT_RANDOM_DRAWS = 8
TASK_COMPETENCE_THRESHOLD = 0.95
MINIMUM_COMPETENT_SEEDS = 22
MINIMUM_TOP_095_PER_PASSING_ARCHITECTURE = 14
MINIMUM_PASSING_ARCHITECTURES = 3
MINIMUM_POOLED_TOP_095 = 60
MINIMUM_POSITIVE_SELECTIVITY_PER_PASSING_ARCHITECTURE = 14
MINIMUM_MEDIAN_BILATERAL = 0.95
MINIMUM_RUN_BILATERAL = 0.90
MINIMUM_BILATERAL_RUNS = 22
RANK_NULL_PROBABILITY = 4.0 / 65.0
PER_ARCHITECTURE_ALPHA = 0.0125
MINIMUM_CONTEXT_CKA = 0.35
MINIMUM_CONTEXT_SPECIFICITY = 0.15
HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("registration-check", "confirmatory"), required=True
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def binomial_upper_tail(n: int, k: int, probability: float) -> float:
    return float(sum(
        math.comb(n, value)
        * probability ** value
        * (1.0 - probability) ** (n - value)
        for value in range(k, n + 1)
    ))


def matched_random_component(
    component: np.ndarray,
    architecture: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Randomize direction while preserving each receiver norm per episode."""
    randomized = np.zeros_like(component)
    for indices in P014.receiver_indices(architecture):
        direction = rng.normal(size=(component.shape[0], len(indices)))
        direction /= np.maximum(
            np.linalg.norm(direction, axis=1, keepdims=True), 1e-12
        )
        norm = np.linalg.norm(component[:, indices], axis=1, keepdims=True)
        randomized[:, indices] = direction * norm
    return randomized


def prepare_relation(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    profiles: dict[str, np.ndarray],
) -> dict[str, Any]:
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
    relation_logits, relation_responses = P014.response_for_components(
        model,
        episodes,
        normal_logits,
        states["ab"],
        component,
        donor,
        reverse_component,
    )
    return {
        "states": states,
        "component": component,
        "reverse_component": reverse_component,
        "donor": donor,
        "normal_logits": normal_logits,
        "relation_logits": relation_logits,
        "relation_responses": relation_responses,
    }


def audit(
    architecture: str,
    model: dict[str, Any],
    episodes: dict[str, np.ndarray],
    profiles: dict[str, np.ndarray],
    random_seed: int,
    deletion_draws: int,
    context_draws: int,
) -> tuple[dict[str, float], dict[str, np.ndarray], list[dict[str, np.ndarray]]]:
    prepared = prepare_relation(architecture, model, episodes, profiles)
    component = prepared["component"]
    normal_logits = prepared["normal_logits"]
    normal_loss = P015.cross_entropy(normal_logits, episodes["y"])
    relation_delete_increase = (
        P015.cross_entropy(prepared["relation_logits"]["delete"], episodes["y"])
        - normal_loss
    )
    bilateral = {
        operator: float(np.mean(np.all(
            np.sum(np.abs(response), axis=2) > 1e-9, axis=1
        )))
        for operator, response in prepared["relation_responses"].items()
    }

    rng = np.random.default_rng(random_seed)
    random_delete_increases: list[float] = []
    random_contexts: list[dict[str, np.ndarray]] = []
    for draw in range(deletion_draws):
        random_component = matched_random_component(component, architecture, rng)
        deleted_state = prepared["states"]["ab"] - random_component
        deleted_logits = E010.continue_from(model, deleted_state, episodes["x"])
        random_delete_increases.append(
            P015.cross_entropy(deleted_logits, episodes["y"]) - normal_loss
        )
        if draw < context_draws:
            random_reverse = matched_random_component(
                prepared["reverse_component"], architecture, rng
            )
            _, fields = P014.response_for_components(
                model,
                episodes,
                normal_logits,
                prepared["states"]["ab"],
                random_component,
                prepared["donor"],
                random_reverse,
            )
            random_contexts.append(fields)

    null = np.asarray(random_delete_increases)
    percentile = float(
        (np.sum(null < relation_delete_increase)
         + 0.5 * np.sum(null == relation_delete_increase)) / null.size
    )
    empirical_p = float((1 + np.sum(null >= relation_delete_increase)) / (1 + null.size))
    metrics = {
        "component_norm": float(np.mean(
            np.linalg.norm(component, axis=1) / math.sqrt(component.shape[1])
        )),
        "normal_cross_entropy": normal_loss,
        "normal_both_correct": P015.both_correct(normal_logits, episodes["y"]),
        "delete_cross_entropy_increase": relation_delete_increase,
        "random_delete_cross_entropy_increase_median": float(np.median(null)),
        "delete_selectivity": relation_delete_increase - float(np.median(null)),
        "delete_empirical_percentile": percentile,
        "delete_empirical_p": empirical_p,
        "bilateral_response_minimum": min(bilateral.values()),
    }
    return metrics, prepared["relation_responses"], random_contexts


def summarize(values: list[float]) -> dict[str, float]:
    return E012.summarize(values)


def summarize_or_empty(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"minimum": None, "median": None, "maximum": None}
    return summarize(values)


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    if fieldnames is None:
        if not rows:
            raise ValueError("fieldnames are required for an empty CSV")
        fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_registration_manifest() -> dict[str, Any]:
    """Refuse execution when any frozen preregistration source has changed."""
    manifest_path = HERE / "registration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("source_sha256", {})
    if not expected:
        raise SystemExit("FAIL: registration manifest has no source hashes")
    observed: dict[str, str] = {}
    mismatches: list[str] = []
    for relative_path, expected_hash in sorted(expected.items()):
        source_path = REPOSITORY_ROOT / relative_path
        if not source_path.is_file():
            mismatches.append(relative_path + ":missing")
            continue
        observed_hash = sha256_file(source_path)
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
        "# Experiment 005 Result",
        "",
        "## Emergent Relational-Carrier Solution Class",
        "",
        f"Status: {summary['status']}",
        f"Primary readout: {summary['primary_readout']}",
        "",
        "## Architecture-level rank results",
        "",
        "| Architecture | Competent | Top-0.95 | Positive selectivity | Exact p |",
        "|---|---:|---:|---:|---:|",
    ]
    for architecture, item in summary["architecture_rank_tests"].items():
        lines.append(
            f"| {architecture} | {item['competent_seed_count']} | "
            f"{item['top_0_95_seed_count']} | "
            f"{item['positive_selectivity_count']} | "
            f"{item['exact_one_sided_binomial_p']:.6g} |"
        )
    lines.extend([
        "",
        f"Pooled top-0.95 count: {summary['pooled_top_0_95_count']}",
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


_WORKER_CONTEXT: dict[str, Any] = {}


def run_training_seed(
    training_seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run one independent seed using the process-local inherited context."""
    args = _WORKER_CONTEXT["args"]
    profiles = _WORKER_CONTEXT["profiles"]
    episodes = _WORKER_CONTEXT["episodes"]
    performance_x = _WORKER_CONTEXT["performance_x"]
    performance_y = _WORKER_CONTEXT["performance_y"]
    metric_rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []
    relation: dict[str, dict[str, np.ndarray]] = {}
    random: dict[str, list[dict[str, np.ndarray]]] = {}
    competent: dict[str, bool] = {}

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
        competent[architecture] = (
            performance["both_correct"] >= TASK_COMPETENCE_THRESHOLD
        )
        if architecture == "independent":
            metrics = {
                "component_norm": 0.0,
                "normal_cross_entropy": performance["cross_entropy"],
                "normal_both_correct": performance["both_correct"],
                "delete_cross_entropy_increase": 0.0,
                "random_delete_cross_entropy_increase_median": 0.0,
                "delete_selectivity": 0.0,
                "delete_empirical_percentile": 0.0,
                "delete_empirical_p": 1.0,
                "bilateral_response_minimum": 0.0,
            }
            relation[architecture] = {}
            random[architecture] = []
        else:
            metrics, relation[architecture], random[architecture] = audit(
                architecture,
                model,
                episodes,
                profiles,
                1640000 + 100 * training_seed + architecture_index,
                args.deletion_random_draws,
                args.context_random_draws,
            )
        metric_rows.append({
            "training_seed": training_seed,
            "architecture": architecture,
            "task_competent": competent[architecture],
            "heldout_both_correct": performance["both_correct"],
            **metrics,
        })

    for left_index, left_architecture in enumerate(INTERACTING_ARCHITECTURES):
        for right_architecture in INTERACTING_ARCHITECTURES[left_index + 1 :]:
            if not (competent[left_architecture] and competent[right_architecture]):
                continue
            relation_cka = E012.linear_cka(
                E012.field_matrix(relation[left_architecture]),
                E012.field_matrix(relation[right_architecture]),
            )
            random_values = [
                E012.linear_cka(
                    E012.field_matrix(random[left_architecture][draw]),
                    E012.field_matrix(random[right_architecture][draw]),
                )
                for draw in range(args.context_random_draws)
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
                "context_cka_specificity": relation_cka - float(np.median(random_values)),
            })
    return metric_rows, context_rows


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
        raise SystemExit("FAIL: workers must be at least 1")
    if args.mode == "confirmatory":
        seed_indices = CONFIRMATORY_SEEDS
        evaluation_seeds = CONFIRMATORY_EVALUATION_SEEDS
        args.steps = STEPS
        args.batch_size = BATCH_SIZE
        args.learning_rate = LEARNING_RATE
        args.test_episodes = TEST_EPISODES
        args.deletion_random_draws = DELETION_RANDOM_DRAWS
        args.context_random_draws = CONTEXT_RANDOM_DRAWS
    else:
        seed_indices = REGISTRATION_CHECK_SEEDS
        evaluation_seeds = REGISTRATION_CHECK_EVALUATION_SEEDS
        args.steps = 40
        args.batch_size = 32
        args.learning_rate = LEARNING_RATE
        args.test_episodes = 128
        args.deletion_random_draws = 4
        args.context_random_draws = 2
    args.training_seeds = len(seed_indices)

    counts = {
        architecture: P014.active_parameter_count(architecture)
        for architecture in ARCHITECTURES
    }
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
    metric_rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []

    _WORKER_CONTEXT.update({
        "args": args,
        "profiles": profiles,
        "episodes": episodes,
        "performance_x": performance_x,
        "performance_y": performance_y,
    })
    workers = min(args.workers, len(seed_indices))
    if workers > 1:
        if "fork" not in multiprocessing.get_all_start_methods():
            raise SystemExit("FAIL: parallel seed execution requires fork support")
        with multiprocessing.get_context("fork").Pool(processes=workers) as pool:
            seed_results = pool.imap(
                run_training_seed, seed_indices
            )
            for seed_metric_rows, seed_context_rows in seed_results:
                metric_rows.extend(seed_metric_rows)
                context_rows.extend(seed_context_rows)
    else:
        for training_seed in seed_indices:
            seed_metric_rows, seed_context_rows = run_training_seed(training_seed)
            metric_rows.extend(seed_metric_rows)
            context_rows.extend(seed_context_rows)

    args.out_dir.mkdir(parents=True)
    write_csv(args.out_dir / "rank_metrics.csv", metric_rows)
    write_csv(
        args.out_dir / "competent_context_correspondence.csv",
        context_rows,
        [
            "training_seed",
            "left_architecture",
            "right_architecture",
            "involves_new_architecture",
            "relation_context_cka",
            "random_context_cka_median",
            "context_cka_specificity",
        ],
    )

    architecture_summary: dict[str, Any] = {}
    for architecture in ARCHITECTURES:
        all_rows = [row for row in metric_rows if row["architecture"] == architecture]
        competent_rows = [row for row in all_rows if row["task_competent"]]
        architecture_summary[architecture] = {
            "total_seed_count": len(all_rows),
            "competent_seed_count": len(competent_rows),
            "competence_rate": len(competent_rows) / len(all_rows),
            "heldout_both_correct": summarize([
                float(row["heldout_both_correct"]) for row in all_rows
            ]),
        }
        if competent_rows:
            for field in (
                "component_norm",
                "delete_cross_entropy_increase",
                "random_delete_cross_entropy_increase_median",
                "delete_selectivity",
                "delete_empirical_percentile",
                "delete_empirical_p",
                "bilateral_response_minimum",
            ):
                architecture_summary[architecture][field] = summarize([
                    float(row[field]) for row in competent_rows
                ])
            architecture_summary[architecture]["percentile_0_95_count"] = sum(
                float(row["delete_empirical_percentile"]) >= 0.95
                for row in competent_rows
            )
            architecture_summary[architecture]["positive_selectivity_count"] = sum(
                float(row["delete_selectivity"]) > 0.0 for row in competent_rows
            )

    new_pair_summary: dict[str, Any] = {}
    for other_architecture in E009.INTERACTING_ARCHITECTURES:
        chosen = [
            row for row in context_rows
            if {row["left_architecture"], row["right_architecture"]}
            == {other_architecture, NEW_ARCHITECTURE}
        ]
        key = other_architecture + "__" + NEW_ARCHITECTURE
        new_pair_summary[key] = {
            "jointly_competent_seed_count": len(chosen),
            "relation_context_cka": summarize_or_empty([
                float(row["relation_context_cka"]) for row in chosen
            ]),
            "random_context_cka_median": summarize_or_empty([
                float(row["random_context_cka_median"]) for row in chosen
            ]),
            "context_cka_specificity": summarize_or_empty([
                float(row["context_cka_specificity"]) for row in chosen
            ]),
        }

    architecture_rank_tests: dict[str, Any] = {}
    for architecture in INTERACTING_ARCHITECTURES:
        item = architecture_summary[architecture]
        competent_count = int(item["competent_seed_count"])
        top_count = int(item.get("percentile_0_95_count", 0))
        exact_p = binomial_upper_tail(
            competent_count, top_count, RANK_NULL_PROBABILITY
        )
        architecture_rank_tests[architecture] = {
            "competent_seed_count": competent_count,
            "top_0_95_seed_count": top_count,
            "positive_selectivity_count": int(
                item.get("positive_selectivity_count", 0)
            ),
            "rank_null_probability": RANK_NULL_PROBABILITY,
            "exact_one_sided_binomial_p": exact_p,
        }

    passing_rank_architectures = [
        architecture for architecture, item in architecture_rank_tests.items()
        if item["top_0_95_seed_count"]
        >= MINIMUM_TOP_095_PER_PASSING_ARCHITECTURE
        and item["exact_one_sided_binomial_p"] <= PER_ARCHITECTURE_ALPHA
    ]
    passing_positive_architectures = [
        architecture for architecture, item in architecture_rank_tests.items()
        if item["positive_selectivity_count"]
        >= MINIMUM_POSITIVE_SELECTIVITY_PER_PASSING_ARCHITECTURE
    ]
    pooled_top_count = sum(
        item["top_0_95_seed_count"] for item in architecture_rank_tests.values()
    )
    bilateral_0_90_counts = {
        architecture: sum(
            float(row["bilateral_response_minimum"]) >= MINIMUM_RUN_BILATERAL
            for row in metric_rows
            if row["architecture"] == architecture and row["task_competent"]
        )
        for architecture in INTERACTING_ARCHITECTURES
    }
    checks = {
        "capacity_exact_486": set(counts.values()) == {486},
        "competence_at_least_22_of_24_each_architecture": all(
            item["competent_seed_count"] >= MINIMUM_COMPETENT_SEEDS
            for item in architecture_rank_tests.values()
        ),
        "at_least_three_architectures_top_0_95_14_of_24_with_exact_p": (
            len(passing_rank_architectures) >= MINIMUM_PASSING_ARCHITECTURES
        ),
        "pooled_top_0_95_at_least_60_of_96": (
            pooled_top_count >= MINIMUM_POOLED_TOP_095
        ),
        "at_least_three_architectures_positive_14_of_24": (
            len(passing_positive_architectures) >= MINIMUM_PASSING_ARCHITECTURES
        ),
        "median_bilateral_minimum_at_least_0_95_each_architecture": all(
            "bilateral_response_minimum" in architecture_summary[name]
            and architecture_summary[name]["bilateral_response_minimum"]["median"]
            >= MINIMUM_MEDIAN_BILATERAL
            for name in INTERACTING_ARCHITECTURES
        ),
        "bilateral_minimum_0_90_in_at_least_22_of_24_each_architecture": all(
            bilateral_0_90_counts[name] >= MINIMUM_BILATERAL_RUNS
            for name in INTERACTING_ARCHITECTURES
        ),
        "independent_accuracy_maximum_0_20": (
            architecture_summary["independent"]["heldout_both_correct"]["maximum"]
            <= 0.20
        ),
        "independent_component_zero": all(
            float(row["component_norm"]) < 1e-10
            for row in metric_rows if row["architecture"] == "independent"
        ),
        "new_architecture_context_cka_median_at_least_0_35": all(
            item["jointly_competent_seed_count"] > 0
            and item["relation_context_cka"]["median"] is not None
            and item["relation_context_cka"]["median"] >= MINIMUM_CONTEXT_CKA
            for item in new_pair_summary.values()
        ),
        "new_architecture_context_specificity_median_at_least_0_15": all(
            item["jointly_competent_seed_count"] > 0
            and item["context_cka_specificity"]["median"] is not None
            and item["context_cka_specificity"]["median"]
            >= MINIMUM_CONTEXT_SPECIFICITY
            for item in new_pair_summary.values()
        ),
    }
    readout = (
        "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    ) if args.mode == "confirmatory" else "NOT_APPLICABLE"
    summary = {
        "schema": SCHEMA,
        "status": (
            "CONFIRMATORY_COMPLETE"
            if args.mode == "confirmatory"
            else "REGISTRATION_CHECK_COMPLETE"
        ),
        "mode": args.mode,
        "primary_readout": readout,
        "task": "delayed reciprocal recall",
        "capacity": counts,
        "training": {
            "steps": args.steps,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "training_seed_indices": list(seed_indices),
            "training_seed_count": len(seed_indices),
            "no_seed_replacement": True,
        },
        "evaluation": {
            "test_episodes": args.test_episodes,
            "deletion_random_draws": args.deletion_random_draws,
            "context_random_draws": args.context_random_draws,
            "random_control": "episode-wise receiver-norm-matched direction",
            "task_competence_threshold": TASK_COMPETENCE_THRESHOLD,
            "evaluation_seeds": list(evaluation_seeds),
        },
        "competence_denominator": (
            "All fixed seeds are reported. Carrier classification is conditioned on the "
            "predeclared ability to perform the task."
        ),
        "local_carrier": architecture_summary,
        "new_architecture_correspondence": new_pair_summary,
        "architecture_rank_tests": architecture_rank_tests,
        "passing_rank_architectures": passing_rank_architectures,
        "passing_positive_architectures": passing_positive_architectures,
        "pooled_top_0_95_count": pooled_top_count,
        "bilateral_0_90_counts": bilateral_0_90_counts,
        "acceptance_checks": checks,
        "registration_verification": registration_verification,
        "calibration_firewall": (
            "Local calibration seeds 0..7, 100..111, and 200..223 and all local "
            "calibration outputs are excluded from this confirmatory result."
        ),
        "claim_boundary": (
            "A supported result establishes a recurrent solution class in which an "
            "ordinary coordination objective produces a receiver-specific relational "
            "component with unusual causal rank and cross-architecture intervention "
            "geometry. It does not identify the component with ontological subjectivity."
        ),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out_dir / "RESULT.md").write_text(
        render_result(summary), encoding="utf-8"
    )
    manifest = {
        "schema": "siel-experiment-005-output-manifest-v1",
        "mode": args.mode,
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
        "primary_readout": readout,
        "acceptance_checks": checks,
        "architecture_rank_tests": architecture_rank_tests,
        "passing_rank_architectures": passing_rank_architectures,
        "pooled_top_0_95_count": pooled_top_count,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
