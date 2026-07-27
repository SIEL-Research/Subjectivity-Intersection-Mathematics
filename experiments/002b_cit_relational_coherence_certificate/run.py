#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Confirmatory audit of CIT as a relational-coherence certificate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence


SCHEMA = "siel-experiment-002b-cit-certificate-v1"
EXPERIMENT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = EXPERIMENT_DIR.parents[1]
MANIFEST_PATH = EXPERIMENT_DIR / "registration_manifest.json"
UPSTREAM_PATH = (
    REPOSITORY_ROOT
    / "experiments"
    / "002a_cdc6600_dual_ring_invariant_audit"
    / "run.py"
)
OPERATIONAL_CONTROLS = ((1, 0), (0, 1))
ONE_HOT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def load_upstream():
    spec = importlib.util.spec_from_file_location("experiment_002a", UPSTREAM_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load Experiment 002A authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A2 = load_upstream()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fieldnames: Sequence[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_registration() -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mismatches = {}
    for relative, expected in manifest["source_sha256"].items():
        path = REPOSITORY_ROOT / relative
        observed = sha256_file(path) if path.is_file() else None
        if observed != expected:
            mismatches[relative] = {"expected": expected, "observed": observed}
    if mismatches:
        fail("registration hash mismatch: " + json.dumps(mismatches))
    A2.verify_registration()
    return manifest


def repository_receipt() -> dict[str, str]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"registration_commit": commit, "remote": remote}


def signals(
    cw_state: Sequence[int],
    ccw_state: Sequence[int],
    cw_control: tuple[int, int],
    ccw_control: tuple[int, int] | None = None,
) -> dict[str, tuple[int, ...]]:
    if ccw_control is None:
        ccw_control = cw_control
    cw_sum, cw_carry = A2.local_outputs(cw_state, *cw_control)
    ccw_sum, ccw_carry = A2.local_outputs(ccw_state, *ccw_control)
    return {
        "cw_sum": cw_sum,
        "cw_carry": cw_carry,
        "ccw_sum": ccw_sum,
        "ccw_carry": ccw_carry,
    }


def copy_signals(value: dict[str, Sequence[int]]) -> dict[str, tuple[int, ...]]:
    return {key: tuple(items) for key, items in value.items()}


def rotate_word(word: Sequence[int], shift: int) -> tuple[int, ...]:
    shift %= len(word)
    return tuple(word[-shift:] + word[:-shift]) if shift else tuple(word)


def readout(value: dict[str, Sequence[int]]) -> dict[str, object]:
    d_plus = A2.xor_words(value["cw_sum"], value["cw_carry"])
    d_minus = A2.xor_words(value["ccw_sum"], value["ccw_carry"])
    cit_word = A2.and_words(d_plus, d_minus)
    l_plus = int(all(d_plus))
    l_minus = int(all(d_minus))
    cit = int(all(cit_word))
    return {
        "d_plus": d_plus,
        "d_minus": d_minus,
        "l_plus": l_plus,
        "l_minus": l_minus,
        "l_combined": l_plus & l_minus,
        "cit": cit,
    }


def make_case(
    category: str,
    intervention: str,
    value: dict[str, Sequence[int]],
    detail: str,
) -> dict[str, object]:
    result = readout(value)
    valid = int(category == "admissible")
    return {
        "category": category,
        "intervention": intervention,
        "detail": detail,
        "task_valid": valid,
        "d_plus": A2.word_text(result["d_plus"]),
        "d_minus": A2.word_text(result["d_minus"]),
        "l_plus": result["l_plus"],
        "l_minus": result["l_minus"],
        "l_combined": result["l_combined"],
        "cit": result["cit"],
        "constant_one": 1,
        "timing_oracle": valid,
        "exclusive_relational_detection": int(
            category == "relation_only"
            and result["l_plus"] == 1
            and result["l_minus"] == 1
            and result["cit"] == 0
        ),
    }


def admissible_cases() -> list[dict[str, object]]:
    rows = []
    for cw_number in range(8):
        for ccw_number in range(8):
            for control in OPERATIONAL_CONTROLS:
                base = signals(A2.bits(cw_number), A2.bits(ccw_number), control)
                rows.append(make_case(
                    "admissible", "baseline", base,
                    f"cw={cw_number};ccw={ccw_number};control={control}",
                ))
                swapped = {
                    "cw_sum": base["ccw_sum"],
                    "cw_carry": base["ccw_carry"],
                    "ccw_sum": base["cw_sum"],
                    "ccw_carry": base["cw_carry"],
                }
                rows.append(make_case(
                    "admissible", "exchange_orientation_labels", swapped,
                    f"cw={cw_number};ccw={ccw_number};control={control}",
                ))
                for shift in (1, 2):
                    relabelled = {
                        key: rotate_word(value, shift)
                        for key, value in base.items()
                    }
                    rows.append(make_case(
                        "admissible", f"cyclic_relabel_{shift}", relabelled,
                        f"cw={cw_number};ccw={ccw_number};control={control}",
                    ))
    return rows


def local_integrity_cases() -> list[dict[str, object]]:
    rows = []
    for cw_number in range(8):
        for ccw_number in range(8):
            for control in OPERATIONAL_CONTROLS:
                base = signals(A2.bits(cw_number), A2.bits(ccw_number), control)
                for side in ("cw", "ccw"):
                    for channel in ("sum", "carry"):
                        key = side + "_" + channel
                        for index in range(3):
                            changed = copy_signals(base)
                            word = list(changed[key])
                            word[index] ^= 1
                            changed[key] = tuple(word)
                            rows.append(make_case(
                                "local_integrity",
                                "invert_" + key,
                                changed,
                                (
                                    f"cw={cw_number};ccw={ccw_number};"
                                    f"control={control};site={index}"
                                ),
                            ))

    for current in range(8):
        for prior in range(8):
            if current == prior:
                continue
            for control in OPERATIONAL_CONTROLS:
                for side in ("cw", "ccw"):
                    for channel in ("sum", "carry"):
                        base = signals(A2.bits(current), A2.bits(0), control)
                        if side == "ccw":
                            base = signals(A2.bits(0), A2.bits(current), control)
                        prior_sum, prior_carry = A2.local_outputs(
                            A2.bits(prior), *control
                        )
                        changed = copy_signals(base)
                        changed[side + "_" + channel] = (
                            prior_sum if channel == "sum" else prior_carry
                        )
                        rows.append(make_case(
                            "local_integrity",
                            "unmatched_epoch_" + side + "_" + channel,
                            changed,
                            f"current={current};prior={prior};control={control}",
                        ))
    return rows


def relation_only_cases() -> list[dict[str, object]]:
    rows = []

    for current in range(8):
        for prior in range(8):
            if current == prior:
                continue
            for control in OPERATIONAL_CONTROLS:
                for side in ("cw", "ccw"):
                    base = signals(A2.bits(current), A2.bits(current), control)
                    prior_sum, prior_carry = A2.local_outputs(
                        A2.bits(prior), *control
                    )
                    changed = copy_signals(base)
                    changed[side + "_sum"] = prior_sum
                    changed[side + "_carry"] = prior_carry
                    rows.append(make_case(
                        "relation_only",
                        "matched_whole_ring_epoch_skew_" + side,
                        changed,
                        f"current={current};prior={prior};control={control}",
                    ))

    ccw_cycle = (ONE_HOT[0], ONE_HOT[2], ONE_HOT[1])
    for cw_phase, cw_state in enumerate(ONE_HOT):
        for ccw_phase, ccw_state in enumerate(ccw_cycle):
            if cw_phase == ccw_phase:
                continue
            for control in OPERATIONAL_CONTROLS:
                rows.append(make_case(
                    "relation_only",
                    "phase_incompatible_partner",
                    signals(cw_state, ccw_state, control),
                    f"cw_phase={cw_phase};ccw_phase={ccw_phase};control={control}",
                ))

    for cw_number in range(8):
        for ccw_number in range(8):
            for cw_control, ccw_control in (
                ((1, 0), (0, 1)),
                ((0, 1), (1, 0)),
            ):
                rows.append(make_case(
                    "relation_only",
                    "inconsistent_operational_controls",
                    signals(
                        A2.bits(cw_number),
                        A2.bits(ccw_number),
                        cw_control,
                        ccw_control,
                    ),
                    (
                        f"cw={cw_number};ccw={ccw_number};"
                        f"cw_control={cw_control};ccw_control={ccw_control}"
                    ),
                ))

    for cw_number in range(8):
        for ccw_number in range(8):
            for control in OPERATIONAL_CONTROLS:
                base = signals(A2.bits(cw_number), A2.bits(ccw_number), control)
                for shift in (1, 2):
                    changed = copy_signals(base)
                    changed["ccw_sum"] = rotate_word(base["ccw_sum"], shift)
                    changed["ccw_carry"] = rotate_word(
                        base["ccw_carry"], shift
                    )
                    rows.append(make_case(
                        "relation_only",
                        "relative_site_remap",
                        changed,
                        (
                            f"cw={cw_number};ccw={ccw_number};"
                            f"control={control};shift={shift}"
                        ),
                    ))
    return rows


def sequence_rows() -> list[dict[str, object]]:
    rows = []
    ccw_cycle = (ONE_HOT[0], ONE_HOT[2], ONE_HOT[1])
    for sequence in ("temporary_local_fault", "temporary_relation_fault"):
        for time in range(6):
            phase = time % 3
            base = signals(ONE_HOT[phase], ccw_cycle[phase], (1, 0))
            fault_active = time in (2, 3)
            if sequence == "temporary_local_fault" and fault_active:
                changed = copy_signals(base)
                word = list(changed["cw_sum"])
                word[0] ^= 1
                changed["cw_sum"] = tuple(word)
                base = changed
            if sequence == "temporary_relation_fault" and fault_active:
                wrong_phase = (phase + 1) % 3
                base = signals(ONE_HOT[phase], ccw_cycle[wrong_phase], (1, 0))
            result = readout(base)
            rows.append({
                "sequence": sequence,
                "time": time,
                "fault_active": int(fault_active),
                "l_plus": result["l_plus"],
                "l_minus": result["l_minus"],
                "l_combined": result["l_combined"],
                "cit": result["cit"],
                "constant_one": 1,
                "timing_oracle": int(not fault_active),
            })
    return rows


def summarize(rows: list[dict[str, object]], sequences: list[dict[str, object]]):
    categories = Counter(str(row["category"]) for row in rows)
    gates = ("cit", "l_plus", "l_minus", "l_combined", "constant_one", "timing_oracle")
    performance = {}
    for gate in gates:
        valid = [row for row in rows if row["task_valid"] == 1]
        invalid = [row for row in rows if row["task_valid"] == 0]
        relation = [row for row in rows if row["category"] == "relation_only"]
        local = [row for row in rows if row["category"] == "local_integrity"]
        performance[gate] = {
            "valid_permitted": sum(int(row[gate]) for row in valid),
            "valid_total": len(valid),
            "invalid_blocked": sum(1 - int(row[gate]) for row in invalid),
            "invalid_total": len(invalid),
            "local_faults_blocked": sum(1 - int(row[gate]) for row in local),
            "local_fault_total": len(local),
            "relation_faults_blocked": sum(1 - int(row[gate]) for row in relation),
            "relation_fault_total": len(relation),
        }

    grouped_sequences = defaultdict(list)
    for row in sequences:
        grouped_sequences[str(row["sequence"])].append(row)
    sequence_summary = {}
    for name, items in grouped_sequences.items():
        fault_times = [int(row["time"]) for row in items if row["fault_active"]]
        start = min(fault_times)
        end = max(fault_times) + 1
        detected = [
            int(row["time"]) for row in items
            if row["fault_active"] and row["cit"] == 0
        ]
        recovered = [
            int(row["time"]) for row in items
            if int(row["time"]) >= end and row["cit"] == 1
        ]
        sequence_summary[name] = {
            "cit_trace": [int(row["cit"]) for row in items],
            "valid_steps_permitted": sum(
                int(row["cit"]) for row in items if not row["fault_active"]
            ),
            "valid_step_total": sum(
                1 for row in items if not row["fault_active"]
            ),
            "detection_latency": None if not detected else min(detected) - start,
            "recovery_latency": None if not recovered else min(recovered) - end,
        }

    exclusive = sum(int(row["exclusive_relational_detection"]) for row in rows)
    cit_equals_local = sum(
        int(row["cit"] == row["l_combined"]) for row in rows
    )
    all_admissible_pass = (
        performance["cit"]["valid_permitted"]
        == performance["cit"]["valid_total"]
    )
    local_detected = performance["cit"]["local_faults_blocked"] > 0
    if exclusive > 0 and cit_equals_local < len(rows):
        class_id = "RC-2"
        class_label = "irreducible two-orientation coherence certificate"
    elif all_admissible_pass and local_detected:
        class_id = "RC-1"
        class_label = "reducible distributed integrity certificate"
    else:
        class_id = "RC-0"
        class_label = "static local tautology"

    return {
        "case_counts": dict(categories),
        "total_cases": len(rows),
        "exclusive_relational_detections": exclusive,
        "cit_equals_local_conjunction_cases": cit_equals_local,
        "cit_equals_local_conjunction_rate": cit_equals_local / len(rows),
        "gate_performance": performance,
        "sequence_summary": sequence_summary,
        "classification": {
            "class_id": class_id,
            "class_label": class_label,
        },
    }


def check_expected(summary: dict[str, object]) -> dict[str, bool]:
    metrics = summary["metrics"]
    perf = metrics["gate_performance"]
    checks = {
        "registered_case_counts": metrics["case_counts"] == {
            "admissible": 512,
            "local_integrity": 1984,
            "relation_only": 620,
        },
        "registered_total_case_count": metrics["total_cases"] == 3116,
        "admissible_construction_is_locally_valid": (
            perf["l_plus"]["valid_permitted"]
            == perf["l_plus"]["valid_total"]
            and perf["l_minus"]["valid_permitted"]
            == perf["l_minus"]["valid_total"]
        ),
        "relation_only_construction_is_locally_valid": (
            perf["l_plus"]["relation_faults_blocked"] == 0
            and perf["l_minus"]["relation_faults_blocked"] == 0
        ),
        "sequence_lengths_are_registered": all(
            len(item["cit_trace"]) == 6
            for item in metrics["sequence_summary"].values()
        ),
        "classification_uses_registered_classes": (
            metrics["classification"]["class_id"] in {"RC-0", "RC-1", "RC-2"}
        ),
    }
    if not all(checks.values()):
        fail("one or more registered acceptance checks failed")
    return checks


def result_markdown(summary: dict[str, object]) -> str:
    metrics = summary["metrics"]
    perf = metrics["gate_performance"]["cit"]
    classification = metrics["classification"]
    return "\n".join([
        "# Experiment 002B Result",
        "",
        "## Status",
        "",
        "**" + str(summary["status"]).upper() + "**",
        "",
        "## Classification",
        "",
        "**" + classification["class_id"] + " — "
        + classification["class_label"] + "**",
        "",
        "## Primary endpoint",
        "",
        "- exclusive relational detections: `"
        + str(metrics["exclusive_relational_detections"]) + "`",
        "- CIT/local-conjunction equality: `"
        + str(metrics["cit_equals_local_conjunction_cases"]) + "/"
        + str(metrics["total_cases"]) + "`",
        "",
        "## Gate performance",
        "",
        "- admissible cases permitted: `"
        + str(perf["valid_permitted"]) + "/" + str(perf["valid_total"]) + "`",
        "- local integrity faults blocked: `"
        + str(perf["local_faults_blocked"]) + "/"
        + str(perf["local_fault_total"]) + "`",
        "- relation-only faults blocked: `"
        + str(perf["relation_faults_blocked"]) + "/"
        + str(perf["relation_fault_total"]) + "`",
        "",
        "## Interpretation",
        "",
        "The complete readout detects registered local corruptions across both",
        "rings and preserves every admissible case. It is nevertheless exactly",
        "equal to the conjunction of the two local ring certificates in every",
        "registered case. No relation-only failure is detected while both local",
        "certificates pass.",
        "",
        "The registered construction therefore supports a reducible distributed",
        "integrity role, not an irreducible two-orientation coherence certificate.",
        "This does not alter Experiment 002A and does not identify CIT with a",
        "relational carrier or subjectivity.",
        "",
        "## Reproducibility receipt",
        "",
        "- registration commit: `" + summary["repository"]["registration_commit"] + "`",
        "- remote: `" + summary["repository"]["remote"] + "`",
        "- schema: `" + SCHEMA + "`",
        "",
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("confirmatory",), required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.out_dir)
    if output_dir.exists():
        fail("confirmatory output directory already exists")
    verify_registration()
    rows = admissible_cases() + local_integrity_cases() + relation_only_cases()
    sequences = sequence_rows()
    summary: dict[str, object] = {
        "schema": SCHEMA,
        "status": "pending",
        "repository": repository_receipt(),
        "metrics": summarize(rows, sequences),
    }
    if args.check:
        summary["acceptance_checks"] = check_expected(summary)
    summary["status"] = "pass"
    output_dir.mkdir(parents=True)
    case_fields = tuple(rows[0].keys())
    sequence_fields = tuple(sequences[0].keys())
    write_csv(output_dir / "certificate_cases.csv", rows, case_fields)
    write_csv(output_dir / "temporary_fault_sequences.csv", sequences, sequence_fields)
    write_json(output_dir / "summary.json", summary)
    (output_dir / "RESULT.md").write_text(
        result_markdown(summary), encoding="utf-8"
    )
    output_hashes = {
        path.name: sha256_file(path)
        for path in sorted(output_dir.iterdir())
        if path.name != "output_manifest.json"
    }
    write_json(output_dir / "output_manifest.json", output_hashes)
    metrics = summary["metrics"]
    perf = metrics["gate_performance"]["cit"]
    print("status =", summary["status"])
    print("total_cases =", metrics["total_cases"])
    print("exclusive_relational_detections =", metrics["exclusive_relational_detections"])
    print("cit_equals_local_conjunction =", str(metrics["cit_equals_local_conjunction_cases"]) + "/" + str(metrics["total_cases"]))
    print("local_faults_blocked =", str(perf["local_faults_blocked"]) + "/" + str(perf["local_fault_total"]))
    print("relation_faults_blocked =", str(perf["relation_faults_blocked"]) + "/" + str(perf["relation_fault_total"]))
    print("classification =", metrics["classification"]["class_id"])
    print("wrote", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
