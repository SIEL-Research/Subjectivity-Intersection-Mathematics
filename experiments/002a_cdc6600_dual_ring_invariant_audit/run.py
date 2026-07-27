#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent audit of the CDC 6600 dual-ring Boolean invariant."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable, Sequence


SCHEMA = "siel-experiment-002a-cdc6600-dual-ring-audit-v1"
EXPERIMENT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = EXPERIMENT_DIR.parents[1]
MANIFEST_PATH = EXPERIMENT_DIR / "registration_manifest.json"
SOURCE_PATH = (
    REPOSITORY_ROOT
    / "third_party"
    / "luke_casson_leighton"
    / "cdc6600_dual_ring_cit_demo.py"
)
ONES = (1, 1, 1)
ZERO = (0, 0, 0)
OPERATIONAL_CONTROLS = ((1, 0), (0, 1))
HISTORY_STEPS = 6


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


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


def bits(value: int) -> tuple[int, int, int]:
    return ((value >> 2) & 1, (value >> 1) & 1, value & 1)


def word_text(value: Sequence[int]) -> str:
    return "".join(str(int(bit)) for bit in value)


def full_adder(a: int, b: int, c: int) -> tuple[int, int]:
    sum_bit = int(bool(a) ^ bool(b) ^ bool(c))
    carry_bit = int((a and b) or (b and c) or (c and a))
    return sum_bit, carry_bit


