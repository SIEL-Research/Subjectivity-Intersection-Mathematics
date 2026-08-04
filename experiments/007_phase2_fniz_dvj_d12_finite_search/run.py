#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the preregistered Experiment 007 Phase 2 finite search."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
PHASE1_DIR = REPO_ROOT / "experiments/007_phase1_fniz_dvj_d12_source_audit"
PHASE1_CANDIDATES = PHASE1_DIR / "results/conditional_candidate_rules.csv"
PHASE1_SUMMARY = PHASE1_DIR / "results/summary.json"
EXPECTED_PHASE1_CANDIDATE_SHA256 = (
    "a1f250c58889cc4cc200c1fe0cfa32f36111db72d9fc8d57157a6b5cbedfaf65"
)
EXPECTED_PHASE1_SUMMARY_SHA256 = (
    "d6b2b194a129cf0e7ab0688d0219aefe59221a8d12bbd54b821e1be6a3a9aa81"
)
EXPECTED_RIEMANN_COMMIT = "12759beb5c6acb41b83597dfb77b74cd576d5066"
EXPECTED_RIEMANN_REMOTE = "https://gitlab.com/d12rg/d12rg-riemann.git"
EXPECTED_SOURCE_HASHES = {
    "src/d12rg_riemann/signed_fniz_xi.py":
        "be7868799c781c62eb8adec424e6752b78e07a84c4e25fa86e45060e067045c5",
    "src/d12rg_riemann/spectral_cit_holonomy.py":
        "4c0114ba440c7b572f66cf27b3d69fe397a3ea8c54f60b7ef0c60305dc83b349",
    "src/d12rg_riemann/spectral_cit_moving.py":
        "ff6dc3fa0fdef313ff65564f06933d10ae307fa7fa75fec5b8cf984e0551b97f",
    "src/d12rg_riemann/spectral_dvj.py":
        "9dc5c1ede19b2f45a63c8a2cc04611a1187dfc01ff93826fd6622d3ba684f4c2",
    "src/d12rg_riemann/spectral_dvj_transfer.py":
        "91562caf97a6800ad5e8a622d786772d28a3c5dc7e9e7bf96ae4d6a9922be2d4",
}
OPERATIONS = ("+", "-", "*", "/")
UNITS_C12 = (1, 5, 7, 11)
DEVELOPMENT_WORDS = (
    ("+", "*", "-", "/") * 3,
    ("+", "+", "+", "*", "*", "*", "-", "-", "-", "/", "/", "/"),
    ("+", "*", "/", "-", "*", "-", "+", "/", "-", "/", "+", "*"),
    ("+", "/", "*", "-", "/", "+", "-", "*", "*", "-", "+", "/"),
)
DVJ_PARAMETERS = ("0.5", "1.0", "2.0", "5.0")
MP_DPS = 80
ROOT_DPS = 90
TOLERANCE_TEXT = "1e-40"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--riemann-repo", required=True)
    parser.add_argument(
        "--out-dir", default=str(EXPERIMENT_DIR / "results")
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


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


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


def verify_registration_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    for relative, expected in manifest["registration_sha256"].items():
        observed = sha256_file(REPO_ROOT / relative)
        require(observed == expected, "registration hash mismatch: " + relative)
    return manifest


def verify_phase1():
    require(
        sha256_file(PHASE1_CANDIDATES) == EXPECTED_PHASE1_CANDIDATE_SHA256,
        "Phase 1 candidate table hash mismatch",
    )
    require(
        sha256_file(PHASE1_SUMMARY) == EXPECTED_PHASE1_SUMMARY_SHA256,
        "Phase 1 summary hash mismatch",
    )
    summary = json.loads(PHASE1_SUMMARY.read_text(encoding="utf-8"))
    require(summary["status"] == "AUDIT_COMPLETE", "Phase 1 is incomplete")
    require(
        summary["primary_classification"] == "INCOMPLETE_SOURCE_DEFINITION",
        "unexpected Phase 1 classification",
    )
    return summary


def load_candidates():
    rows = []
    with PHASE1_CANDIDATES.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = {
                "candidate_id": raw["candidate_id"],
                "add_step": int(raw["add_step"]),
                "subtract_step": int(raw["subtract_step"]),
                "multiply_step": int(raw["multiply_step"]),
                "divide_step": int(raw["divide_step"]),
                "generated_subgroup_order": int(raw["generated_subgroup_order"]),
                "lagrange_divides_12": raw["lagrange_divides_12"] == "True",
                "source_anchor": raw["source_anchor"],
                "phase1_selected": raw["selected"] == "True",
            }
            require(
                row["subtract_step"] == (-row["add_step"]) % 12,
                "invalid subtraction step",
            )
            require(
                row["divide_step"] == (-row["multiply_step"]) % 12,
                "invalid division step",
            )
            require(row["lagrange_divides_12"], "Phase 1 Lagrange flag failed")
            require(row["source_anchor"] == "NONE", "unexpected source anchor")
            require(not row["phase1_selected"], "Phase 1 selected a candidate")
            rows.append(row)
    require(len(rows) == 144, "Phase 1 candidate count is not 144")
    require(len({row["candidate_id"] for row in rows}) == 144, "duplicate candidate IDs")
    return rows


def verify_riemann_source(path):
    repo = Path(path).resolve()
    require((repo / ".git").exists(), "Riemann path is not a Git checkout")
    require(git_output(repo, "rev-parse", "HEAD") == EXPECTED_RIEMANN_COMMIT, "Riemann commit mismatch")
    require(
        normalized_remote(git_output(repo, "remote", "get-url", "origin"))
        == normalized_remote(EXPECTED_RIEMANN_REMOTE),
        "Riemann remote mismatch",
    )
    require(not git_output(repo, "status", "--porcelain"), "Riemann checkout is dirty")
    for relative, expected in EXPECTED_SOURCE_HASHES.items():
        require(sha256_file(repo / relative) == expected, "source hash mismatch: " + relative)
    return repo


def c12_order(step):
    return 12 // math.gcd(12, int(step))


def generated_order(add_step, multiply_step):
    return 12 // math.gcd(12, int(add_step), int(multiply_step))


def mapping_from_row(row):
    return {
        "+": row["add_step"],
        "-": row["subtract_step"],
        "*": row["multiply_step"],
        "/": row["divide_step"],
    }


def development_path_coverage(mapping, word):
    position = 0
    visited = {position}
    for operation in word:
        position = (position + mapping[operation]) % 12
        visited.add(position)
    return len(visited)


def equivalence_key(add_step, multiply_step):
    orbit = set()
    for unit in UNITS_C12:
        first = (unit * add_step) % 12
        second = (unit * multiply_step) % 12
        orbit.add((first, second))
        orbit.add((second, first))
    return min(orbit)


def candidate_metrics(row, modes, shift_modes):
    mapping = mapping_from_row(row)
    translated = {
        operation: set(shift_modes(modes, step))
        for operation, step in mapping.items()
    }
    union = set().union(*translated.values())
    symmetric_differences = [
        len(translated[left] ^ translated[right])
        for left, right in combinations(OPERATIONS, 2)
    ]
    path_coverages = [
        development_path_coverage(mapping, word)
        for word in DEVELOPMENT_WORDS
    ]
    distinct_steps = len(set(mapping.values())) == 4
    metrics = {
        "full_group": generated_order(row["add_step"], row["multiply_step"]) == 12,
        "four_distinct_steps": distinct_steps,
        "translated_mode_union_size": len(union),
        "minimum_pairwise_mode_symmetric_difference": min(symmetric_differences),
        "minimum_development_path_coverage": min(path_coverages),
        "minimum_primitive_order": min(
            c12_order(row["add_step"]), c12_order(row["multiply_step"])
        ),
        "development_path_coverages": path_coverages,
        "equivalence_key": equivalence_key(row["add_step"], row["multiply_step"]),
    }
    metrics["score"] = (
        int(metrics["full_group"]),
        int(metrics["four_distinct_steps"]),
        metrics["translated_mode_union_size"],
        metrics["minimum_pairwise_mode_symmetric_difference"],
        metrics["minimum_development_path_coverage"],
        metrics["minimum_primitive_order"],
    )
    return metrics


def audit_dvj(repo):
    import mpmath as mp
    from d12rg_riemann.spectral_cit_holonomy import (
        apply_central_holonomy,
        canonical_twisted_links,
        cycle_holonomy,
        twisted_cycle_power,
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
    state = tuple(mp.mpc(index + 1, (index + 1) / 23) for index in range(12))
    rows = []
    for parameter_text in DVJ_PARAMETERS:
        parameter = mp.mpf(parameter_text)
        lower_symbol = suzuki_rapidity_symbol(parameter, lower)
        upper_symbol = suzuki_rapidity_symbol(parameter, upper)
        transfer = dvj_direct_transfer_symbol(parameter, lower, upper)
        reciprocal = dvj_reciprocal_phase_carrier(parameter, lower, upper)
        links = canonical_twisted_links(transfer)
        after = twisted_cycle_power(state, links, 12)
        expected = apply_central_holonomy(state, transfer)
        row = {
            "parameter": parameter_text,
            "nonzero": transfer != 0,
            "forward_residual": abs(transfer * lower_symbol - upper_symbol),
            "inverse_residual": abs(upper_symbol / transfer - lower_symbol),
            "reciprocal_determinant_residual": abs(reciprocal[0][0] * reciprocal[1][1] - 1),
            "cycle_holonomy_residual": abs(cycle_holonomy(links) - transfer),
            "clock_closure_residual": max(abs(a - b) for a, b in zip(after, expected)),
        }
        require(row["nonzero"], "DVJ transfer vanished")
        for key, value in row.items():
            if key.endswith("_residual"):
                require(value <= tolerance, "DVJ calibration failed: " + key)
        rows.append(row)
    return rows


def classify(top_rows):
    if not top_rows:
        return "NO_ADMISSIBLE_CANDIDATE"
    if len(top_rows) == 1:
        return "UNIQUE_CONSTRUCTED_RULE_SELECTED"
    keys = {tuple(row["equivalence_key"]) for row in top_rows}
    if len(keys) == 1:
        return "ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED"
    return "MULTIPLE_TOP_EQUIVALENCE_CLASSES"


def result_markdown(summary):
    selected = summary["selection"]
    return f"""# Experiment 007 Phase 2 Result\n\n## Primary classification\n\n**{summary['primary_classification']}**\n\n## Complete search\n\nAll {summary['candidate_count']} frozen Phase 1 candidates were scored under the preregistered lexicographic rule.\n\nMaximum-score candidates: {selected['top_candidate_count']}.\n\nMaximum-score equivalence classes: {selected['top_equivalence_class_count']}.\n\nCanonical computational representative: {selected['canonical_representative']}.\n\n## Interpretation\n\nThe selected object, if any, is a constructed bridge rule or equivalence class. This phase does not establish Class 2, O3, temporal nonseparability, recursive self-re-entry, or bilateral downstream action. Those require a separately preregistered Phase 3 on untouched conditions.\n"""


def main():
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    registration = verify_registration_manifest(args.registration_manifest)
    phase1 = verify_phase1()
    candidates = load_candidates()
    repo = verify_riemann_source(args.riemann_repo)
    sys.path.insert(0, str(repo / "src"))
    from d12rg_riemann.spectral_cit_holonomy import PAPER53_ADMISSIBLE_MODES
    from d12rg_riemann.spectral_cit_moving import shift_modes

    scored = []
    for candidate in candidates:
        metrics = candidate_metrics(candidate, PAPER53_ADMISSIBLE_MODES, shift_modes)
        scored.append({**candidate, **metrics})
    require(len(scored) == 144, "not all candidates were scored")
    maximum_score = max(row["score"] for row in scored)
    top_rows = [row for row in scored if row["score"] == maximum_score]
    primary = classify(top_rows)
    top_keys = sorted({tuple(row["equivalence_key"]) for row in top_rows})
    canonical_representative = (
        min(row["candidate_id"] for row in top_rows)
        if primary in (
            "UNIQUE_CONSTRUCTED_RULE_SELECTED",
            "ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED",
        )
        else None
    )

    for row in scored:
        row["top_score"] = row["score"] == maximum_score
        row["selected_equivalence_class"] = (
            bool(top_keys)
            and primary in (
                "UNIQUE_CONSTRUCTED_RULE_SELECTED",
                "ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED",
            )
            and tuple(row["equivalence_key"]) == top_keys[0]
        )

    class_members = defaultdict(list)
    for row in scored:
        class_members[tuple(row["equivalence_key"])].append(row)
    class_rows = []
    for key in sorted(class_members):
        members = class_members[key]
        class_rows.append({
            "equivalence_key": f"{key[0]},{key[1]}",
            "member_count": len(members),
            "top_member_count": sum(row["top_score"] for row in members),
            "canonical_candidate_id": min(row["candidate_id"] for row in members),
            "maximum_score_in_class": ";".join(str(item) for item in max(row["score"] for row in members)),
            "selected": any(row["selected_equivalence_class"] for row in members),
        })

    dvj_rows = audit_dvj(repo)
    summary = {
        "schema": "siel-experiment-007-phase2-finite-search-v1",
        "status": "SEARCH_COMPLETE",
        "primary_classification": primary,
        "experiment": "Experiment 007 Phase 2",
        "primary_object": "constructed connector for K^E_FNIZ-DVJ-D12",
        "candidate_count": len(scored),
        "error_control_family_count": 144,
        "maximum_score": maximum_score,
        "score_order": [
            "full_group",
            "four_distinct_steps",
            "translated_mode_union_size",
            "minimum_pairwise_mode_symmetric_difference",
            "minimum_development_path_coverage",
            "minimum_primitive_order",
        ],
        "selection": {
            "top_candidate_count": len(top_rows),
            "top_candidate_ids": sorted(row["candidate_id"] for row in top_rows),
            "top_equivalence_class_count": len(top_keys),
            "top_equivalence_keys": top_keys,
            "canonical_representative": canonical_representative,
            "scientific_object": (
                "equivalence_class"
                if primary == "ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED"
                else "single_rule"
                if primary == "UNIQUE_CONSTRUCTED_RULE_SELECTED"
                else "unresolved"
            ),
        },
        "phase1": {
            "classification": phase1["primary_classification"],
            "candidate_sha256": EXPECTED_PHASE1_CANDIDATE_SHA256,
            "summary_sha256": EXPECTED_PHASE1_SUMMARY_SHA256,
            "results_doi": "10.5281/zenodo.21794739",
        },
        "source": {
            "repository": EXPECTED_RIEMANN_REMOTE,
            "commit": EXPECTED_RIEMANN_COMMIT,
            "hashes": EXPECTED_SOURCE_HASHES,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "mpmath_precision": MP_DPS,
            "dvj_root_precision": ROOT_DPS,
            "tolerance": TOLERANCE_TEXT,
        },
        "development_words": DEVELOPMENT_WORDS,
        "dvj_calibration": dvj_rows,
        "completion_checks": {
            "registration_verified": True,
            "phase1_verified": True,
            "source_verified": True,
            "all_144_candidates_loaded": len(candidates) == 144,
            "all_144_candidates_scored": len(scored) == 144,
            "frozen_ranking_applied": True,
            "frozen_equivalence_applied": True,
            "all_ties_preserved": len(top_rows) >= 1,
            "classification_emitted": True,
        },
        "interpretation_boundary": {
            "source_derived": False,
            "class2_tested": False,
            "o3_tested": False,
            "phase3_confirmatory_data_inspected": False,
            "factorised_null_tested": False,
        },
        "registration_manifest": registration,
    }

    scored_rows = []
    for row in sorted(scored, key=lambda item: item["candidate_id"]):
        scored_rows.append({
            "candidate_id": row["candidate_id"],
            "add_step": row["add_step"],
            "subtract_step": row["subtract_step"],
            "multiply_step": row["multiply_step"],
            "divide_step": row["divide_step"],
            "full_group": row["full_group"],
            "four_distinct_steps": row["four_distinct_steps"],
            "translated_mode_union_size": row["translated_mode_union_size"],
            "minimum_pairwise_mode_symmetric_difference": row["minimum_pairwise_mode_symmetric_difference"],
            "minimum_development_path_coverage": row["minimum_development_path_coverage"],
            "minimum_primitive_order": row["minimum_primitive_order"],
            "development_path_coverages": ";".join(str(item) for item in row["development_path_coverages"]),
            "score": ";".join(str(item) for item in row["score"]),
            "equivalence_key": f"{row['equivalence_key'][0]},{row['equivalence_key'][1]}",
            "top_score": row["top_score"],
            "selected_equivalence_class": row["selected_equivalence_class"],
        })

    summary_path = out_dir / "summary.json"
    candidates_path = out_dir / "scored_candidates.csv"
    classes_path = out_dir / "equivalence_classes.csv"
    result_path = out_dir / "RESULT.md"
    output_manifest_path = out_dir / "output_manifest.json"
    write_json(summary_path, summary)
    write_csv(candidates_path, list(scored_rows[0]), scored_rows)
    write_csv(classes_path, list(class_rows[0]), class_rows)
    result_path.write_text(result_markdown(summary), encoding="utf-8")
    output_files = [summary_path, candidates_path, classes_path, result_path]
    write_json(output_manifest_path, {
        "schema": "siel-experiment-007-phase2-output-manifest-v1",
        "files": {path.name: sha256_file(path) for path in output_files},
    })

    print("status = SEARCH_COMPLETE")
    print("primary_classification =", primary)
    print("top_candidate_count =", len(top_rows))
    print("top_equivalence_class_count =", len(top_keys))
    print("canonical_representative =", canonical_representative)
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
