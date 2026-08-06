#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 007A Phase 1 registered operator-object definition audit."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA = "siel-experiment-007a-phase1-operator-object-audit-v1"
EXPECTED_RIEMANN_COMMIT = "12759beb5c6acb41b83597dfb77b74cd576d5066"
EXPECTED_RIEMANN_REMOTE = "https://gitlab.com/d12rg/d12rg-riemann.git"
EXPECTED_D12_HASHES = {
    "docs/spectral/s-pr40-paper53-cit-port-rigidity.md":
        "b83e25532628ca6a5651b1ed76990db9d0bb40704c9946af6c7a74f9a5c46f17",
    "docs/gate4/k-pr80-paper53-cit-projectors.md":
        "f2d92561b915181d88e31300289b6af4a6cd6bdb437c4334d5db2d2e62505495",
    "src/d12rg_riemann/spectral_cit_port.py":
        "9e2b76767295160d5bfdd3b14344eca162654ec9d7effd702c72a6fbe49c616c",
    "src/d12rg_riemann/paper53_cit_projectors.py":
        "598a6d8cb04247327718553bb4b487cd00b83b454a76816b8976d819940fa267",
}
EXPECTED_SIO_HASHES = {
    "experiments/006_spontaneous_o3_reentry/PREREGISTRATION.md":
        "9af2aa91c57917507bb79b2a9887fa94ffa509936f96cf8e59f748c19085e212",
    "experiments/006_spontaneous_o3_reentry/TECHNICAL_SPECIFICATION.md":
        "ffc5762656ca7e56ba49f2e45922b40fa70ae0efd24e986709d2fd90f3c3a9f9",
    "experiments/006_spontaneous_o3_reentry/run.py":
        "87e673c09bc1dce5471cf90fa70c9425c5cc2bb669006e473e799415074f9375",
    "experiments/006_spontaneous_o3_reentry/results/summary.json":
        "a7537c103a4a320647863df98de195ca4867e29bc10697bf16881406fb2e6333",
    "experiments/006r_spontaneous_o3_reentry_revised/PREREGISTRATION.md":
        "c40e4270e2d67c313641584b3fe2c4fcc47e10a51ced2049d2697cc2be5fc173",
    "experiments/006r_spontaneous_o3_reentry_revised/TECHNICAL_SPECIFICATION.md":
        "a23907114833f72bb9474924b9e1ac3b198f18372c322678b3511dd3b1465c47",
    "experiments/006r_spontaneous_o3_reentry_revised/run.py":
        "77e785b2f66070bfbe0d489890b399b313a0ff97bc0e8b0a24af0ac25b0d9de7",
    "experiments/006r_spontaneous_o3_reentry_revised/results/summary.json":
        "1d94cd86afe6552e7fc65a6c96de185340ffcb85999c265f30bbcad209e3d51e",
    "experiments/006a_emergent_nonseparable_relational_c/PREREGISTRATION.md":
        "f84c5322d339e6e63b8c7ad0b6b0a8f97fde927928035f6de28181ff34efeaca",
    "experiments/006a_emergent_nonseparable_relational_c/TECHNICAL_SPECIFICATION.md":
        "a36547df0c410aaee8ad75b9f5fc674dee487815811a2db9f74463569931d187",
    "experiments/006a_emergent_nonseparable_relational_c/run.py":
        "8050b5465e5233f8d90f7bae0b7f106dd4232fc0666cef2a165d73516172cd5b",
    "experiments/006a_emergent_nonseparable_relational_c/results/summary.json":
        "ad462bbd4afbea212ae62a9229ec6f1ce167f194a831bfc4480054dcd1f24b16",
}
EXPECTED_BASIS_EXPONENTS = (5, 1, 11, 7, 10, 2, 0)
EXPECTED_CHARACTER_EXPONENTS = (0, 1, 2, 5, 7, 10, 11)
EXPECTED_MINIMAL_POLYNOMIAL = (-1, 2, -1, -1, 1, 1, -2, 1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--riemann-repo", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--registration-manifest",
        default=HERE / "registration_manifest.json",
        type=Path,
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_remote(value: str) -> str:
    return value.strip().removesuffix("/").removesuffix(".git")


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo, text=True
    ).strip()


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def serial(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [serial(item) for item in value]
    if isinstance(value, list):
        return [serial(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serial(item) for key, item in value.items()}
    return value


def write_json(path: Path, value):
    path.write_text(
        json.dumps(serial(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_registration_manifest(path: Path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["registration_sha256"].items():
        target = ROOT / relative
        if not target.is_file() or sha256_file(target) != expected:
            mismatches.append(relative)
    require(not mismatches, "registration mismatch: " + ", ".join(mismatches))
    return manifest


def verify_sources(riemann_repo: Path):
    repo = riemann_repo.resolve()
    require(repo.is_dir(), "missing Riemann repository")
    commit = git_output(repo, "rev-parse", "HEAD")
    remote = git_output(repo, "remote", "get-url", "origin")
    require(commit == EXPECTED_RIEMANN_COMMIT, "Riemann commit mismatch")
    require(
        normalized_remote(remote) == normalized_remote(EXPECTED_RIEMANN_REMOTE),
        "Riemann remote mismatch",
    )
    source_hashes = {}
    for relative, expected in EXPECTED_D12_HASHES.items():
        path = repo / relative
        observed = sha256_file(path)
        require(observed == expected, "D12RG source mismatch: " + relative)
        source_hashes[relative] = observed
    sio_hashes = {}
    for relative, expected in EXPECTED_SIO_HASHES.items():
        path = ROOT / relative
        observed = sha256_file(path)
        require(observed == expected, "SIO source mismatch: " + relative)
        sio_hashes[relative] = observed
    return {
        "riemann_repository": str(repo),
        "riemann_commit": commit,
        "riemann_remote": remote,
        "d12rg_source_hashes": source_hashes,
        "sio_source_hashes": sio_hashes,
    }


def flatten(matrix):
    return tuple(value for row in matrix for value in row)


def matrix_rank(vectors):
    if not vectors:
        return 0
    work = [list(map(Fraction, row)) for row in zip(*vectors)]
    rows = len(work)
    columns = len(work[0])
    rank = 0
    for column in range(columns):
        pivot = next(
            (row for row in range(rank, rows) if work[row][column] != 0),
            None,
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        value = work[rank][column]
        work[rank] = [item / value for item in work[rank]]
        for row in range(rows):
            if row == rank:
                continue
            factor = work[row][column]
            if factor:
                work[row] = [
                    left - factor * right
                    for left, right in zip(work[row], work[rank])
                ]
        rank += 1
        if rank == rows:
            break
    return rank


def linear_coordinates(basis, target):
    columns = [flatten(matrix) for matrix in basis]
    rhs = flatten(target)
    system = [
        [columns[column][row] for column in range(len(columns))] + [rhs[row]]
        for row in range(len(rhs))
    ]
    pivot_row = 0
    pivots = []
    for column in range(len(columns)):
        pivot = next(
            (row for row in range(pivot_row, len(system)) if system[row][column]),
            None,
        )
        if pivot is None:
            continue
        system[pivot_row], system[pivot] = system[pivot], system[pivot_row]
        value = system[pivot_row][column]
        system[pivot_row] = [item / value for item in system[pivot_row]]
        for row in range(len(system)):
            if row == pivot_row:
                continue
            factor = system[row][column]
            if factor:
                system[row] = [
                    left - factor * right
                    for left, right in zip(system[row], system[pivot_row])
                ]
        pivots.append(column)
        pivot_row += 1
    require(len(pivots) == len(columns), "basis is not independent")
    for row in system:
        require(any(row[:-1]) or row[-1] == 0, "target is outside basis span")
    result = [Fraction(0) for unused in columns]
    for row, column in enumerate(pivots):
        result[column] = system[row][-1]
    return tuple(result)


def audit_d12rg(riemann_repo: Path):
    sys.path.insert(0, str(riemann_repo.resolve() / "src"))
    module = importlib.import_module("d12rg_riemann.spectral_cit_port")
    basis_exponents = tuple(module.PAPER53_BASIS_EXPONENTS)
    character_exponents = tuple(module.PAPER53_CHARACTER_EXPONENTS)
    minimal = tuple(module.PAPER53_MINIMAL_POLYNOMIAL)
    matrices = tuple(module.paper53_source_matrices())
    generated = tuple(module.paper53_generated_matrices())
    generator = module.paper53_generator()
    identity = module.identity_matrix(7)
    checks = {
        "basis_has_seven_elements": len(matrices) == 7,
        "basis_exponents_exact": basis_exponents == EXPECTED_BASIS_EXPONENTS,
        "character_exponents_exact": character_exponents == EXPECTED_CHARACTER_EXPONENTS,
        "minimal_polynomial_exact": minimal == EXPECTED_MINIMAL_POLYNOMIAL,
        "printed_matrices_are_registered_powers": matrices == generated,
        "identity_is_final_basis_matrix": matrices[-1] == identity,
        "generator_has_exact_order_twelve": (
            module.matrix_power(generator, 12) == identity
            and all(module.matrix_power(generator, power) != identity for power in range(1, 12))
        ),
        "minimal_polynomial_annihilates_generator": (
            module.matrix_polynomial(generator, minimal) == module.zero_matrix(7)
        ),
        "basis_rank_is_seven": matrix_rank([flatten(matrix) for matrix in matrices]) == 7,
    }
    products = []
    all_products_in_span = True
    basis_set_closed = True
    for left_index, left in enumerate(matrices):
        for right_index, right in enumerate(matrices):
            product = module.matrix_multiply(left, right)
            coefficients = linear_coordinates(matrices, product)
            reconstructed = module.zero_matrix(7)
            for coefficient, matrix in zip(coefficients, matrices):
                reconstructed = module.matrix_add(
                    reconstructed,
                    module.matrix_scale(matrix, coefficient),
                )
            in_span = reconstructed == product
            all_products_in_span &= in_span
            single_basis = sum(value != 0 for value in coefficients) == 1 and 1 in coefficients
            basis_set_closed &= single_basis
            products.append({
                "left_basis_index": left_index + 1,
                "right_basis_index": right_index + 1,
                "left_exponent": basis_exponents[left_index],
                "right_exponent": basis_exponents[right_index],
                "coefficients": ";".join(str(value) for value in coefficients),
                "product_in_linear_span": in_span,
                "product_is_one_basis_element": single_basis,
            })
    checks["all_basis_products_in_seven_dimensional_span"] = all_products_in_span
    checks["seven_printed_basis_matrices_set_closed"] = basis_set_closed
    require(all(value for key, value in checks.items() if key != "seven_printed_basis_matrices_set_closed"), "D12RG algebra audit failed")
    require(not basis_set_closed, "unexpected set closure of seven basis matrices")
    return {
        "classification": "SEVEN_DIMENSIONAL_UNITAL_OPERATOR_ALGEBRA",
        "basis_exponents": basis_exponents,
        "character_exponents": character_exponents,
        "minimal_polynomial": minimal,
        "ambient_generator_order": 12,
        "vector_space_dimension": 7,
        "basis_matrix_count": 7,
        "set_closed_under_matrix_product": basis_set_closed,
        "linear_span_closed_under_matrix_product": all_products_in_span,
        "reciprocal_exponent_pairs": ((1, 11), (2, 10), (5, 7)),
        "identity_exponent": 0,
        "checks": checks,
    }, products


def ast_inventory(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments = []
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    assignments.append(target.id)
    return {"assignments": sorted(assignments), "functions": sorted(functions)}


def audit_sio_sources():
    run_paths = [
        ROOT / "experiments/006_spontaneous_o3_reentry/run.py",
        ROOT / "experiments/006r_spontaneous_o3_reentry_revised/run.py",
        ROOT / "experiments/006a_emergent_nonseparable_relational_c/run.py",
    ]
    inventories = {str(path.relative_to(ROOT)): ast_inventory(path) for path in run_paths}
    all_assignments = {name.lower() for data in inventories.values() for name in data["assignments"]}
    all_functions = {name.lower() for data in inventories.values() for name in data["functions"]}
    documents = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8").lower()
        for relative in EXPECTED_SIO_HASHES
        if relative.endswith(".md")
    )
    operational_checks = {
        "relation_component_extractor_present": (
            "directed_component_from_states" in all_functions or "synergy" in all_functions
        ),
        "recurrent_update_present": "advance" in documents or "re-entry" in documents,
        "cross_pair_exchange_present": "cross-pair" in documents,
        "bilateral_effect_present": "bilateral" in documents,
        "nonseparable_component_present": "nonseparable" in documents,
    }
    algebra_definition_checks = {
        "finite_primitive_operator_set_declared": any(
            "operator" in name and ("primitive" in name or "basis" in name)
            for name in all_assignments
        ),
        "operator_domains_and_codomains_declared": (
            "operator domain" in documents and "codomain" in documents
        ),
        "executable_operator_composition_declared": any(
            "compose" in name and ("operator" in name or "action" in name)
            for name in all_functions
        ),
        "inadmissible_compositions_declared": (
            "inadmissible composition" in documents or "undefined composition" in documents
        ),
        "identity_and_inverse_rules_declared": (
            "identity operator" in documents and "inverse operator" in documents
        ),
        "canonical_operator_table_rule_declared": (
            "canonical operator" in documents and "operator table" in documents
        ),
    }
    require(all(operational_checks.values()), "frozen SIO operational sources are incomplete")
    algebra_complete = all(algebra_definition_checks.values())
    classification = (
        "SIO_SOURCE_DEFINES_UNIQUE_OPERATOR_ALGEBRA"
        if algebra_complete
        else "SIO_OPERATOR_ALGEBRA_UNDERDEFINED"
    )
    return {
        "classification": classification,
        "operational_checks": operational_checks,
        "algebra_definition_checks": algebra_definition_checks,
        "source_inventories": inventories,
    }


def classify(d12rg, sio):
    if d12rg["classification"] != "SEVEN_DIMENSIONAL_UNITAL_OPERATOR_ALGEBRA":
        return "D12RG_TARGET_UNDERDEFINED"
    if sio["classification"] != "SIO_SOURCE_DEFINES_UNIQUE_OPERATOR_ALGEBRA":
        return "D12_TARGET_DEFINED_SIO_EXTRACTION_UNDERDEFINED"
    return "READY_FOR_HASH_SEPARATED_INDEPENDENT_COMPARISON"


def render_result(summary):
    d12 = summary["d12rg_operator_object"]
    sio = summary["sio_operator_object"]
    return "\n".join([
        "# Experiment 007A Phase 1 Result",
        "",
        "## Primary classification",
        "",
        f"**{summary['primary_classification']}**",
        "",
        "## D12RG target",
        "",
        f"Classification: `{d12['classification']}`.",
        "",
        "The seven printed matrices are a basis of a seven-dimensional unital operator algebra. They are selected powers of one ambient order-12 generator, but the seven-element basis set is not closed as a set under ordinary matrix multiplication. Its linear span is closed, and products reduce exactly to linear combinations of the seven basis matrices.",
        "",
        "## SIO source boundary",
        "",
        f"Classification: `{sio['classification']}`.",
        "",
        "The frozen 006, 006R, and 006A sources define relational-component extraction, recurrent transport, cross-pair exchange, nonseparability, and bilateral effects. They do not yet define one finite primitive operator basis with typed domains, codomains, composition, inadmissible cases, identity/inverse rules, and canonicalisation.",
        "",
        "## Consequence",
        "",
        "A hash-separated SIO-to-D12RG algebra comparison cannot yet be executed without first registering a constructed SIO operator-extraction rule. The next phase must define that rule, its primitive-removal and primitive-addition robustness variants, its witness set, complete failure routing, and the hash-before-load comparison boundary.",
        "",
        "This is an operator-object definition result. It is not a Class 2, O3, or cross-framework isomorphism result.",
        "",
    ])


def main():
    args = parse_args()
    require(not args.out_dir.exists(), "output directory already exists")
    registration = verify_registration_manifest(args.registration_manifest)

    # The SIO inventory and its digest are fixed before D12RG is imported.
    sio = audit_sio_sources()
    sio_table_digest = hashlib.sha256(
        json.dumps(serial(sio), sort_keys=True).encode("utf-8")
    ).hexdigest()

    provenance = verify_sources(args.riemann_repo)
    d12rg, product_rows = audit_d12rg(args.riemann_repo)
    primary = classify(d12rg, sio)
    summary = {
        "schema": SCHEMA,
        "status": "COMPLETE",
        "primary_classification": primary,
        "registration_verified": True,
        "registration": registration,
        "provenance": provenance,
        "independence_boundary": {
            "sio_inventory_generated_before_d12rg_import": True,
            "sio_inventory_sha256": sio_table_digest,
            "d12rg_loaded_only_after_sio_inventory_hash": True,
        },
        "d12rg_operator_object": d12rg,
        "sio_operator_object": sio,
        "next_phase_gate": (
            "Register a constructed SIO operator basis and complete typed product law before comparison."
            if primary == "D12_TARGET_DEFINED_SIO_EXTRACTION_UNDERDEFINED"
            else "Proceed according to the registered classification."
        ),
    }
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "d12_basis_product_structure.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(product_rows[0]))
        writer.writeheader()
        writer.writerows(product_rows)
    write_json(args.out_dir / "summary.json", summary)
    (args.out_dir / "RESULT.md").write_text(render_result(summary), encoding="utf-8")
    output_names = ("d12_basis_product_structure.csv", "summary.json", "RESULT.md")
    write_json(
        args.out_dir / "output_manifest.json",
        {
            "schema": SCHEMA,
            "files": {name: sha256_file(args.out_dir / name) for name in output_names},
        },
    )
    print(json.dumps({
        "status": "COMPLETE",
        "primary_classification": primary,
        "d12rg_operator_object": d12rg["classification"],
        "sio_operator_object": sio["classification"],
    }, indent=2))


if __name__ == "__main__":
    main()
