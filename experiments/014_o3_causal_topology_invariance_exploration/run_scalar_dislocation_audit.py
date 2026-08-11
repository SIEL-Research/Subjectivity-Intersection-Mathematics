#!/usr/bin/env python3
"""Test and reject scalar pre-return dislocation as a sufficient recovery predictor."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TOLERANCE = 1e-12


def decreasing_in_axis(rows, axis_getter):
    ordered = sorted(rows, key=axis_getter)
    values = [row["similarities_to_matched_intact"]["correct_return"] for row in ordered]
    return all(right <= left + TOLERANCE for left, right in zip(values, values[1:]))


def main() -> None:
    source = json.loads((RESULTS / "molecular_reentry_phase_map_summary.json").read_text())
    groups = defaultdict(list)
    for row in source["rows"]:
        groups[(row["profile"], row["temperature"], row["return_steps"])].append(row)
    records = []
    for key, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        duration_pass = decreasing_in_axis(rows, lambda row: row["removal_steps"])
        scalar_pass = decreasing_in_axis(rows, lambda row: row["pre_return_dislocation"])
        records.append({
            "profile": key[0],
            "temperature": key[1],
            "return_steps": key[2],
            "removal_duration_order_pass": duration_pass,
            "scalar_dislocation_order_pass": scalar_pass,
        })
    duration_count = sum(item["removal_duration_order_pass"] for item in records)
    scalar_count = sum(item["scalar_dislocation_order_pass"] for item in records)
    summary = {
        "schema": "siel-e014-scalar-dislocation-audit-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "hypothesis": "a scalar normalized-JS dislocation at O3 return is sufficient to order later correct-return recovery",
        "decision": "SCALAR_DISLOCATION_SUFFICIENCY_NOT_SUPPORTED",
        "group_count": len(records),
        "removal_duration_order": {
            "passing_groups": duration_count,
            "pass_fraction": duration_count / len(records),
        },
        "scalar_dislocation_order": {
            "passing_groups": scalar_count,
            "pass_fraction": scalar_count / len(records),
        },
        "interpretation": "re-entry history cannot be reduced to distance magnitude alone; state direction, basin and distributional form remain causally relevant",
        "records": records,
        "scope": {
            "not_confirmatory": True,
            "scalar_hypothesis_tested_after_phase_map_inspection": True,
            "failure_preserved": True,
        },
    }
    (RESULTS / "scalar_dislocation_audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Scalar pre-return dislocation audit",
        "",
        f"Decision: `{summary['decision']}`.",
        f"Removal-duration order: `{duration_count}/{len(records)}` (`{duration_count / len(records):.6f}`).",
        f"Scalar-dislocation order: `{scalar_count}/{len(records)}` (`{scalar_count / len(records):.6f}`).",
        "",
        "A single distance from the native state is not a sufficient history variable. The direction, basin, and distributional form of displacement must remain in the causal description.",
        "This is a preserved result-informed exploratory failure.",
    ]
    (RESULTS / "SCALAR_DISLOCATION_AUDIT_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "decision": summary["decision"],
        "groups": len(records),
        "duration_pass_fraction": duration_count / len(records),
        "scalar_dislocation_pass_fraction": scalar_count / len(records),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