def local_outputs(
    state: Sequence[int],
    inverter: int,
    reset: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    outputs = [
        full_adder(1 - int(q_bit), inverter, reset)
        for q_bit in state
    ]
    return (
        tuple(item[0] for item in outputs),
        tuple(item[1] for item in outputs),
    )


def xor_words(
    left: Sequence[int],
    right: Sequence[int],
) -> tuple[int, ...]:
    return tuple(int(a) ^ int(b) for a, b in zip(left, right))


def and_words(
    left: Sequence[int],
    right: Sequence[int],
) -> tuple[int, ...]:
    return tuple(int(bool(a) and bool(b)) for a, b in zip(left, right))


def rotate(word: Sequence[int], direction: str) -> tuple[int, int, int]:
    a, b, c = tuple(int(value) for value in word)
    if direction == "cw":
        return c, a, b
    if direction == "ccw":
        return b, c, a
    raise ValueError("direction must be cw or ccw")


def ring_next(
    state: Sequence[int],
    inverter: int,
    reset: int,
    direction: str,
) -> tuple[int, int, int]:
    sums, carries = local_outputs(state, inverter, reset)
    set_inputs = rotate(sums, direction)
    reset_inputs = rotate(carries, direction)
    result = []
    for old, set_bit, reset_bit in zip(state, set_inputs, reset_inputs):
        if reset_bit:
            result.append(0)
        elif set_bit:
            result.append(1)
        else:
            result.append(int(old))
    return tuple(result)


def direct_readout(
    cw_state: Sequence[int],
    ccw_state: Sequence[int],
    inverter: int,
    reset: int,
) -> dict[str, object]:
    cw_sum, cw_carry = local_outputs(cw_state, inverter, reset)
    ccw_sum, ccw_carry = local_outputs(ccw_state, inverter, reset)
    cw_diff = xor_words(cw_sum, cw_carry)
    ccw_diff = xor_words(ccw_sum, ccw_carry)
    cit_word = and_words(cw_diff, ccw_diff)
    return {
        "cw_sum": cw_sum,
        "cw_carry": cw_carry,
        "ccw_sum": ccw_sum,
        "ccw_carry": ccw_carry,
        "cw_diff": cw_diff,
        "ccw_diff": ccw_diff,
        "cit_word": cit_word,
        "cit": int(all(cit_word)),
    }


def trajectory(
    cw_state: Sequence[int],
    ccw_state: Sequence[int],
    inverter: int,
    reset: int,
    steps: int = HISTORY_STEPS,
    cw_direction: str = "cw",
    ccw_direction: str = "ccw",
) -> dict[str, list[object]]:
    cw = tuple(cw_state)
    ccw = tuple(ccw_state)
    states: list[object] = []
    readouts: list[object] = []
    for _ in range(steps):
        readouts.append(direct_readout(cw, ccw, inverter, reset)["cit"])
        states.append((word_text(cw), word_text(ccw)))
        cw = ring_next(cw, inverter, reset, cw_direction)
        ccw = ring_next(ccw, inverter, reset, ccw_direction)
    return {"states": states, "cit": readouts}


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
    return manifest


def repository_receipt() -> dict[str, object]:
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


def source_self_test() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", str(SOURCE_PATH), "--self-test"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def exhaustive_audit() -> tuple[dict[str, object], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    for cw_number in range(8):
        for ccw_number in range(8):
            for inverter, reset in OPERATIONAL_CONTROLS:
                result = direct_readout(
                    bits(cw_number), bits(ccw_number), inverter, reset
                )
                rows.append({
                    "cw_state": word_text(bits(cw_number)),
                    "ccw_state": word_text(bits(ccw_number)),
                    "H": inverter,
                    "Z": reset,
                    "cw_diff": word_text(result["cw_diff"]),
                    "ccw_diff": word_text(result["ccw_diff"]),
                    "cit_word": word_text(result["cit_word"]),
                    "cit": result["cit"],
                })

    local_cases = []
    for q_bit in (0, 1):
        for inverter, reset in OPERATIONAL_CONTROLS:
            sum_bit, carry_bit = full_adder(1 - q_bit, inverter, reset)
            local_cases.append(sum_bit ^ carry_bit)

    single_ring_cases = []
    for state_number in range(8):
        for inverter, reset in OPERATIONAL_CONTROLS:
            sums, carries = local_outputs(bits(state_number), inverter, reset)
            single_ring_cases.append(xor_words(sums, carries))

    partner_comparisons = 0
    partner_changes = 0
    for cw_number in range(8):
        for inverter, reset in OPERATIONAL_CONTROLS:
            reference = direct_readout(
                bits(cw_number), bits(0), inverter, reset
            )["cit"]
            for ccw_number in range(8):
                partner_comparisons += 1
                observed = direct_readout(
                    bits(cw_number), bits(ccw_number), inverter, reset
                )["cit"]
                partner_changes += int(observed != reference)

    state_interventions = 0
    state_changes = 0
    for cw_number in range(8):
        for ccw_number in range(8):
            for inverter, reset in OPERATIONAL_CONTROLS:
                reference = direct_readout(
                    bits(cw_number), bits(ccw_number), inverter, reset
                )["cit"]
                for side in ("cw", "ccw"):
                    for bit_index in range(3):
                        changed_cw = cw_number
                        changed_ccw = ccw_number
                        mask = 1 << (2 - bit_index)
                        if side == "cw":
                            changed_cw ^= mask
                        else:
                            changed_ccw ^= mask
                        observed = direct_readout(
                            bits(changed_cw), bits(changed_ccw), inverter, reset
                        )["cit"]
                        state_interventions += 1
                        state_changes += int(observed != reference)

    history_traces = set()
    orientation_traces = set()
    feedback_equivalent = True
    for cw_number in range(8):
        for ccw_number in range(8):
            for inverter, reset in OPERATIONAL_CONTROLS:
                normal = trajectory(
                    bits(cw_number), bits(ccw_number), inverter, reset
                )
                history_traces.add(tuple(normal["cit"]))
                for directions in (("cw", "ccw"), ("ccw", "cw")):
                    changed = trajectory(
                        bits(cw_number),
                        bits(ccw_number),
                        inverter,
                        reset,
                        cw_direction=directions[0],
                        ccw_direction=directions[1],
                    )
                    orientation_traces.add(tuple(changed["cit"]))

            constant = trajectory(bits(cw_number), bits(ccw_number), 1, 0)
            feedback_cw = bits(cw_number)
            feedback_ccw = bits(ccw_number)
            feedback_states = []
            feedback_cit = 1
            for _ in range(HISTORY_STEPS):
                feedback_states.append(
                    (word_text(feedback_cw), word_text(feedback_ccw))
                )
                readout = direct_readout(
                    feedback_cw, feedback_ccw, feedback_cit, 0
                )
                feedback_cit = int(readout["cit"])
                feedback_cw = ring_next(feedback_cw, feedback_cit, 0, "cw")
                feedback_ccw = ring_next(
                    feedback_ccw, feedback_cit, 0, "ccw"
                )
            feedback_equivalent &= (
                feedback_states == constant["states"]
                and [1] * HISTORY_STEPS == constant["cit"]
            )

    reset_cases = 0
    reset_passes = 0
    for cw_number in range(8):
        for ccw_number in range(8):
            reset_cases += 1
            cw_next = ring_next(bits(cw_number), 1, 1, "cw")
            ccw_next = ring_next(bits(ccw_number), 1, 1, "ccw")
            reset_passes += int(cw_next == ZERO and ccw_next == ZERO)

    mismatched_cases = 0
    mismatched_non_111 = 0
    for current_number in range(8):
        for prior_number in range(8):
            for inverter, reset in OPERATIONAL_CONTROLS:
                current_sum, _ = local_outputs(
                    bits(current_number), inverter, reset
                )
                _, prior_carry = local_outputs(
                    bits(prior_number), inverter, reset
                )
                mismatched_cases += 1
                mismatched_non_111 += int(
                    xor_words(current_sum, prior_carry) != ONES
                )

    metrics = {
        "operational_pair_cases": len(rows),
        "operational_invariant_passes": sum(
            row["cw_diff"] == "111"
            and row["ccw_diff"] == "111"
            and row["cit_word"] == "111"
            and row["cit"] == 1
            for row in rows
        ),
        "local_adder_cases": len(local_cases),
        "local_adder_invariant_passes": sum(local_cases),
        "single_ring_cases": len(single_ring_cases),
        "single_ring_invariant_passes": sum(
            value == ONES for value in single_ring_cases
        ),
        "partner_substitution_comparisons": partner_comparisons,
        "partner_substitution_changes": partner_changes,
        "state_interventions": state_interventions,
        "state_intervention_changes": state_changes,
        "distinct_history_cit_traces": len(history_traces),
        "distinct_orientation_cit_traces": len(orientation_traces),
        "feedback_equals_constant_control": bool(feedback_equivalent),
        "double_high_reset_cases": reset_cases,
        "double_high_reset_passes": reset_passes,
        "mismatched_epoch_cases": mismatched_cases,
        "mismatched_epoch_non_111": mismatched_non_111,
    }
    return metrics, rows


def classify(metrics: dict[str, object]) -> dict[str, object]:
    local_null_complete = (
        metrics["local_adder_invariant_passes"]
        == metrics["local_adder_cases"]
        and metrics["single_ring_invariant_passes"]
        == metrics["single_ring_cases"]
    )
    gates = {
        "J_joint_generation": not local_null_complete,
        "H_history": metrics["distinct_history_cit_traces"] > 1,
        "I_intervention": metrics["state_intervention_changes"] > 0,
        "P_pair_specificity": metrics["partner_substitution_changes"] > 0,
        "G_gauge_invariance": metrics["distinct_orientation_cit_traces"] == 1,
        "N_null_separation": not local_null_complete,
        "T_frozen_transfer": (
            metrics["operational_invariant_passes"]
            == metrics["operational_pair_cases"]
        ),
        "bilateral_feedback": not metrics["feedback_equals_constant_control"],
    }
    seven = (
        "J_joint_generation",
        "H_history",
        "I_intervention",
        "P_pair_specificity",
        "G_gauge_invariance",
        "N_null_separation",
        "T_frozen_transfer",
    )
    if all(gates[name] for name in seven) and gates["bilateral_feedback"]:
        class_id = 2
        label = "pair-indexed relational carrier"
    elif gates["H_history"] or gates["I_intervention"]:
        class_id = 1
        label = "incomplete shared-history state"
    else:
        class_id = 0
        label = "local-complementarity/common-control null"
    return {
        "class_id": class_id,
        "class_label": label,
        "evidence_gates": gates,
    }


def result_markdown(summary: dict[str, object]) -> str:
    metrics = summary["metrics"]
    classification = summary["classification"]
    gates = classification["evidence_gates"]
    lines = [
        "# Experiment 002A Result",
        "",
        "## Status",
        "",
        "**" + str(summary["status"]).upper() + "**",
        "",
        "## Primary result",
        "",
        "The preserved implementation reproduced its registered Boolean",
        "invariant and reset behaviour. The independent classification audit",
        "assigned the registered `CIT` readout to **Class "
        + str(classification["class_id"])
        + " — "
        + str(classification["class_label"])
        + "**.",
        "",
        "## Exact readout",
        "",
        "- source self-test: "
        + ("PASS" if summary["source_self_test"]["passed"] else "FAIL"),
        "- operational paired cases: `"
        + str(metrics["operational_invariant_passes"])
        + "/"
        + str(metrics["operational_pair_cases"])
        + "` invariant passes",
        "- local-adder cases: `"
        + str(metrics["local_adder_invariant_passes"])
        + "/"
        + str(metrics["local_adder_cases"])
        + "` invariant passes",
        "- single-ring cases: `"
        + str(metrics["single_ring_invariant_passes"])
        + "/"
        + str(metrics["single_ring_cases"])
        + "` invariant passes",
        "- partner-substitution changes: `"
        + str(metrics["partner_substitution_changes"])
        + "/"
        + str(metrics["partner_substitution_comparisons"])
        + "`",
        "- one-bit intervention changes: `"
        + str(metrics["state_intervention_changes"])
        + "/"
        + str(metrics["state_interventions"])
        + "`",
        "- double-high resets: `"
        + str(metrics["double_high_reset_passes"])
        + "/"
        + str(metrics["double_high_reset_cases"])
        + "`",
        "- feedback equals constant control: `"
        + str(metrics["feedback_equals_constant_control"]).lower()
        + "`",
        "",
        "## Evidence gates",
        "",
    ]
    for name, passed in gates.items():
        lines.append("- `" + name + "`: " + ("PASS" if passed else "FAIL"))
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The two oriented rings and matched buffers do produce the stated",
        "readout. However, the same invariant is already forced at each local",
        "full adder by `S XOR K = 1` in single-high mode. The final dual-ring",
        "comparison therefore combines two constant words and contains no",
        "registered pair or history information.",
        "",
        "The `H = Z = 1` transition to `000` is verified as a common reset.",
        "It is not a selective intervention on a relation-generated state.",
        "",
        "This result classifies only the registered `CIT` readout. It does not",
        "exclude other uses of the dual-ring architecture or a revised",
        "history-bearing coupling that would require a separate registration.",
        "",
        "## Reproducibility receipt",
        "",
        "- registration commit: `"
        + str(summary["repository"]["registration_commit"])
        + "`",
        "- remote: `" + str(summary["repository"]["remote"]) + "`",
        "- schema: `" + SCHEMA + "`",
        "",
    ])
    return "\n".join(lines)


