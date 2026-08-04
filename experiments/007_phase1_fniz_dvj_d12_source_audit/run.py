#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the preregistered Experiment 007 Phase 1 source audit."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
EXPECTED_RIEMANN_COMMIT = "12759beb5c6acb41b83597dfb77b74cd576d5066"
EXPECTED_RIEMANN_REMOTE = "https://gitlab.com/d12rg/d12rg-riemann.git"
EXPECTED_ADVAITA_COMMIT = "375d25e834208cf9a92154be9e51d72f09175a8f"
EXPECTED_ADVAITA_PATH = (
    "z12cft-cft/knowledge/paper7.5/"
    "Advaita Canonical Database Expanded Operator Form LaTeX Source.txt"
)
EXPECTED_ADVAITA_SHA256 = (
    "ebb0edfc0f4533a25eaf05adeba98aa0a5f9ded32f5a246acd636c6e51481630"
)
EXPECTED_SOURCE_HASHES = {
    "src/d12rg_riemann/signed_fniz_xi.py":
        "be7868799c781c62eb8adec424e6752b78e07a84c4e25fa86e45060e067045c5",
    "src/d12rg_riemann/spectral_fniz_symmetry_audit.py":
        "be010b68ea8f620b7b6dd57aea1495a4d1a1583c5c7420317ff4b391be064e6b",
    "src/d12rg_riemann/spectral_maya_fniz.py":
        "32a6be8e33c063649b0d5493c4fe46a6ffdfa680f39b67b7b906d808493faa0a",
    "src/d12rg_riemann/spectral_cit_holonomy.py":
        "4c0114ba440c7b572f66cf27b3d69fe397a3ea8c54f60b7ef0c60305dc83b349",
    "src/d12rg_riemann/spectral_cit_moving.py":
        "ff6dc3fa0fdef313ff65564f06933d10ae307fa7fa75fec5b8cf984e0551b97f",
    "src/d12rg_riemann/spectral_dvj.py":
        "9dc5c1ede19b2f45a63c8a2cc04611a1187dfc01ff93826fd6622d3ba684f4c2",
    "src/d12rg_riemann/spectral_dvj_transfer.py":
        "91562caf97a6800ad5e8a622d786772d28a3c5dc7e9e7bf96ae4d6a9922be2d4",
    "docs/gate4/k-pr84-signed-fniz-xi-endpoint-closure.md":
        "9b7f1ee676603077c5f75cd9ab4a82890e5b64ceb33f5228c7532d3668cf1662",
    "docs/spectral/s-pr41-full-d12-twisted-cit-holonomy.md":
        "dfcef8937257146eb7456526c7ab6d0e32075ed600628627f574b4cccad1e6f1",
    "docs/spectral/s-pr42-moving-projector-positive-kernel.md":
        "8b5a3191d13f5fa2a7fd53b8ff73ad2061dde31b7b2dfd8031dbdcf1b53aa4c7",
}
DVJ_PARAMETERS = ("0.5", "1.0", "2.0", "5.0")
MP_DPS = 80
ROOT_DPS = 90
TOLERANCE_TEXT = "1e-40"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--riemann-repo", required=True)
    parser.add_argument("--advaita-file", required=True)
    parser.add_argument(
        "--out-dir",
        default=str(EXPERIMENT_DIR / "results"),
    )
    parser.add_argument(
        "--registration-manifest",
        default=str(EXPERIMENT_DIR / "registration_manifest.json"),
    )
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(repo, *arguments):
    return subprocess.check_output(
        ["git", *arguments], cwd=repo, text=True
    ).strip()


def normalized_remote(url):
    return str(url).removesuffix("/").removesuffix(".git")


