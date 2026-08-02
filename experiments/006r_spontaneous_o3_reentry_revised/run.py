#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Result-informed revised confirmation of spontaneous operational O3 re-entry."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
E006_SOURCE = (
    REPOSITORY_ROOT
    / "experiments"
    / "006_spontaneous_o3_reentry"
    / "run.py"
)
SCHEMA = "siel-experiment-006r-spontaneous-o3-reentry-v1"
CONFIRMATORY_SEEDS = tuple(range(3000, 3048))
CONFIRMATORY_EVALUATION_SEEDS = (61650001, 61650002)
REGISTRATION_CHECK_SEEDS = (2900,)
REGISTRATION_CHECK_EVALUATION_SEEDS = (61649001, 61649002)
DEVELOPMENT_SEEDS_EXCLUDED = (
    tuple(range(300, 312))
    + tuple(range(400, 448))
    + tuple(range(1000, 1024))
    + tuple(range(2000, 2024))
)
MINIMUM_COMPETENT_SEEDS = 44
MINIMUM_TRANSPORT_SEEDS_PER_ARCHITECTURE = 40
MINIMUM_ACTION_SEEDS_PER_ARCHITECTURE = 36
MINIMUM_POOLED_TRANSPORT_SEEDS = 168
SECONDARY_PARTITIONED_MINIMUM = 40
SECONDARY_DISTRIBUTED_MAXIMUM = 39
SECONDARY_MINIMUM_GAP = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("registration-check", "confirmatory"), required=True
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_registration_manifest() -> dict[str, Any]:
    path = HERE / "registration_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = manifest.get("source_sha256", {})
    if not expected:
        raise SystemExit("FAIL: registration manifest has no source hashes")
    observed: dict[str, str] = {}
    mismatches: list[str] = []
    for relative, expected_hash in sorted(expected.items()):
        source = REPOSITORY_ROOT / relative
        if not source.is_file():
            mismatches.append(relative + ":missing")
            continue
        observed_hash = sha256_file(source)
        observed[relative] = observed_hash
        if observed_hash != expected_hash:
            mismatches.append(relative + ":hash")
    if mismatches:
        raise SystemExit("FAIL: frozen source mismatch: " + ", ".join(mismatches))
    return {
        "manifest": str(path.relative_to(REPOSITORY_ROOT)),
        "source_count": len(expected),
        "all_source_hashes_match": True,
        "observed_source_sha256": observed,
    }


