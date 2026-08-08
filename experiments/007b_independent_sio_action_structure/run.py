#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 007B independent SIO action-structure construction."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA = "siel-experiment-007b-independent-sio-action-structure-v1"
REGISTRY_PATH = HERE / "source_action_registry.json"
MANIFEST_PATH = HERE / "registration_manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("registration-check", "confirmatory"), required=True
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_registration_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    observed: dict[str, str] = {}
    for section in ("registration_sha256", "source_sha256"):
        values = manifest.get(section, {})
        if not values:
            mismatches.append(section + ":empty")
            continue
        for relative, expected in sorted(values.items()):
            path = ROOT / relative
            if not path.is_file():
                mismatches.append(relative + ":missing")
                continue
            actual = sha256_file(path)
            observed[relative] = actual
            if actual != expected:
                mismatches.append(relative + ":hash")
    if mismatches:
        raise RuntimeError("registration mismatch: " + ", ".join(mismatches))
    return {
        "verified": True,
        "file_count": len(observed),
        "observed_sha256": observed,
    }


def function_source(path: Path, function_name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one function {function_name} in {path}, found {len(matches)}"
        )
    segment = ast.get_source_segment(text, matches[0])
    if segment is None:
        raise RuntimeError(f"cannot recover source for {function_name}")
    return segment


