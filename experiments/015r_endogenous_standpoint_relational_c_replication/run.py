#!/usr/bin/env python3
"""Frozen E015R public confirmatory replication runner.

The simulator and representation mechanism are an exact byte-preserved copy
of the retained E015-X3 runner. E015R repeats the registered E015 operational
test on fresh seeds and adds a hard DOI-1 verification gate before execution.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
BASE_PATH = HERE / "e015_x3_frozen_base.py"
BASE_SHA256 = "9c56bc3a6293e40345ed35aa1d97815228e405eda5106ae9d521a5d2684b43f1"
CONFIRMATORY_SEEDS = tuple(range(98100, 98148))
TEST_SEEDS = tuple(range(98000, 98008))
RANDOMIZATIONS = 10_000
ALPHA = 0.05
PREREGISTRATION_TAG = "e015r-preregistration-v1.0.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


if sha256(BASE_PATH) != BASE_SHA256:
    raise RuntimeError("E015-X3 base runner hash mismatch")

SPEC = importlib.util.spec_from_file_location("e015_x3_frozen_base", BASE_PATH)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = BASE
SPEC.loader.exec_module(BASE)


def verify_manifest(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        target = REPOSITORY_ROOT / relative
        actual = sha256(target)
        if actual != expected:
            raise SystemExit(f"manifest mismatch: {relative}: {actual} != {expected}")


def verify_baseline_gate() -> dict[str, object]:
    gate = json.loads((HERE / "BASELINE_GATE.json").read_text(encoding="utf-8"))
    required = (
        "source_identity",
        "path_manifest",
        "split_manifest_status",
        "baseline_intermediate",
        "baseline_primary",
        "intervention_invariants",
    )
    if any(gate.get(name) != "PASS" for name in required):
        raise SystemExit("Exact-Path Baseline Gate is not PASS")
    if gate.get("scientific_baseline_authorized") is not True:
        raise SystemExit("E015R scientific baseline gate is not authorized")
    return gate


def verify_doi1_gate(manifest: Path) -> dict[str, object]:
    receipt_path = HERE / "registration_receipt.json"
    if not receipt_path.exists():
        raise SystemExit("E-DOI-1 blocked: registration_receipt.json is absent")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    required_true = (
        "zenodo_record_public",
        "remote_release_reopened",
        "remote_doi_reopened",
        "files_and_checksums_match",
    )
    if receipt.get("status") != "PASS":
        raise SystemExit("E-DOI-1 blocked: receipt status is not PASS")
    if receipt.get("tag") != PREREGISTRATION_TAG:
        raise SystemExit("E-DOI-1 blocked: preregistration tag mismatch")
    if not str(receipt.get("doi", "")).startswith("10.5281/zenodo."):
        raise SystemExit("E-DOI-1 blocked: published Zenodo DOI is absent")
    if any(receipt.get(name) is not True for name in required_true):
        raise SystemExit("E-DOI-1 blocked: public verification is incomplete")
    if receipt.get("manifest_sha256") != sha256(manifest):
        raise SystemExit("E-DOI-1 blocked: frozen manifest receipt mismatch")
    return receipt


def renamed_episode(episode: object) -> object:
    return BASE.Episode(
        actions=np.asarray(episode.actions)[::-1].copy(),
        values=np.asarray(episode.values).copy(),
        sources=(1 - np.asarray(episode.sources)).copy(),
        maps_before=(episode.maps_before[1], episode.maps_before[0]),
        maps_after=(episode.maps_after[1], episode.maps_after[0]),
        port_swap=episode.port_swap,
    )


def channel_permuted_episode(episode: object) -> object:
    return BASE.Episode(
        actions=np.asarray(episode.actions).copy(),
        values=np.asarray(episode.values)[:, ::-1].copy(),
        sources=np.asarray(episode.sources)[:, ::-1].copy(),
        maps_before=episode.maps_before,
        maps_after=episode.maps_after,
        port_swap=episode.port_swap,
    )


def view_difference(
    left: object, right: object, *, include_fixed_position_control: bool = True
) -> float:
    differences = [
        float(np.max(np.abs(left.x - right.x))),
        float(np.max(np.abs(left.target - right.target))),
        abs(float(left.role_accuracy) - float(right.role_accuracy)),
        abs(float(left.post_swap_accuracy) - float(right.post_swap_accuracy)),
    ]
    if include_fixed_position_control:
        differences.append(
            abs(
                float(left.fixed_position_accuracy)
                - float(right.fixed_position_accuracy)
            )
        )
    return max(differences)


def observation_rows(episodes: Sequence[object]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for episode in episodes:
        for t in range(BASE.EVAL_START, BASE.STEPS):
            for observer in (0, 1):
                for position in (0, 1):
                    rows.append(
                        {
                            "position": position,
                            "value_bin": int(round(float(episode.values[t, position]) * 4.0)),
                            "time_parity": t % 2,
                            "target": int(int(episode.sources[t, position]) == observer),
                        }
                    )
    return rows


def observation_only_accuracy(
    training_episodes: Sequence[object], testing_episodes: Sequence[object]
) -> float:
    counts: dict[tuple[int, int, int], list[int]] = {}
    for row in observation_rows(training_episodes):
        key = (row["position"], row["value_bin"], row["time_parity"])
        counts.setdefault(key, [0, 0])[row["target"]] += 1
    hits = 0
    testing = observation_rows(testing_episodes)
    for row in testing:
        key = (row["position"], row["value_bin"], row["time_parity"])
        count = counts.get(key, [1, 1])
        prediction = 1 if count[1] > count[0] else 0
        hits += int(prediction == row["target"])
    return hits / len(testing)


def intervention_metrics(
    reservoir: object,
    beta: np.ndarray,
    views: Sequence[object],
    records: Sequence[dict[str, object]],
) -> dict[str, float]:
    state_only_effects: list[float] = []
    coherent_errors: list[float] = []
    reconstruction_errors: list[float] = []
    for index, (view, record) in enumerate(zip(views, records)):
        donor = records[(index + 2) % len(records)]
        donor_view = views[(index + 2) % len(views)]
        baseline = np.asarray(record["baseline_output"], dtype=float)
        recipient_x = np.asarray(record["x"], dtype=float)
        donor_state = np.asarray(donor["baseline_state"], dtype=float)
        state_only = BASE.future_output(
            reservoir,
            beta,
            donor_state,
            recipient_x,
            BASE.LESION_STEP + 1,
            BASE.HORIZON,
        )
        state_only_effects.append(
            float(
                np.mean(np.abs(baseline - state_only))
                / max(float(record["output_scale"]), 1e-12)
            )
        )

        donor_baseline = np.asarray(donor["baseline_output"], dtype=float)
        coherent = BASE.future_output(
            reservoir,
            beta,
            donor_state,
            np.asarray(donor_view.x, dtype=float),
            BASE.LESION_STEP + 1,
            BASE.HORIZON,
        )
        coherent_errors.append(
            float(
                np.mean(np.abs(donor_baseline - coherent))
                / max(float(donor["output_scale"]), 1e-12)
            )
        )

        states = BASE.four_history_states(reservoir, view.x)
        c = BASE.component(states)
        c_t = c[BASE.LESION_STEP]
        baseline_state = states["ab"][BASE.LESION_STEP]
        deleted_next = BASE.advance(
            reservoir,
            baseline_state - c_t,
            view.x[BASE.LESION_STEP + 1],
        )
        intervened_next_c = (
            deleted_next
            - states["a0"][BASE.LESION_STEP + 1]
            - states["0b"][BASE.LESION_STEP + 1]
            + states["00"][BASE.LESION_STEP + 1]
        )
        baseline_next_c = c[BASE.LESION_STEP + 1]
        transported = baseline_next_c - intervened_next_c
        reconstructed = intervened_next_c + transported
        reconstruction_errors.append(
            float(np.max(np.abs(reconstructed - baseline_next_c)))
        )
    return {
        "state_only_exchange_effect": float(np.mean(state_only_effects)),
        "coherent_exchange_error": float(np.mean(coherent_errors)),
        "reentry_reconstruction_error": float(max(reconstruction_errors)),
    }


def evaluate_seed(seed: int) -> dict[str, float | int]:
    train_episodes = [
        BASE.generate_episode(seed * 1000 + 100 + index, port_swap=(index % 2 == 1))
        for index in range(BASE.TRAIN_EPISODES)
    ]
    test_episodes = [
        BASE.generate_episode(seed * 1000 + 500 + index, port_swap=(index % 2 == 1))
        for index in range(BASE.TEST_EPISODES)
    ]
    train_views = [
        BASE.build_view(episode, observer, index)
        for index, episode in enumerate(train_episodes)
        for observer in (0, 1)
    ]
    test_views = [
        BASE.build_view(episode, observer, index)
        for index, episode in enumerate(test_episodes)
        for observer in (0, 1)
    ]

    rename_difference = 0.0
    channel_difference = 0.0
    for index, episode in enumerate(test_episodes):
        renamed = renamed_episode(episode)
        permuted = channel_permuted_episode(episode)
        for observer in (0, 1):
            original = test_views[2 * index + observer]
            rename_difference = max(
                rename_difference,
                view_difference(
                    original,
                    BASE.build_view(renamed, 1 - observer, index),
                ),
            )
            channel_difference = max(
                channel_difference,
                view_difference(
                    original,
                    BASE.build_view(permuted, observer, index),
                    include_fixed_position_control=False,
                ),
            )

    connected = BASE.train_reservoir(seed + 10_000_000, "connected", train_views)
    additive = BASE.train_reservoir(seed + 20_000_000, "additive", train_views)
    beta_connected = BASE.fit_readout(connected, train_views)
    beta_additive = BASE.fit_readout(additive, train_views)
    connected_r2 = BASE.evaluate_predictions(connected, beta_connected, test_views)
    additive_r2 = BASE.evaluate_predictions(additive, beta_additive, test_views)
    shuffled_r2 = BASE.shuffled_other_r2(connected, beta_connected, test_views)

    rng = np.random.default_rng(seed + 30_000_000)
    records = [
        BASE.view_component_record(connected, additive, beta_connected, view, rng)
        for view in test_views
    ]
    BASE.add_exchange_effects(connected, beta_connected, records)
    bilateral_minima = []
    for episode_index in range(BASE.TEST_EPISODES):
        pair = [
            float(row["deletion_effect"])
            for row in records
            if row["episode_index"] == episode_index
        ]
        bilateral_minima.append(min(pair))
    interventions = intervention_metrics(connected, beta_connected, test_views, records)

    return {
        "seed": seed,
        "role_accuracy": float(np.mean([view.role_accuracy for view in test_views])),
        "post_swap_accuracy": float(
            np.mean(
                [
                    view.post_swap_accuracy
                    for view in test_views
                    if test_episodes[view.episode_index].port_swap
                ]
            )
        ),
        "fixed_position_accuracy": float(
            np.mean([view.fixed_position_accuracy for view in test_views])
        ),
        "observation_only_accuracy": observation_only_accuracy(
            train_episodes, test_episodes
        ),
        "rename_difference": rename_difference,
        "channel_permutation_difference": channel_difference,
        "connected_r2": connected_r2,
        "additive_r2": additive_r2,
        "shuffled_other_r2": shuffled_r2,
        "connected_advantage": connected_r2 - additive_r2,
        "shuffle_drop": connected_r2 - shuffled_r2,
        "c_rms": float(np.mean([float(row["c_rms"]) for row in records])),
        "additive_c_rms": float(
            np.max([float(row["additive_c_rms"]) for row in records])
        ),
        "deletion_effect": float(
            np.mean([float(row["deletion_effect"]) for row in records])
        ),
        "bilateral_min_effect": float(np.mean(bilateral_minima)),
        "transport_fraction": float(
            np.mean([float(row["transport_fraction"]) for row in records])
        ),
        "exchange_effect": float(
            np.mean([float(row["exchange_effect"]) for row in records])
        ),
        **interventions,
    }


def sign_flip_pvalue(differences: Sequence[float], seed: int) -> float:
    observed = statistics.fmean(differences)
    rng = np.random.default_rng(seed)
    exceed = 0
    array = np.asarray(differences, dtype=float)
    for _ in range(RANDOMIZATIONS):
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=len(array))
        if float(np.mean(array * signs)) >= observed:
            exceed += 1
    return (exceed + 1) / (RANDOMIZATIONS + 1)


def holm(pvalues: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    passed = {name: False for name in pvalues}
    still_passing = True
    total = len(ordered)
    for rank, (name, pvalue) in enumerate(ordered):
        threshold = alpha / (total - rank)
        if still_passing and pvalue < threshold:
            passed[name] = True
        else:
            still_passing = False
    return passed


def normal_tost(differences: Sequence[float], margin: float) -> dict[str, float | bool]:
    mean = statistics.fmean(differences)
    if all(value == differences[0] for value in differences):
        passed = -margin <= mean <= margin
        return {
            "mean": mean,
            "p_lower": 0.0 if passed else 1.0,
            "p_upper": 0.0 if passed else 1.0,
            "passed": passed,
        }
    standard_error = statistics.stdev(differences) / math.sqrt(len(differences))
    normal = statistics.NormalDist()
    z_lower = (mean + margin) / standard_error
    z_upper = (margin - mean) / standard_error
    p_lower = 1.0 - normal.cdf(z_lower)
    p_upper = 1.0 - normal.cdf(z_upper)
    return {
        "mean": mean,
        "p_lower": p_lower,
        "p_upper": p_upper,
        "passed": p_lower < ALPHA and p_upper < ALPHA,
    }


def count_at_least(rows: Sequence[dict[str, float | int]], name: str, value: float) -> int:
    return sum(float(row[name]) >= value for row in rows)


def count_positive(rows: Sequence[dict[str, float | int]], name: str) -> int:
    return sum(float(row[name]) > 0.0 for row in rows)


def summarize(rows: Sequence[dict[str, float | int]]) -> dict[str, object]:
    metric_names = [name for name in rows[0] if name != "seed"]
    values = {
        name: [float(row[name]) for row in rows]
        for name in metric_names
    }
    means = {name: statistics.fmean(series) for name, series in values.items()}
    medians = {name: statistics.median(series) for name, series in values.items()}
    pvalues = {
        "connected_advantage": sign_flip_pvalue(
            values["connected_advantage"], 981501
        ),
        "shuffle_drop": sign_flip_pvalue(values["shuffle_drop"], 981502),
        "c_exchange": sign_flip_pvalue(values["exchange_effect"], 981503),
    }
    holm_pass = holm(pvalues)
    coherent_tost = normal_tost(values["coherent_exchange_error"], 0.03)
    finite = all(
        math.isfinite(float(value))
        for row in rows
        for name, value in row.items()
        if name != "seed"
    )

    primary_gates = {
        "a1_role_constitution": means["role_accuracy"] >= 0.75
        and count_at_least(rows, "role_accuracy", 0.70) >= 44,
        "a2_post_swap_tracking": means["post_swap_accuracy"] >= 0.75
        and count_at_least(rows, "post_swap_accuracy", 0.68) >= 44,
        "a3_model_competence": means["connected_r2"] >= 0.60
        and count_at_least(rows, "connected_r2", 0.50) >= 44
        and count_at_least(rows, "additive_r2", 0.30) >= 44,
        "a4_connected_advantage": means["connected_advantage"] >= 0.05
        and count_positive(rows, "connected_advantage") >= 44
        and holm_pass["connected_advantage"],
        "a5_other_stream_dependence": means["shuffle_drop"] >= 0.10
        and count_positive(rows, "shuffle_drop") >= 44
        and holm_pass["shuffle_drop"],
        "a6_nonseparable_c": medians["c_rms"] >= 0.03
        and max(values["additive_c_rms"]) <= 1e-10,
        "a7_bilateral_causal_effect": medians["bilateral_min_effect"] >= 0.003
        and count_positive(rows, "bilateral_min_effect") >= 44,
        "a8_later_c_transport": medians["transport_fraction"] >= 0.40
        and count_at_least(rows, "transport_fraction", 0.10) >= 44,
        "a9_cross_pair_c_exchange": medians["exchange_effect"] > 0.0
        and holm_pass["c_exchange"],
    }
    validity_gates = {
        "b1_exact_path_baselines": True,
        "b2_leakage_nulls": means["fixed_position_accuracy"] <= 0.55
        and means["observation_only_accuracy"] <= 0.55,
        "b3_permutation_invariance": max(values["rename_difference"]) == 0.0
        and max(values["channel_permutation_difference"]) == 0.0,
        "b4_state_only_exchange_impairment": medians[
            "state_only_exchange_effect"
        ]
        >= 0.003
        and count_positive(rows, "state_only_exchange_effect") >= 44,
        "b5_coherent_exchange_restoration": bool(coherent_tost["passed"]),
        "b6_reentry_reconstruction": max(
            values["reentry_reconstruction_error"]
        )
        <= 1e-12,
        "b7_runtime_integrity": len(rows) == len(CONFIRMATORY_SEEDS) and finite,
    }
    if not all(validity_gates.values()):
        decision = "Inconclusive result"
    elif not all(primary_gates.values()):
        decision = "Negative result"
    else:
        decision = "SIEL replicated result"
    return {
        "experiment": "E015R",
        "phase": "confirmatory",
        "decision": decision,
        "joint_support": decision == "SIEL replicated result",
        "qualifiers": [
            "synthetic",
            "prospectively public preregistered replication",
            "direct replication of E015 operational gates",
            "adversarial challenge pending",
        ],
        "means": means,
        "medians": medians,
        "counts": {
            "role_ge_0_70": count_at_least(rows, "role_accuracy", 0.70),
            "post_swap_ge_0_68": count_at_least(rows, "post_swap_accuracy", 0.68),
            "connected_r2_ge_0_50": count_at_least(rows, "connected_r2", 0.50),
            "additive_r2_ge_0_30": count_at_least(rows, "additive_r2", 0.30),
            "connected_advantage_positive": count_positive(rows, "connected_advantage"),
            "shuffle_drop_positive": count_positive(rows, "shuffle_drop"),
            "bilateral_positive": count_positive(rows, "bilateral_min_effect"),
            "transport_ge_0_10": count_at_least(rows, "transport_fraction", 0.10),
            "state_only_exchange_positive": count_positive(
                rows, "state_only_exchange_effect"
            ),
        },
        "pvalues_unadjusted": pvalues,
        "holm_pass": holm_pass,
        "coherent_exchange_tost": coherent_tost,
        "primary_gates": primary_gates,
        "validity_gates": validity_gates,
        "seeds": [int(row["seed"]) for row in rows],
        "claim_boundary": (
            "The result is limited to the registered operational conjunction in the frozen "
            "synthetic system: causal-history standpoint constitution, prediction-trained "
            "nonseparable relational C, bilateral causal contribution, and later-C re-entry "
            "without fixed global actor identity."
        ),
    }


def markdown_report(summary: dict[str, object]) -> str:
    means = summary["means"]
    medians = summary["medians"]
    lines = [
        "# E015R public confirmatory replication result",
        "",
        f"- primary decision: **{summary['decision']}**",
        f"- joint support: **{str(summary['joint_support']).lower()}**",
        f"- mean role accuracy: `{means['role_accuracy']:.12f}`",
        f"- mean post-swap accuracy: `{means['post_swap_accuracy']:.12f}`",
        f"- mean connected R2: `{means['connected_r2']:.12f}`",
        f"- mean additive R2: `{means['additive_r2']:.12f}`",
        f"- mean connected advantage: `{means['connected_advantage']:.12f}`",
        f"- mean other-stream shuffle drop: `{means['shuffle_drop']:.12f}`",
        f"- median connected C RMS: `{medians['c_rms']:.12f}`",
        f"- mean additive C RMS: `{summary['means']['additive_c_rms']:.3e}`",
        f"- median bilateral minimum effect: `{medians['bilateral_min_effect']:.12f}`",
        f"- median later-C transport: `{medians['transport_fraction']:.12f}`",
        f"- median cross-pair C exchange: `{medians['exchange_effect']:.12f}`",
        "",
        "## A-class primary gates",
        "",
    ]
    lines.extend(
        f"- {name}: `{str(value).lower()}`"
        for name, value in summary["primary_gates"].items()
    )
    lines.extend(["", "## B-class validity gates", ""])
    lines.extend(
        f"- {name}: `{str(value).lower()}`"
        for name, value in summary["validity_gates"].items()
    )
    lines.extend(["", "## Claim boundary", "", str(summary["claim_boundary"]), ""])
    return "\n".join(lines)


def git_metadata() -> dict[str, object]:
    def command(*args: str) -> str:
        return subprocess.check_output(args, cwd=REPOSITORY_ROOT, text=True).strip()

    return {
        "root": str(REPOSITORY_ROOT),
        "head": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "remote": command("git", "remote", "get-url", "origin"),
        "dirty_before_output": bool(command("git", "status", "--porcelain")),
    }


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run(manifest: Path) -> None:
    verify_manifest(manifest)
    baseline_gate = verify_baseline_gate()
    doi1_receipt = verify_doi1_gate(manifest)
    if subprocess.check_output(
        ("git", "status", "--porcelain"), cwd=REPOSITORY_ROOT, text=True
    ).strip():
        raise SystemExit("confirmatory execution requires a clean Git worktree")
    output_dir = HERE / "results"
    if output_dir.exists():
        raise SystemExit(f"confirmatory output directory already exists: {output_dir}")
    metadata = {
        "experiment": "E015R",
        "phase": "confirmatory",
        "started_unix": time.time(),
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "pid": os.getpid(),
        "git": git_metadata(),
        "manifest": str(manifest),
        "manifest_sha256": sha256(manifest),
        "base_runner_sha256": sha256(BASE_PATH),
        "baseline_gate_sha256": sha256(HERE / "BASELINE_GATE.json"),
        "scientific_baseline_authorized": baseline_gate[
            "scientific_baseline_authorized"
        ],
        "doi1": doi1_receipt,
        "deviations": [],
        "status": "RUNNING",
    }
    output_dir.mkdir()
    rows: list[dict[str, float | int]] = []
    try:
        write_json(output_dir / "execution_log.json", metadata)
        for seed in CONFIRMATORY_SEEDS:
            rows.append(evaluate_seed(seed))
            write_json(output_dir / "e015r_raw_seed_results.partial.json", rows)
        summary = summarize(rows)
        write_json(output_dir / "e015r_raw_seed_results.json", rows)
        write_json(output_dir / "e015r_decision.json", summary)
        (output_dir / "E015R_RESULT_REPORT.md").write_text(
            markdown_report(summary), encoding="utf-8"
        )
        metadata["status"] = "COMPLETE"
        metadata["finished_unix"] = time.time()
        write_json(output_dir / "execution_log.json", metadata)
        print(json.dumps(summary, indent=2, sort_keys=True))
    except BaseException as error:
        metadata["status"] = "ERROR"
        metadata["finished_unix"] = time.time()
        metadata["error_type"] = type(error).__name__
        metadata["error"] = str(error)
        write_json(output_dir / "execution_log.json", metadata)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("confirmatory",), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(arguments.manifest)