def load_e006():
    module_name = "e006_registered_computation_for_e006r"
    spec = importlib.util.spec_from_file_location(module_name, E006_SOURCE)
    if spec is None or spec.loader is None:
        raise SystemExit("FAIL: cannot load frozen Experiment 006 computation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def primary_checks(e006, summary: dict[str, Any]) -> dict[str, bool]:
    architectures = {
        name: summary["architectures"][name]
        for name in e006.INTERACTING_ARCHITECTURES
    }
    pooled = sum(
        item["transport_all_three_seed_count"]
        for item in architectures.values()
    )
    return {
        "capacity_exact_486": {
            e006.P014.active_parameter_count(name)
            for name in e006.ARCHITECTURES
        } == {486},
        "competence_at_least_44_of_48_each_interacting_architecture": all(
            item["competent_seed_count"] >= MINIMUM_COMPETENT_SEEDS
            for item in architectures.values()
        ),
        "transport_all_three_at_least_40_of_48_each_architecture": all(
            item["transport_all_three_seed_count"]
            >= MINIMUM_TRANSPORT_SEEDS_PER_ARCHITECTURE
            for item in architectures.values()
        ),
        "pooled_transport_at_least_168_of_192": (
            pooled >= MINIMUM_POOLED_TRANSPORT_SEEDS
        ),
        "action_loss_two_of_three_at_least_36_of_48_each": all(
            item["action_two_of_three_seed_count"]
            >= MINIMUM_ACTION_SEEDS_PER_ARCHITECTURE
            for item in architectures.values()
        ),
        "action_magnitude_two_of_three_at_least_36_of_48_each": all(
            item["action_magnitude_two_of_three_seed_count"]
            >= MINIMUM_ACTION_SEEDS_PER_ARCHITECTURE
            for item in architectures.values()
        ),
        "median_transport_fraction_at_least_0_75_each": all(
            item["transport_fraction_of_next"]["median"] >= 0.75
            for item in architectures.values()
        ),
        "median_transport_alignment_at_least_0_60_each": all(
            item["transport_alignment_with_next"]["median"] >= 0.60
            for item in architectures.values()
        ),
        "median_exchange_loss_at_least_0_25_each": all(
            item["exchange_cross_entropy_increase"]["median"] >= 0.25
            for item in architectures.values()
        ),
        "median_bilateral_erasure_at_least_0_95_each": all(
            item["erase_bilateral_fraction"]["median"] >= 0.95
            for item in architectures.values()
        ),
        "independent_accuracy_at_most_0_20": (
            summary["architectures"]["independent"]
            ["heldout_both_correct"]["maximum"] <= 0.20
        ),
        "independent_component_at_most_1e_10": (
            summary["architectures"]["independent"]
            ["component_norm"]["maximum"] <= 1e-10
        ),
        "reentry_reconstruction_error_at_most_1e_12": all(
            item["reentry_state_reconstruction_error"]["maximum"] <= 1e-12
            for item in summary["architectures"].values()
        ),
    }


def secondary_boundary(e006, summary: dict[str, Any]) -> dict[str, Any]:
    counts = {
        name: summary["architectures"][name][
            "own_history_two_of_three_seed_count"
        ]
        for name in e006.INTERACTING_ARCHITECTURES
    }
    partitioned = (
        "central_shared", "directional_relay", "four_channel_crossbar"
    )
    checks = {
        "partitioned_architectures_at_least_40_of_48": all(
            counts[name] >= SECONDARY_PARTITIONED_MINIMUM
            for name in partitioned
        ),
        "distributed_fewer_than_40_of_48": (
            counts["distributed"] <= SECONDARY_DISTRIBUTED_MAXIMUM
        ),
        "distributed_gap_at_least_6": (
            min(counts[name] for name in partitioned)
            - counts["distributed"] >= SECONDARY_MINIMUM_GAP
        ),
    }
    return {
        "counts": counts,
        "checks": checks,
        "readout": (
            "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
        ),
    }


def render_result(summary: dict[str, Any], e006) -> str:
    lines = [
        "# Experiment 006R Result",
        "",
        "## Revised Confirmation of Spontaneous Operational O3 Re-entry",
        "",
        f"Status: {summary['status']}",
        f"Primary readout: {summary['primary_readout']}",
        f"Secondary boundary readout: {summary['secondary_boundary']['readout']}",
        "",
        "| Architecture | Competent | Transport all 3 | Action 2 of 3 | Own-history 2 of 3 |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in e006.INTERACTING_ARCHITECTURES:
        item = summary["architectures"][name]
        lines.append(
            f"| {name} | {item['competent_seed_count']} | "
            f"{item['transport_all_three_seed_count']} | "
            f"{item['action_two_of_three_seed_count']} | "
            f"{item['own_history_two_of_three_seed_count']} |"
        )
    lines.extend(["", "## Revised primary acceptance checks", ""])
    for name, passed in summary["primary_acceptance_checks"].items():
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Secondary boundary checks", ""])
    for name, passed in summary["secondary_boundary"]["checks"].items():
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Interpretation boundary", "", summary["claim_boundary"], ""])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.out_dir.exists():
        raise SystemExit("FAIL: output directory exists")
    verification = (
        verify_registration_manifest() if args.check
        else {"all_source_hashes_match": None, "check_requested": False}
    )
    e006 = load_e006()
    e006.CONFIRMATORY_SEEDS = CONFIRMATORY_SEEDS
    e006.CONFIRMATORY_EVALUATION_SEEDS = CONFIRMATORY_EVALUATION_SEEDS
    e006.REGISTRATION_CHECK_SEEDS = REGISTRATION_CHECK_SEEDS
    e006.REGISTRATION_CHECK_EVALUATION_SEEDS = (
        REGISTRATION_CHECK_EVALUATION_SEEDS
    )
    e006.DEVELOPMENT_SEEDS_EXCLUDED = DEVELOPMENT_SEEDS_EXCLUDED

    original_argv = sys.argv
    sys.argv = [
        str(E006_SOURCE), "--mode", args.mode,
        "--out-dir", str(args.out_dir),
        "--workers", str(args.workers),
    ]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            e006.main()
    finally:
        sys.argv = original_argv

    summary_path = args.out_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["schema"] = SCHEMA
    summary["registration_verification"] = verification
    summary["experiment_006_confirmatory_seeds_reused"] = bool(
        set(summary["training_seeds"]) & set(range(2000, 2024))
    )
    summary["result_informed_revision"] = True
    summary["primary_acceptance_checks"] = primary_checks(e006, summary)
    summary["secondary_boundary"] = secondary_boundary(e006, summary)
    summary["pooled_transport_seed_passes"] = sum(
        summary["architectures"][name]["transport_all_three_seed_count"]
        for name in e006.INTERACTING_ARCHITECTURES
    )
    summary["claim_boundary"] = (
        "A supported primary result confirms transfer of spontaneous operational "
        "O3 re-entry across a new 48-seed allocation. The secondary readout tests "
        "whether relation-versus-individual-history identifiability depends on "
        "implementation topology. Neither decision identifies the learned component "
        "with ontological subjectivity or proves a unique physical mechanism."
    )
    if args.mode == "confirmatory":
        summary["primary_readout"] = (
            "SUPPORTED" if all(summary["primary_acceptance_checks"].values())
            else "NOT_SUPPORTED"
        )
    else:
        summary["primary_readout"] = "NOT_APPLICABLE"
        summary["secondary_boundary"]["readout"] = "NOT_APPLICABLE"
    summary.pop("acceptance_checks", None)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "RESULT.md").write_text(
        render_result(summary, e006), encoding="utf-8"
    )
    manifest = {
        "schema": "siel-experiment-006r-output-manifest-v1",
        "mode": args.mode,
        "files_sha256": {
            path.name: sha256_file(path)
            for path in sorted(args.out_dir.iterdir())
            if path.name != "output_manifest.json"
        },
    }
    (args.out_dir / "output_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": summary["status"],
        "primary_readout": summary["primary_readout"],
        "secondary_boundary_readout": summary["secondary_boundary"]["readout"],
        "pooled_transport_seed_passes": summary["pooled_transport_seed_passes"],
        "primary_acceptance_checks": summary["primary_acceptance_checks"],
        "secondary_boundary": summary["secondary_boundary"],
        "architectures": {
            name: {
                "competent": summary["architectures"][name]["competent_seed_count"],
                "transport_all_three": summary["architectures"][name]["transport_all_three_seed_count"],
                "action_two_of_three": summary["architectures"][name]["action_two_of_three_seed_count"],
                "own_history_two_of_three": summary["architectures"][name]["own_history_two_of_three_seed_count"],
            }
            for name in e006.INTERACTING_ARCHITECTURES
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