def check_expected(summary: dict[str, object]) -> None:
    metrics = summary["metrics"]
    required = {
        "source_self_test": summary["source_self_test"]["passed"],
        "all_operational_cases": (
            metrics["operational_pair_cases"] == 128
            and metrics["operational_invariant_passes"] == 128
        ),
        "local_adder_reduction": (
            metrics["local_adder_cases"] == 4
            and metrics["local_adder_invariant_passes"] == 4
        ),
        "single_ring_reduction": (
            metrics["single_ring_cases"] == 16
            and metrics["single_ring_invariant_passes"] == 16
        ),
        "partner_independence": metrics["partner_substitution_changes"] == 0,
        "state_independence": metrics["state_intervention_changes"] == 0,
        "history_independence": metrics["distinct_history_cit_traces"] == 1,
        "orientation_invariance": (
            metrics["distinct_orientation_cit_traces"] == 1
        ),
        "constant_feedback_equivalence": (
            metrics["feedback_equals_constant_control"] is True
        ),
        "all_common_resets": (
            metrics["double_high_reset_cases"] == 64
            and metrics["double_high_reset_passes"] == 64
        ),
        "registered_class_zero": summary["classification"]["class_id"] == 0,
    }
    summary["acceptance_checks"] = required
    if not all(required.values()):
        fail("one or more registered acceptance checks failed")


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
    receipt = repository_receipt()
    source_result = source_self_test()
    metrics, rows = exhaustive_audit()
    classification = classify(metrics)
    summary: dict[str, object] = {
        "schema": SCHEMA,
        "status": "pending",
        "repository": receipt,
        "source": {
            "path": str(SOURCE_PATH.relative_to(REPOSITORY_ROOT)),
            "sha256": sha256_file(SOURCE_PATH),
        },
        "source_self_test": source_result,
        "metrics": metrics,
        "classification": classification,
    }
    if args.check:
        check_expected(summary)
    summary["status"] = "pass" if all(
        summary.get("acceptance_checks", {"execution": True}).values()
    ) else "fail"
    output_dir.mkdir(parents=True)
    write_csv(
        output_dir / "exhaustive_operational_cases.csv",
        rows,
        (
            "cw_state",
            "ccw_state",
            "H",
            "Z",
            "cw_diff",
            "ccw_diff",
            "cit_word",
            "cit",
        ),
    )
    (output_dir / "source_self_test.txt").write_text(
        source_result["stdout"] + source_result["stderr"],
        encoding="utf-8",
    )
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
    print("status =", summary["status"])
    print("source_self_test =", source_result["passed"])
    print("operational_invariant =", str(metrics["operational_invariant_passes"]) + "/128")
    print("local_adder_invariant =", str(metrics["local_adder_invariant_passes"]) + "/4")
    print("partner_substitution_changes =", metrics["partner_substitution_changes"])
    print("state_intervention_changes =", metrics["state_intervention_changes"])
    print("feedback_equals_constant =", metrics["feedback_equals_constant_control"])
    print("classification = Class", classification["class_id"])
    print("wrote", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
