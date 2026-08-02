#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Recompute the public-data portion of the E003R post-release design audit.

This script does not rerun E003R and does not alter its registered decision.
It reads only the published receipts and the frozen donor rule.  The separate
connector-packet projection audit requires the hash-frozen private runtime and
is therefore not claimed by this public-only calculation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PAIR_COUNT = 128
DONOR_OFFSET = 65
PAIR_SPECIFICITY_THRESHOLD = 0.0707154800


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    receipts = read_rows(HERE / "results" / "state_match_receipts.csv")
    metrics = read_rows(HERE / "results" / "pair_metrics.csv")

    if len(receipts) != PAIR_COUNT or len(metrics) != PAIR_COUNT:
        raise SystemExit("FAIL: expected 128 rows in each published receipt")

    metrics_by_pair = {row["pair_id"]: row for row in metrics}
    if len(metrics_by_pair) != PAIR_COUNT:
        raise SystemExit("FAIL: duplicate pair identifiers in pair metrics")

    unique_a = {row["A_reference_sha256"] for row in receipts}
    unique_b = {row["B_reference_sha256"] for row in receipts}
    unique_ab = {
        (row["A_reference_sha256"], row["B_reference_sha256"])
        for row in receipts
    }

    same_family: list[str] = []
    cross_family: list[str] = []
    phase_a_failures: list[str] = []
    phase_b_failures: list[str] = []
    donor_rows = []

    for index, receipt in enumerate(receipts):
        recipient = receipt["pair_id"]
        donor_index = (index + DONOR_OFFSET) % PAIR_COUNT
        donor = receipts[donor_index]
        recipient_family = int(receipt["family"])
        donor_family = int(donor["family"])
        within_family = recipient_family == donor_family
        (same_family if within_family else cross_family).append(recipient)

        metric = metrics_by_pair[recipient]
        phase_a_distance = float(metric["phase_a_pair_specificity"])
        phase_b_distance = float(metric["phase_b_pair_specificity"])
        phase_a_pass = phase_a_distance > PAIR_SPECIFICITY_THRESHOLD
        phase_b_pass = phase_b_distance > PAIR_SPECIFICITY_THRESHOLD
        if not phase_a_pass:
            phase_a_failures.append(recipient)
        if not phase_b_pass:
            phase_b_failures.append(recipient)

        donor_rows.append({
            "recipient": recipient,
            "donor": donor["pair_id"],
            "recipient_family": recipient_family,
            "donor_family": donor_family,
            "within_family": within_family,
            "phase_a_pair_specificity_distance": phase_a_distance,
            "phase_b_pair_specificity_distance": phase_b_distance,
            "phase_a_pair_specificity": phase_a_pass,
            "phase_b_pair_specificity": phase_b_pass,
        })

    summary = {
        "schema": "siel-e003r-post-release-public-design-audit-v1",
        "scope": "published receipts and frozen donor rule only",
        "administrative_pair_count": len(receipts),
        "unique_complete_A_state_hashes": len(unique_a),
        "unique_complete_B_state_hashes": len(unique_b),
        "unique_complete_AB_state_hash_pairs": len(unique_ab),
        "donor_offset": DONOR_OFFSET,
        "pair_specificity_threshold_strictly_greater_than": (
            PAIR_SPECIFICITY_THRESHOLD
        ),
        "same_family_exchange_count": len(same_family),
        "same_family_recipients": same_family,
        "cross_family_exchange_count": len(cross_family),
        "phase_a_pair_specificity_failures": phase_a_failures,
        "phase_b_pair_specificity_failures": phase_b_failures,
        "same_family_recipients_equal_phase_a_failures": (
            same_family == phase_a_failures
        ),
        "same_family_recipients_equal_phase_b_failures": (
            same_family == phase_b_failures
        ),
        "connector_packet_projection": {
            "status": "NOT_RECOMPUTED_BY_PUBLIC_ONLY_AUDIT",
            "reason": "requires the hash-frozen private subjectivity-agent runtime",
        },
        "donor_assignments": donor_rows,
    }

    expected = {
        "administrative_pair_count": 128,
        "unique_complete_A_state_hashes": 16,
        "unique_complete_B_state_hashes": 16,
        "unique_complete_AB_state_hash_pairs": 16,
        "same_family_exchange_count": 2,
        "same_family_recipients": ["P2063", "P2127"],
        "cross_family_exchange_count": 126,
        "phase_a_pair_specificity_failures": ["P2063", "P2127"],
        "phase_b_pair_specificity_failures": ["P2063", "P2127"],
    }
    for key, value in expected.items():
        if summary[key] != value:
            raise SystemExit(f"FAIL: {key}: {summary[key]!r} != {value!r}")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
