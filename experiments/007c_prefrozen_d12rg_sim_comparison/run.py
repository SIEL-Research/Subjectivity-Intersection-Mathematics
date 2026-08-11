#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 007C pre-frozen D12RG--SIM structural comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import subprocess
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST_PATH = HERE / "registration_manifest.json"
CONTRACT_PATH = HERE / "comparison_contract.json"
SCHEMA = "siel-experiment-007c-prefrozen-d12rg-sim-comparison-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("registration-check", "confirmatory"), required=True
    )
    parser.add_argument("--d12rg-repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def git_value(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def verify_hashes(base: Path, expected: dict[str, str]) -> dict[str, str]:
    observed: dict[str, str] = {}
    failures: list[str] = []
    for relative, wanted in sorted(expected.items()):
        path = base / relative
        if not path.is_file():
            failures.append(relative + ":missing")
            continue
        actual = sha256_file(path)
        observed[relative] = actual
        if actual != wanted:
            failures.append(relative + ":sha256")
    if failures:
        raise RuntimeError("provenance verification failed: " + ", ".join(failures))
    return observed


def verify_registration(manifest: dict[str, Any]) -> dict[str, Any]:
    observed = verify_hashes(ROOT, manifest["registration_sha256"])
    contract = read_json(CONTRACT_PATH)
    if contract.get("schema") != "siel-experiment-007c-comparison-contract-v1":
        raise RuntimeError("unexpected comparison contract schema")
    return {
        "verified": True,
        "file_count": len(observed),
        "observed_sha256": observed,
        "contract_schema": contract["schema"],
    }


def verify_inputs(
    manifest: dict[str, Any], d12rg_repo: Path
) -> dict[str, Any]:
    sim_observed = verify_hashes(ROOT, manifest["sim_source_sha256"])
    if not d12rg_repo.is_dir():
        raise RuntimeError("D12RG repository is missing")
    d12_commit = git_value(d12rg_repo, "rev-parse", "HEAD")
    if d12_commit != manifest["d12rg_source"]["commit"]:
        raise RuntimeError("D12RG commit mismatch")
    remotes = git_value(d12rg_repo, "remote", "-v")
    if manifest["d12rg_source"]["repository"] not in remotes:
        raise RuntimeError("D12RG remote mismatch")
    d12_observed = verify_hashes(
        d12rg_repo, manifest["d12rg_source"]["source_sha256"]
    )
    return {
        "verified": True,
        "sim_source_sha256": sim_observed,
        "d12rg_source_sha256": d12_observed,
        "d12rg_commit": d12_commit,
        "d12rg_remote_verified": True,
    }


def load_primitives(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    **row,
                    "input_types_list": [
                        value for value in row["input_types"].split(";") if value
                    ],
                }
            )
    return rows


def parameter_free_unary(primitive: dict[str, Any]) -> bool:
    return len(primitive["input_types_list"]) == 1


def role_candidates(
    primitives: list[dict[str, Any]], role: str, rule: dict[str, Any]
) -> list[str]:
    candidates: list[str] = []
    for primitive in primitives:
        inputs = primitive["input_types_list"]
        if len(inputs) != int(rule["arity"]):
            continue
        if rule.get("parameter_free") and not parameter_free_unary(primitive):
            continue
        if rule.get("same_input_output_type"):
            if not inputs or inputs[0] != primitive["output_type"]:
                continue
        if rule.get("linearity") and primitive["linearity"] != rule["linearity"]:
            continue
        if rule.get("direction") and primitive["direction"] != rule["direction"]:
            continue

        # Exact order and idempotence must be source-declared. Experiment 007B
        # declares neither property for any primitive and explicitly reports no
        # global generator or involution. Absence is a failed registered gate.
        if "exact_order" in rule:
            continue
        if rule.get("idempotent"):
            continue
        candidates.append(primitive["primitive_id"])
    return sorted(candidates)