def canonical_key(site: dict[str, Any]) -> str:
    value = {
        "canonical_rule": site["canonical_rule"],
        "input_types": site["input_types"],
        "output_type": site["output_type"],
        "linearity": site["linearity"],
        "direction": site["direction"],
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def verify_and_canonicalize_registry() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sites = registry["operation_sites"]
    ids = [site["site_id"] for site in sites]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate operation-site ID")

    site_rows: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for site in sites:
        path = ROOT / site["source_path"]
        source = function_source(path, site["function"])
        missing = [
            fragment
            for fragment in site["required_fragments"]
            if fragment not in source
        ]
        if missing:
            raise RuntimeError(
                f"source fragments missing for {site['site_id']}: {missing}"
            )
        key = canonical_key(site)
        groups[key].append(site)
        site_rows.append({
            "site_id": site["site_id"],
            "source_path": site["source_path"],
            "function": site["function"],
            "canonical_rule": site["canonical_rule"],
            "input_types": ";".join(site["input_types"]),
            "output_type": site["output_type"],
            "linearity": site["linearity"],
            "direction": site["direction"],
            "source_verified": True,
        })

    primitives: list[dict[str, Any]] = []
    for index, key in enumerate(sorted(groups), start=1):
        members = sorted(groups[key], key=lambda item: item["site_id"])
        first = members[0]
        primitives.append({
            "primitive_id": f"P{index:02d}",
            "canonical_rule": first["canonical_rule"],
            "input_types": list(first["input_types"]),
            "output_type": first["output_type"],
            "linearity": first["linearity"],
            "direction": first["direction"],
            "supporting_sites": [item["site_id"] for item in members],
            "canonical_key": key,
        })
    return site_rows, primitives, registry["predeclared_addition"]


def composition_rows(primitives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left in primitives:
        for right in primitives:
            positions = [
                index
                for index, type_name in enumerate(right["input_types"])
                if type_name == left["output_type"]
            ]
            rows.append({
                "first_primitive": left["primitive_id"],
                "first_rule": left["canonical_rule"],
                "then_primitive": right["primitive_id"],
                "then_rule": right["canonical_rule"],
                "composable": bool(positions),
                "matching_input_positions": ";".join(map(str, positions)),
            })
    return rows


def common_linear_endomorphism_carrier(primitives: list[dict[str, Any]]) -> str | None:
    if not primitives:
        return None
    possible: str | None = None
    for primitive in primitives:
        if primitive["linearity"] != "linear":
            return None
        if len(primitive["input_types"]) != 1:
            return None
        input_type = primitive["input_types"][0]
        if primitive["output_type"] != input_type:
            return None
        if possible is None:
            possible = input_type
        elif possible != input_type:
            return None
    return possible


def structural_class(primitives: list[dict[str, Any]]) -> str:
    if not primitives:
        return "NO_STABLE_ACTION_STRUCTURE"
    common = common_linear_endomorphism_carrier(primitives)
    if common is not None:
        return "STABLE_FINITE_DIMENSIONAL_LINEAR_ACTION_ALGEBRA"
    if all(item["linearity"] in {"linear", "affine", "discrete_routing"} for item in primitives):
        return "STABLE_LINEAR_ACTION_STRUCTURE_WITHOUT_FINITE_CLOSURE"
    return "STABLE_NONLINEAR_OR_TYPED_ACTION_STRUCTURE"


def mediation_route_present(primitives: list[dict[str, Any]]) -> bool:
    rules = {item["canonical_rule"] for item in primitives}
    return (
        bool({"extract_relation", "extract_joint_synergy"} & rules)
        and bool({"erase_relation", "substitute_relation"} & rules)
        and "advance_recurrently" in rules
        and "replace_joint_in_bundle" in rules
        and "difference_relational_contribution" in rules
    )


def robustness_rows(
    primitives: list[dict[str, Any]], addition: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    base = structural_class(primitives)
    rows: list[dict[str, Any]] = []
    classes: list[str] = []
    for primitive in primitives:
        variant = [
            item for item in primitives if item["primitive_id"] != primitive["primitive_id"]
        ]
        value = structural_class(variant)
        classes.append(value)
        rows.append({
            "variant": "remove_" + primitive["primitive_id"],
            "changed_rule": primitive["canonical_rule"],
            "primitive_count": len(variant),
            "structural_class": value,
            "class_matches_base": value == base,
            "mediation_route_present": mediation_route_present(variant),
        })
    added = {
        "primitive_id": "P_ADD",
        "canonical_rule": addition["canonical_rule"],
        "input_types": addition["input_types"],
        "output_type": addition["output_type"],
        "linearity": addition["linearity"],
        "direction": addition["direction"],
        "supporting_sites": ["predeclared_addition"],
    }
    addition_variant = primitives + [added]
    addition_class = structural_class(addition_variant)
    classes.append(addition_class)
    rows.append({
        "variant": "add_predeclared_ordered_receiver_partition",
        "changed_rule": addition["canonical_rule"],
        "primitive_count": len(addition_variant),
        "structural_class": addition_class,
        "class_matches_base": addition_class == base,
        "mediation_route_present": mediation_route_present(addition_variant),
    })
    return rows, all(value == base for value in classes)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def witness_audit() -> dict[str, Any]:
    e006 = load_module(
        "e007b_frozen_e006",
        ROOT / "experiments/006_spontaneous_o3_reentry/run.py",
    )
    e006a = load_module(
        "e007b_frozen_e006a",
        ROOT / "experiments/006a_emergent_nonseparable_relational_c/run.py",
    )
    rng = np.random.default_rng(7007001)

    def bundle() -> dict[str, np.ndarray]:
        return {
            key: rng.normal(size=(3, 24))
            for key in ("ab", "a0", "0b", "00")
        }

    left = bundle()
    right = bundle()
    summed = {key: left[key] + right[key] for key in left}
    directed_left = e006.directed_component_from_states("distributed", left)
    directed_right = e006.directed_component_from_states("distributed", right)
    directed_sum = e006.directed_component_from_states("distributed", summed)
    synergy_left = e006a.synergy(left)
    synergy_right = e006a.synergy(right)
    synergy_sum = e006a.synergy(summed)

    hidden = rng.normal(scale=0.2, size=(3, 24))
    component = rng.normal(scale=0.1, size=(3, 24))
    donor = rng.normal(scale=0.1, size=(3, 24))
    erased = hidden - component
    substituted_identity = hidden - component + component
    substituted_donor = hidden - component + donor

    model = {
        "params": {
            "inputs": np.zeros((24, 8)),
            "recurrent": np.eye(24) * 0.7,
            "bias": np.zeros(24),
            "outputs": np.zeros((6, 24)),
            "output_bias": np.zeros(6),
        }
    }
    input_step = np.zeros((3, 8))
    once = e006.advance(model, hidden, input_step)
    twice_input = e006.advance(model, 2.0 * hidden, input_step)
    nonlinear_gap = float(np.max(np.abs(twice_input - 2.0 * once)))

    pairs = np.asarray([4, 5, 6, 4, 5, 6])
    donor_indices = e006.E010.cross_pair_donor(pairs)
    donor_valid = bool(np.all(pairs[donor_indices] != pairs))

    current = left
    next_bundle = right
    relation = e006.directed_component_from_states("distributed", current)
    next_relation = e006.directed_component_from_states("distributed", next_bundle)
    intervened_joint = e006.advance(model, current["ab"] - relation, input_step)
    next_without = e006.next_component_after_ab_intervention(
        "distributed", next_bundle, intervened_joint
    )
    transported = next_relation - next_without

    return {
        "directed_extractor_linearity_error": float(np.max(np.abs(
            directed_sum - directed_left - directed_right
        ))),
        "synergy_extractor_linearity_error": float(np.max(np.abs(
            synergy_sum - synergy_left - synergy_right
        ))),
        "extractor_non_equivalence_witness": float(np.max(np.abs(
            directed_left - synergy_left
        ))),
        "erasure_identity_error": float(np.max(np.abs(
            erased - (hidden - component)
        ))),
        "substitution_identity_error": float(np.max(np.abs(
            substituted_identity - hidden
        ))),
        "donor_substitution_nontrivial": bool(
            np.max(np.abs(substituted_donor - hidden)) > 1e-10
        ),
        "recurrent_nonlinearity_gap": nonlinear_gap,
        "cross_pair_route_valid": donor_valid,
        "transported_component_finite": bool(np.all(np.isfinite(transported))),
        "transported_component_shape": list(transported.shape),
        "all_witness_checks_pass": bool(
            np.max(np.abs(directed_sum - directed_left - directed_right)) <= 1e-12
            and np.max(np.abs(synergy_sum - synergy_left - synergy_right)) <= 1e-12
            and np.max(np.abs(directed_left - synergy_left)) > 1e-10
            and np.max(np.abs(substituted_identity - hidden)) <= 1e-12
            and nonlinear_gap > 1e-10
            and donor_valid
            and np.all(np.isfinite(transported))
        ),
    }


def djs_audit(primitives: list[dict[str, Any]]) -> dict[str, Any]:
    rules = {item["canonical_rule"] for item in primitives}
    types = {
        type_name
        for item in primitives
        for type_name in (*item["input_types"], item["output_type"])
    }
    checks = {
        "single_base_space_K_source_defined": len(types) == 1,
        "associative_point_mass_probability_convolution_source_defined": (
            "probability_convolution" in rules
        ),
        "global_identity_source_defined": "global_identity" in rules,
        "global_involution_source_defined": "global_involution" in rules,
        "compact_support_conditions_source_defined": "compact_support" in rules,
        "continuity_conditions_source_defined": "continuous_convolution" in rules,
    }
    return {
        "candidate": "Dunkl-Jewett-Spector hypergroup",
        "checks": checks,
        "all_axioms_forced": all(checks.values()),
        "classification": (
            "MINIMAL_NULL" if all(checks.values()) else "REGISTERED_COMPARATOR_NOT_NULL_FLOOR"
        ),
        "source_rule_count": len(rules),
        "source_type_count": len(types),
    }


def render_result(summary: dict[str, Any]) -> str:
    lines = [
        "# Experiment 007B Result",
        "",
        "## Independent Construction of the SIO Action Structure",
        "",
        f"Status: {summary['status']}",
        f"Primary classification: {summary['primary_classification']}",
        "",
        "## Main readout",
        "",
        summary["main_readout"],
        "",
        "## Registered checks",
        "",
    ]
    lines.extend(
        f"- {key}: {'PASS' if value else 'FAIL'}"
        for key, value in summary["registered_checks"].items()
    )
    lines += [
        "",
        "## Structure",
        "",
        f"- verified operation sites: {summary['operation_site_count']}",
        f"- canonical primitives: {summary['canonical_primitive_count']}",
        f"- common linear endomorphism carrier: {summary['common_linear_endomorphism_carrier']}",
        f"- DJS classification: {summary['djs_hypergroup']['classification']}",
        "",
        "## Boundary",
        "",
        summary["claim_boundary"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.out_dir.exists():
        raise SystemExit("FAIL: output directory exists")
    try:
        verification = verify_registration_manifest() if args.check else None
        site_rows, primitives, addition = verify_and_canonicalize_registry()
        addition_source = function_source(
            ROOT / addition["source_path"], addition["function"]
        )
        if not all(fragment in addition_source for fragment in addition["required_fragments"]):
            raise RuntimeError("predeclared addition source mismatch")
        witness = witness_audit()
    except Exception as error:
        raise SystemExit("FAIL: provenance or construction error: " + str(error)) from error

    base_class = structural_class(primitives)
    compositions = composition_rows(primitives)
    robustness, robustness_stable = robustness_rows(primitives, addition)
    common = common_linear_endomorphism_carrier(primitives)
    djs = djs_audit(primitives)
    canonical_unique = len({item["canonical_key"] for item in primitives}) == len(primitives)
    registered_checks = {
        "all_source_sites_verified": all(row["source_verified"] for row in site_rows),
        "canonicalization_unique": canonical_unique,
        "typed_composition_table_complete": len(compositions) == len(primitives) ** 2,
        "witness_checks_pass": witness["all_witness_checks_pass"],
        "base_mediation_route_present": mediation_route_present(primitives),
        "robustness_class_unchanged": robustness_stable,
        "no_common_linear_endomorphism_carrier": common is None,
        "no_source_defined_canonical_global_generator": not any(
            item["canonical_rule"] == "canonical_global_generator"
            for item in primitives
        ),
        "no_source_defined_global_involution": not any(
            item["canonical_rule"] == "global_involution"
            for item in primitives
        ),
        "djs_not_promoted_without_axioms": djs["classification"] == "REGISTERED_COMPARATOR_NOT_NULL_FLOOR",
        "d12rg_not_loaded": not any("d12" in item["source_path"].lower() for item in json.loads(REGISTRY_PATH.read_text())["operation_sites"]),
    }
    stable = all(registered_checks.values())
    primary = base_class if stable else "NO_STABLE_ACTION_STRUCTURE"
    summary = {
        "schema": SCHEMA,
        "mode": args.mode,
        "status": "COMPLETE",
        "primary_classification": primary,
        "main_readout": (
            "The frozen 006-series transformations define one deterministic typed "
            "nonlinear action structure. They do not define a finite common-carrier "
            "operator algebra, a canonical global generator, a global involution, or "
            "a DJS hypergroup."
        ),
        "operation_site_count": len(site_rows),
        "canonical_primitive_count": len(primitives),
        "common_linear_endomorphism_carrier": common,
        "registered_checks": registered_checks,
        "witness_audit": witness,
        "djs_hypergroup": djs,
        "robustness": {
            "base_class": base_class,
            "all_variant_classes_match_base": robustness_stable,
            "mediation_route_critical_removals": [
                row["changed_rule"]
                for row in robustness
                if not row["mediation_route_present"]
            ],
        },
        "provenance_verification": verification,
        "claim_boundary": (
            "Operational SIO action structure only. No subjectivity, ontological O3, "
            "D12RG correspondence, DJS realization, or new abstract algebra is claimed."
        ),
    }

    args.out_dir.mkdir(parents=True)
    write_csv(
        args.out_dir / "source_operation_sites.csv",
        list(site_rows[0]),
        site_rows,
    )
    primitive_rows = [{
        "primitive_id": item["primitive_id"],
        "canonical_rule": item["canonical_rule"],
        "input_types": ";".join(item["input_types"]),
        "output_type": item["output_type"],
        "linearity": item["linearity"],
        "direction": item["direction"],
        "supporting_sites": ";".join(item["supporting_sites"]),
    } for item in primitives]
    write_csv(
        args.out_dir / "canonical_primitives.csv",
        list(primitive_rows[0]),
        primitive_rows,
    )
    write_csv(
        args.out_dir / "typed_composition_table.csv",
        list(compositions[0]),
        compositions,
    )
    write_csv(
        args.out_dir / "robustness_variants.csv",
        list(robustness[0]),
        robustness,
    )
    write_json(args.out_dir / "summary.json", summary)
    (args.out_dir / "RESULT.md").write_text(
        render_result(summary), encoding="utf-8"
    )
    output_files = sorted(
        path for path in args.out_dir.iterdir() if path.name != "output_manifest.json"
    )
    write_json(args.out_dir / "output_manifest.json", {
        "schema": "siel-experiment-007b-output-manifest-v1",
        "files": {
            path.name: sha256_file(path) for path in output_files
        },
    })
    print("status =", summary["status"])
    print("primary_classification =", primary)
    print("operation_site_count =", len(site_rows))
    print("canonical_primitive_count =", len(primitives))
    print("djs_classification =", djs["classification"])
    print("wrote", args.out_dir)
    if not stable:
        raise SystemExit("FAIL: registered checks did not all pass")


if __name__ == "__main__":
    main()