def serial(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if value.__class__.__module__.startswith("mpmath"):
        if value.__class__.__name__ == "mpc":
            return {"real": str(value.real), "imag": str(value.imag)}
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return [serial(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serial(item) for key, item in value.items()}
    return str(value)


def write_json(path, payload):
    Path(path).write_text(
        json.dumps(serial(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path, fieldnames, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_registration_manifest(path):
    manifest_path = Path(path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for relative, expected in manifest["registration_sha256"].items():
        target = REPO_ROOT / relative
        observed = sha256_file(target)
        require(observed == expected, "registration hash mismatch: " + relative)
        rows.append({
            "layer": "registration",
            "item": relative,
            "status": "PASS",
            "detail": observed,
        })
    return manifest, rows


def verify_sources(riemann_repo, advaita_file):
    repo = Path(riemann_repo).resolve()
    advaita = Path(advaita_file).resolve()
    require((repo / ".git").exists(), "Riemann path is not a Git checkout")
    require(advaita.is_file(), "Advaita source file is missing")

    commit = git_output(repo, "rev-parse", "HEAD")
    remote = git_output(repo, "remote", "get-url", "origin")
    dirty = git_output(repo, "status", "--porcelain")
    require(commit == EXPECTED_RIEMANN_COMMIT, "Riemann commit mismatch")
    require(
        normalized_remote(remote) == normalized_remote(EXPECTED_RIEMANN_REMOTE),
        "Riemann remote mismatch",
    )
    require(not dirty, "Riemann source checkout is dirty")

    rows = [
        {"layer": "provenance", "item": "riemann_commit", "status": "PASS", "detail": commit},
        {"layer": "provenance", "item": "riemann_remote", "status": "PASS", "detail": remote},
        {"layer": "provenance", "item": "riemann_clean", "status": "PASS", "detail": "true"},
    ]
    observed_hashes = {}
    for relative, expected in EXPECTED_SOURCE_HASHES.items():
        target = repo / relative
        require(target.is_file(), "missing Riemann source: " + relative)
        observed = sha256_file(target)
        require(observed == expected, "Riemann source hash mismatch: " + relative)
        observed_hashes[relative] = observed
        rows.append({
            "layer": "provenance",
            "item": relative,
            "status": "PASS",
            "detail": observed,
        })

    advaita_hash = sha256_file(advaita)
    require(advaita_hash == EXPECTED_ADVAITA_SHA256, "Advaita source hash mismatch")
    rows.append({
        "layer": "provenance",
        "item": EXPECTED_ADVAITA_PATH,
        "status": "PASS",
        "detail": advaita_hash,
    })
    return repo, advaita, rows, observed_hashes


def audit_advaita(advaita_file):
    text = Path(advaita_file).read_text(encoding="utf-8-sig")
    lower = text.lower()
    checks = {
        "four_operations_named": all(
            word in lower
            for word in ("addition", "subtraction", "multiplication", "division")
        ),
        "operator_history_is_data": "operator history is data" in lower,
        "restoration_work_explicit": (
            "full recovered rule set still requires additional restoration work"
            in lower
        ),
        "carrier_pair_equation_present": "x &= (a,b)" in lower,
        "integration_specific_derivation_present": (
            "integration" in lower
            and "subtraction" in lower
            and "division" in lower
        ),
        "fniz_named": "fniz" in lower,
        "dvj_named": "dvj" in lower,
        "d12_named": "d12" in lower,
        "deck_named": "deck" in lower,
    }
    require(checks["four_operations_named"], "Advaita four-operation statement missing")
    require(checks["operator_history_is_data"], "Advaita history rule missing")
    require(checks["restoration_work_explicit"], "Advaita restoration boundary missing")
    require(checks["carrier_pair_equation_present"], "Advaita carrier equation missing")
    return checks


def audit_fniz(repo):
    sys.path.insert(0, str(repo / "src"))
    from d12rg_riemann.signed_fniz_xi import (
        BASE_OPERATIONS,
        SIGNED_FNIZ_OCTET,
        formal_reciprocal,
        negate_state,
        signed_add,
        signed_divide,
        signed_fniz_xi_theorem,
        signed_multiply,
        signed_subtract,
    )

    theorem = signed_fniz_xi_theorem()
    subtraction_rows = []
    division_rows = []
    for left in SIGNED_FNIZ_OCTET:
        for right in SIGNED_FNIZ_OCTET:
            subtract_exact = (
                signed_subtract(left, right)
                == signed_add(left, negate_state(right))
            )
            divide_exact = (
                signed_divide(left, right)
                == signed_multiply(left, formal_reciprocal(right))
            )
            subtraction_rows.append(subtract_exact)
            division_rows.append(divide_exact)

    checks = {
        "signed_state_count": len(SIGNED_FNIZ_OCTET),
        "base_operations": list(BASE_OPERATIONS),
        "operation_cell_count": len(BASE_OPERATIONS) * len(SIGNED_FNIZ_OCTET) ** 2,
        "signed_zero_distinct": theorem.signed_zero_distinct,
        "subtraction_as_additive_reversal_all_pairs": all(subtraction_rows),
        "division_as_multiplicative_reciprocal_all_pairs": all(division_rows),
        "ordered_pair_count_per_identity": len(subtraction_rows),
    }
    require(checks["signed_state_count"] == 8, "signed FNIZ state count mismatch")
    require(checks["base_operations"] == ["+", "-", "*", "/"], "FNIZ operation order mismatch")
    require(checks["operation_cell_count"] == 256, "FNIZ operation cell count mismatch")
    require(checks["signed_zero_distinct"], "signed zero is not distinct")
    require(checks["subtraction_as_additive_reversal_all_pairs"], "subtraction identity failed")
    require(checks["division_as_multiplicative_reciprocal_all_pairs"], "division identity failed")
    return checks


def generated_subgroup(first, second, modulus=12):
    return tuple(
        value
        for value in range(modulus)
        if value % math.gcd(modulus, first, second) == 0
    )


def conditional_candidates():
    rows = []
    subgroup_orders = set()
    for add_step in range(12):
        for multiply_step in range(12):
            subgroup = generated_subgroup(add_step, multiply_step)
            order = len(subgroup)
            subgroup_orders.add(order)
            rows.append({
                "candidate_id": f"a{add_step:02d}_m{multiply_step:02d}",
                "add_step": add_step,
                "subtract_step": (-add_step) % 12,
                "multiply_step": multiply_step,
                "divide_step": (-multiply_step) % 12,
                "generated_subgroup_order": order,
                "lagrange_divides_12": 12 % order == 0,
                "source_anchor": "NONE",
                "selected": False,
            })
    require(len(rows) == 144, "conditional candidate count mismatch")
    require(all(row["lagrange_divides_12"] for row in rows), "Lagrange audit failed")
    require(subgroup_orders == {1, 2, 3, 4, 6, 12}, "C12 subgroup order spectrum mismatch")
    return rows, sorted(subgroup_orders)


def audit_d12_and_dvj(repo):
    import mpmath as mp
    from d12rg_riemann.spectral_cit_holonomy import (
        D12_ORDER,
        apply_central_holonomy,
        canonical_twisted_links,
        cycle_holonomy,
        twisted_cycle_power,
    )
    from d12rg_riemann.spectral_cit_moving import (
        deck_orbit_union,
        paper53_deck_orbit,
    )
    from d12rg_riemann.spectral_dvj import solve_dvj_positive_roots
    from d12rg_riemann.spectral_dvj_transfer import (
        dvj_direct_transfer_symbol,
        dvj_reciprocal_phase_carrier,
        suzuki_rapidity_symbol,
    )

    mp.mp.dps = MP_DPS
    tolerance = mp.mpf(TOLERANCE_TEXT)
    lower, upper = solve_dvj_positive_roots(dps=ROOT_DPS)
    orbit = paper53_deck_orbit()
    d12_checks = {
        "order": D12_ORDER,
        "deck_orbit_count": len(orbit),
        "distinct_deck_translates": len(set(orbit)),
        "deck_orbit_union": list(deck_orbit_union()),
    }
    require(d12_checks["order"] == 12, "D12 order mismatch")
    require(d12_checks["deck_orbit_count"] == 12, "deck orbit count mismatch")
    require(d12_checks["distinct_deck_translates"] == 12, "deck translates are not distinct")
    require(d12_checks["deck_orbit_union"] == list(range(12)), "deck orbit does not cover D12")

    probe_rows = []
    state = tuple(mp.mpc(index + 1, (index + 1) / 19) for index in range(12))
    for parameter_text in DVJ_PARAMETERS:
        parameter = mp.mpf(parameter_text)
        lower_symbol = suzuki_rapidity_symbol(parameter, lower)
        upper_symbol = suzuki_rapidity_symbol(parameter, upper)
        transfer = dvj_direct_transfer_symbol(parameter, lower, upper)
        reciprocal = dvj_reciprocal_phase_carrier(parameter, lower, upper)
        links = canonical_twisted_links(transfer)
        after = twisted_cycle_power(state, links, 12)
        expected = apply_central_holonomy(state, transfer)
        closure_residual = max(abs(a - b) for a, b in zip(after, expected))
        row = {
            "parameter": parameter_text,
            "transfer": transfer,
            "nonzero": transfer != 0,
            "forward_residual": abs(transfer * lower_symbol - upper_symbol),
            "inverse_residual": abs(upper_symbol / transfer - lower_symbol),
            "reciprocal_determinant_residual": abs(
                reciprocal[0][0] * reciprocal[1][1] - 1
            ),
            "cycle_holonomy_residual": abs(cycle_holonomy(links) - transfer),
            "clock_closure_residual": closure_residual,
        }
        require(row["nonzero"], "DVJ transfer vanished")
        for key in (
            "forward_residual",
            "inverse_residual",
            "reciprocal_determinant_residual",
            "cycle_holonomy_residual",
            "clock_closure_residual",
        ):
            require(row[key] <= tolerance, "DVJ audit failed: " + key)
        probe_rows.append(row)
    return d12_checks, probe_rows


def _name_tokens(tree):
    tokens = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr.lower())
        elif isinstance(node, ast.Import):
            tokens.update(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                tokens.add(node.module.lower())
            tokens.update(alias.name.lower() for alias in node.names)
    return tokens


def connector_scan(repo):
    families = {
        "fniz": ("fniz", "signed_fniz_xi", "spectral_maya_fniz"),
        "dvj": ("dvj", "dvj_direct_transfer_symbol", "spectral_dvj_transfer"),
        "d12_deck": ("deck", "shift_modes", "paper53_deck_orbit", "spectral_cit_moving"),
    }
    executable_candidates = []
    scan_rows = []
    for path in sorted((repo / "src/d12rg_riemann").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        tokens = _name_tokens(tree)
        flags = {
            family: any(any(term in token for token in tokens) for term in terms)
            for family, terms in families.items()
        }
        if any(flags.values()):
            scan_rows.append({
                "file": str(path.relative_to(repo)),
                **flags,
                "all_three": all(flags.values()),
            })
        if all(flags.values()):
            executable_candidates.append(str(path.relative_to(repo)))

    documentation_candidates = []
    for relative in EXPECTED_SOURCE_HASHES:
        if not relative.startswith("docs/"):
            continue
        text = (repo / relative).read_text(encoding="utf-8").lower()
        flags = {
            family: any(term in text for term in terms)
            for family, terms in families.items()
        }
        if all(flags.values()):
            documentation_candidates.append(relative)
    return {
        "executable_connector_candidates": executable_candidates,
        "documentation_cooccurrence_candidates": documentation_candidates,
        "scan_rows": scan_rows,
        "explicit_executable_connector_found": bool(executable_candidates),
    }


def classify(connector, candidate_rows, advaita_checks):
    if not connector["explicit_executable_connector_found"]:
        return "INCOMPLETE_SOURCE_DEFINITION"
    anchored = [row for row in candidate_rows if row["source_anchor"] != "NONE"]
    if not anchored:
        if len(candidate_rows) == 144:
            return "SOURCE_CONSTRAINTS_DO_NOT_NARROW"
        return "MULTIPLE_SOURCE_ADMISSIBLE_RULES"
    if len(anchored) == 1:
        return "UNIQUE_SOURCE_DERIVED_RULE"
    if not anchored:
        return "NO_ADMISSIBLE_RULE"
    if not advaita_checks["restoration_work_explicit"]:
        return "INCOMPLETE_SOURCE_DEFINITION"
    return "MULTIPLE_SOURCE_ADMISSIBLE_RULES"


def result_markdown(summary):
    classification = summary["primary_classification"]
    return f"""# Experiment 007 Phase 1 Result\n\n## Primary classification\n\n**{classification}**\n\n## What was audited\n\nThe frozen D12RG sources passed provenance, signed-FNIZ, D12 group, moving-projector, and native DVJ transfer checks. The complete conditional primitive/derived operation-to-deck family was enumerated without selecting a rule.\n\n## Source-derivation result\n\nExecutable connector candidates found: {len(summary['connector_audit']['executable_connector_candidates'])}.\n\nConditional rules remaining: {summary['candidate_audit']['remaining_rule_count']}.\n\nThis classification concerns whether the cited sources already determine a unique connector. It is not a Class 2, O3, or Riemann-hypothesis result. A later searched rule would remain a constructed bridge and would require a separate frozen search record and held-out confirmation.\n"""


def main():
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest, registration_rows = verify_registration_manifest(
        args.registration_manifest
    )
    repo, advaita, provenance_rows, source_hashes = verify_sources(
        args.riemann_repo, args.advaita_file
    )
    advaita_checks = audit_advaita(advaita)
    fniz_checks = audit_fniz(repo)
    candidates, subgroup_orders = conditional_candidates()
    d12_checks, dvj_rows = audit_d12_and_dvj(repo)
    connector = connector_scan(repo)
    classification = classify(connector, candidates, advaita_checks)

    initial_rule_count = 12 ** 4
    remaining_rule_count = len(candidates)
    summary = {
        "schema": "siel-experiment-007-phase1-source-audit-v1",
        "status": "AUDIT_COMPLETE",
        "primary_classification": classification,
        "experiment": "Experiment 007 Phase 1",
        "primary_object": "K^E_FNIZ-DVJ-D12",
        "o3_identification": False,
        "source_provenance": {
            "riemann_repository": EXPECTED_RIEMANN_REMOTE,
            "riemann_commit": EXPECTED_RIEMANN_COMMIT,
            "riemann_source_hashes": source_hashes,
            "advaita_repository": "https://gitlab.com/d12rg/d12rg_cft.git",
            "advaita_branch": "papers",
            "advaita_commit": EXPECTED_ADVAITA_COMMIT,
            "advaita_path": EXPECTED_ADVAITA_PATH,
            "advaita_sha256": EXPECTED_ADVAITA_SHA256,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "mpmath_precision": MP_DPS,
            "dvj_root_precision": ROOT_DPS,
            "tolerance": TOLERANCE_TEXT,
        },
        "advaita_audit": advaita_checks,
        "fniz_audit": fniz_checks,
        "d12_audit": {
            **d12_checks,
            "generated_subgroup_orders": subgroup_orders,
            "all_orders_divide_12": all(12 % order == 0 for order in subgroup_orders),
        },
        "dvj_audit": dvj_rows,
        "connector_audit": {
            key: value for key, value in connector.items() if key != "scan_rows"
        },
        "candidate_audit": {
            "initial_unconstrained_rule_count": initial_rule_count,
            "after_primitive_derived_constraints": remaining_rule_count,
            "after_lagrange_constraint": sum(
                row["lagrange_divides_12"] for row in candidates
            ),
            "source_anchored_rule_count": sum(
                row["source_anchor"] != "NONE" for row in candidates
            ),
            "remaining_rule_count": remaining_rule_count,
            "selected_rule_count": 0,
            "primitive_derived_pruning_power": (
                1 - remaining_rule_count / initial_rule_count
            ),
            "lagrange_pruning_power_within_conditional_family": 0.0,
        },
        "completion_checks": {
            "registration_verified": True,
            "source_provenance_verified": True,
            "signed_fniz_audited": True,
            "primitive_derived_identities_audited": True,
            "d12_group_audited": True,
            "dvj_probes_audited": True,
            "connector_scan_completed": True,
            "residual_family_reported_without_selection": True,
            "classification_emitted": True,
        },
        "interpretation_boundary": {
            "class2_tested": False,
            "o3_tested": False,
            "riemann_hypothesis_tested": False,
            "by_construction_routing_counted_as_evidence": False,
            "phase2_authorized_by_this_run": False,
        },
        "registration_manifest": manifest,
    }

    source_rows = registration_rows + provenance_rows
    for key, value in advaita_checks.items():
        source_rows.append({
            "layer": "advaita",
            "item": key,
            "status": "PASS" if value else "ABSENT",
            "detail": str(value).lower(),
        })
    for key, value in fniz_checks.items():
        source_rows.append({
            "layer": "fniz",
            "item": key,
            "status": "PASS",
            "detail": json.dumps(serial(value), sort_keys=True),
        })
    for row in connector["scan_rows"]:
        source_rows.append({
            "layer": "connector_scan",
            "item": row["file"],
            "status": "CANDIDATE" if row["all_three"] else "PARTIAL",
            "detail": json.dumps(row, sort_keys=True),
        })

    summary_path = out_dir / "summary.json"
    source_csv = out_dir / "source_audit.csv"
    candidates_csv = out_dir / "conditional_candidate_rules.csv"
    result_path = out_dir / "RESULT.md"
    manifest_path = out_dir / "output_manifest.json"
    write_json(summary_path, summary)
    write_csv(source_csv, ["layer", "item", "status", "detail"], source_rows)
    write_csv(
        candidates_csv,
        [
            "candidate_id", "add_step", "subtract_step",
            "multiply_step", "divide_step", "generated_subgroup_order",
            "lagrange_divides_12", "source_anchor", "selected",
        ],
        candidates,
    )
    result_path.write_text(result_markdown(summary), encoding="utf-8")
    output_files = [summary_path, source_csv, candidates_csv, result_path]
    write_json(manifest_path, {
        "schema": "siel-experiment-007-phase1-output-manifest-v1",
        "files": {
            path.name: sha256_file(path) for path in output_files
        },
    })

    print("status = AUDIT_COMPLETE")
    print("primary_classification =", classification)
    print("conditional_rules_remaining =", remaining_rule_count)
    print("executable_connector_candidates =", len(
        connector["executable_connector_candidates"]
    ))
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