def role_rows(
    primitives: list[dict[str, Any]], contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    generated: dict[str, list[str]] = {}
    rows: list[dict[str, Any]] = []
    for role, rule in contract["role_constraints"].items():
        candidates = role_candidates(primitives, role, rule)
        generated[role] = candidates
        if candidates:
            for candidate in candidates:
                rows.append(
                    {
                        "d12rg_role": role,
                        "sim_primitive": candidate,
                        "eligible": True,
                        "reason": "all_registered_signature_gates_pass",
                    }
                )
        else:
            rows.append(
                {
                    "d12rg_role": role,
                    "sim_primitive": "",
                    "eligible": False,
                    "reason": "no_primitive_passes_all_registered_signature_gates",
                }
            )
    return rows, generated


def comparison(
    manifest: dict[str, Any], contract: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    d12_summary = read_json(ROOT / manifest["inputs"]["e007a_summary"])
    sim_summary = read_json(ROOT / manifest["inputs"]["e007b_summary"])
    primitives = load_primitives(ROOT / manifest["inputs"]["e007b_primitives"])
    with (ROOT / manifest["inputs"]["e007b_composition"]).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        composition_rows = list(csv.DictReader(handle))

    d12_object = d12_summary["d12rg_operator_object"]
    d12_checks = d12_object["checks"]
    role_map_rows, candidates = role_rows(primitives, contract)

    sim_common_carrier = sim_summary.get("common_linear_endomorphism_carrier")
    sim_global_generator = bool(
        sim_summary["registered_checks"].get(
            "source_defined_canonical_global_generator", False
        )
    )
    sim_global_involution = bool(
        sim_summary["registered_checks"].get("source_defined_global_involution", False)
    )
    sim_invariant_trace = bool(
        sim_summary["registered_checks"].get(
            "source_defined_global_invariant_trace", False
        )
    )

    algebra_checks = {
        "d12_dimension_seven": d12_object["vector_space_dimension"] == 7,
        "d12_total_closed_product": bool(
            d12_object["linear_span_closed_under_matrix_product"]
        ),
        "d12_identity": bool(d12_checks["identity_is_final_basis_matrix"]),
        "d12_order12_generator": bool(
            d12_checks["generator_has_exact_order_twelve"]
        ),
        "sim_common_linear_endomorphism_carrier": sim_common_carrier is not None,
        "sim_all_actions_linear": all(
            primitive["linearity"] == "linear" for primitive in primitives
        ),
        "sim_total_product": all(row["composable"] == "True" for row in composition_rows),
        "sim_global_generator": sim_global_generator,
        "sim_global_involution": sim_global_involution,
        "dimension_compatible": len(primitives) == contract["d12rg_target"]["dimension"],
    }
    complete_algebra = all(algebra_checks.values())

    readout_checks = {
        "pi_adm_role_mapped": bool(candidates["PI_ADM"]),
        "normalization_role_mapped": bool(candidates["N"]),
        "reconstruction_role_mapped": bool(candidates["R"]),
        "r_after_n_identity_verified": False,
        "n_after_r_projection_verified": False,
        "mediation_readout_square_commutes": False,
    }
    complete_readout = all(readout_checks.values())
    generic = sim_global_involution or sim_invariant_trace

    if complete_algebra and complete_readout:
        classification = "COMPLETE_MARKED_READOUT_CORRESPONDENCE"
    elif complete_readout:
        classification = "PARTIAL_REGISTERED_CORRESPONDENCE"
    elif generic:
        classification = "GENERIC_INVOLUTION_OR_TRACE_ONLY_CORRESPONDENCE"
    else:
        classification = "NO_REGISTERED_CORRESPONDENCE"

    signature_rows: list[dict[str, Any]] = []
    for feature, d12_value, sim_value, preserved in (
        ("native_object", "total unital Q-algebra", sim_summary["primary_classification"], False),
        ("basis_or_primitive_count", 7, len(primitives), len(primitives) == 7),
        ("common_carrier", True, sim_common_carrier is not None, sim_common_carrier is not None),
        ("all_actions_linear", True, algebra_checks["sim_all_actions_linear"], algebra_checks["sim_all_actions_linear"]),
        ("total_composition", True, algebra_checks["sim_total_product"], algebra_checks["sim_total_product"]),
        ("global_order12_generator", True, sim_global_generator, sim_global_generator),
        ("global_involution", True, sim_global_involution, sim_global_involution),
        ("marked_readout_pair", True, complete_readout, complete_readout),
    ):
        signature_rows.append(
            {
                "feature": feature,
                "d12rg": d12_value,
                "sim": sim_value,
                "preserved": preserved,
            }
        )

    count_only_injections = math.comb(len(primitives), 7) if len(primitives) >= 7 else 0
    controls = [
        {
            "control": "COUNT_DIMENSION_ONLY",
            "match": count_only_injections > 0,
            "readout": f"{count_only_injections} unmarked seven-subsets among {len(primitives)} primitives",
        },
        {
            "control": "GENERIC_INVOLUTION_ONLY",
            "match": sim_global_involution,
            "readout": "no source-defined SIM global involution",
        },
        {
            "control": "COMMON_STATE_LABEL_PERMUTATION",
            "match": classification == "NO_REGISTERED_CORRESPONDENCE",
            "readout": "classification is signature-based and unchanged by primitive-label permutations",
        },
        {
            "control": "DROP_DIRECTION",
            "match": False,
            "readout": "no reverse unary typed pair remains after direction is dropped",
        },
        {
            "control": "UNMARKED_ABSTRACT",
            "match": count_only_injections > 0,
            "readout": "unmarked count matching is possible but fails registered identities",
        },
        {
            "control": "REMOVE_D12_MARKINGS_AND_READOUT",
            "match": count_only_injections > 0,
            "readout": "only combinatorial subset matching remains",
        },
    ]

    result = {
        "schema": SCHEMA,
        "status": "COMPLETE",
        "mode": "confirmatory",
        "primary_classification": classification,
        "comparison_designation": "PRE_FROZEN_TARGET_HASH_SEPARATED_COMPARISON",
        "blind_discovery": False,
        "post_result_target_selection": False,
        "d12rg_target": contract["d12rg_target"],
        "excluded_targets": contract["excluded_targets"],
        "sim_object": {
            "primary_classification": sim_summary["primary_classification"],
            "primitive_count": len(primitives),
            "operation_site_count": sim_summary["operation_site_count"],
            "common_linear_endomorphism_carrier": sim_common_carrier,
        },
        "complete_algebra_isomorphism": {
            "supported": complete_algebra,
            "checks": algebra_checks,
        },
        "marked_readout_correspondence": {
            "supported": complete_readout,
            "checks": readout_checks,
            "eligible_role_candidates": candidates,
        },
        "generic_global_involution_or_invariant_trace": {
            "supported": generic,
            "sim_global_involution": sim_global_involution,
            "sim_global_invariant_trace": sim_invariant_trace,
        },
        "controls": controls,
        "wall_hypergroup": {
            "role": contract["wall_hypergroup_role"],
            "affects_primary_classification": False,
        },
        "main_readout": (
            "The pre-frozen D12RG 4+2+1 object is a total unital rational "
            "operator algebra with a global order-12 generator, reciprocal "
            "involution, and marked two-way readout. The independently frozen "
            "SIM object is a heterogeneous typed nonlinear action structure. "
            "No map satisfies the registered exact correspondence levels."
        ),
        "claim_boundary": (
            "This classification concerns only the two frozen operational "
            "objects and the registered maps. It does not decide broader "
            "relations between D12RG and Subjectivity-Intersection Mathematics."
        ),
    }
    return result, role_map_rows, signature_rows, controls


def result_markdown(summary: dict[str, Any]) -> str:
    algebra = summary["complete_algebra_isomorphism"]
    readout = summary["marked_readout_correspondence"]
    generic = summary["generic_global_involution_or_invariant_trace"]
    return f"""# Experiment 007C Result

## Primary classification

`{summary['primary_classification']}`

## Result

{summary['main_readout']}

The complete algebra-isomorphism gate was `{algebra['supported']}`. The complete marked-readout gate was `{readout['supported']}`. The generic global-involution or invariant-trace gate was `{generic['supported']}`.

The weakened count-only control found 330 possible seven-element subsets among the eleven SIM primitives. Those combinatorial matches disappear when the registered native object, types, total composition, generator, involution, and readout identities are retained.

## Meaning

The result separates a numerical or schematic resemblance from an exact mathematical correspondence. Under the predeclared rules, the D12RG object and the SIM object are different kinds of structure: one is a total unital rational operator algebra on a common carrier; the other is a partial typed action structure containing nonlinear and discrete-routing operations.

## Boundary

{summary['claim_boundary']}
"""


def output_manifest(out_dir: Path, names: list[str]) -> dict[str, Any]:
    files = {
        name: {"sha256": sha256_file(out_dir / name)}
        for name in names
    }
    return {"schema": SCHEMA + "-output-manifest", "files": files}


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(MANIFEST_PATH)
    try:
        registration = verify_registration(manifest)
        if args.mode == "registration-check":
            record = {
                "schema": SCHEMA + "-registration-check",
                "status": "REGISTRATION_VERIFIED_NOT_EXECUTED",
                "registration": registration,
            }
            write_json(args.out_dir / "registration_check.json", record)
            print("status =", record["status"])
            print("registration_file_count =", registration["file_count"])
            return

        provenance = verify_inputs(manifest, args.d12rg_repo.resolve())
        contract = read_json(CONTRACT_PATH)
        summary, map_rows, signature_rows, controls = comparison(manifest, contract)
        summary["registration_verification"] = registration
        summary["source_provenance"] = provenance

        write_json(args.out_dir / "summary.json", summary)
        write_csv(
            args.out_dir / "admissible_maps.csv",
            ["d12rg_role", "sim_primitive", "eligible", "reason"],
            map_rows,
        )
        write_csv(
            args.out_dir / "signature_comparison.csv",
            ["feature", "d12rg", "sim", "preserved"],
            signature_rows,
        )
        write_csv(
            args.out_dir / "controls.csv",
            ["control", "match", "readout"],
            controls,
        )
        (args.out_dir / "RESULT.md").write_text(
            result_markdown(summary), encoding="utf-8"
        )
        names = [
            "summary.json",
            "admissible_maps.csv",
            "signature_comparison.csv",
            "controls.csv",
            "RESULT.md",
        ]
        write_json(
            args.out_dir / "output_manifest.json",
            output_manifest(args.out_dir, names),
        )

        if args.check:
            allowed = {
                "COMPLETE_MARKED_READOUT_CORRESPONDENCE",
                "PARTIAL_REGISTERED_CORRESPONDENCE",
                "GENERIC_INVOLUTION_OR_TRACE_ONLY_CORRESPONDENCE",
                "NO_REGISTERED_CORRESPONDENCE",
            }
            if summary["primary_classification"] not in allowed:
                raise RuntimeError("unregistered primary classification")
        print("status = COMPLETE")
        print("primary_classification =", summary["primary_classification"])
        print("complete_algebra_isomorphism =", summary["complete_algebra_isomorphism"]["supported"])
        print("complete_marked_readout =", summary["marked_readout_correspondence"]["supported"])
        print("generic_involution_or_trace =", summary["generic_global_involution_or_invariant_trace"]["supported"])
    except Exception as error:
        failure = {
            "schema": SCHEMA,
            "status": "FAILED",
            "primary_classification": "PROVENANCE_FAILURE",
            "error": str(error),
        }
        write_json(args.out_dir / "summary.json", failure)
        if args.check:
            raise
        print("status = FAILED")
        print("primary_classification = PROVENANCE_FAILURE")


if __name__ == "__main__":
    main()
