#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exact finite audit of a history-bearing dyadic relational carrier.

This experiment is a calibration benchmark. It does not model subjectivity.
It tests whether a frozen analysis can distinguish an exact path-ordered
relational state from endpoint, individual-memory, shared-driver, static-object,
coordinate-gauge, and analytical-artifact alternatives.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import Iterable


SCHEMA = "siel-experiment-001-exact-relational-holonomy-v1"
POINTS = (0, 1, 2, 3)
IDENTITY = POINTS

# A and B overlap on one point and therefore do not commute.
A_ACTION = (1, 0, 2, 3)  # transposition (0 1)
B_ACTION = (0, 2, 1, 3)  # transposition (1 2)

# The substitute partner acts on a disjoint support and commutes with A.
B_SUBSTITUTE_ACTION = (0, 1, 3, 2)  # transposition (2 3)

REFERENCE_HISTORY = "AABB"
HOLONOMY_HISTORY = "ABAB"


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Return left after right."""

    return tuple(left[right[index]] for index in POINTS)


def inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def conjugate(
    permutation: tuple[int, ...],
    gauge: tuple[int, ...],
) -> tuple[int, ...]:
    return compose(compose(gauge, permutation), inverse(gauge))


def carrier(
    history: str,
    actions: dict[str, tuple[int, ...]],
) -> tuple[int, ...]:
    state = IDENTITY
    for event in history:
        state = compose(actions[event], state)
    return state


def permutation_order(permutation: tuple[int, ...]) -> int:
    state = IDENTITY
    for order in range(1, 25):
        state = compose(permutation, state)
        if state == IDENTITY:
            return order
    raise ValueError("permutation order exceeded finite audit bound")


def cycle_type(permutation: tuple[int, ...]) -> tuple[int, ...]:
    seen: set[int] = set()
    lengths: list[int] = []
    for seed in POINTS:
        if seed in seen:
            continue
        state = seed
        length = 0
        while state not in seen:
            seen.add(state)
            state = permutation[state]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def feedback(
    state: tuple[int, ...],
    probes: tuple[int, int] = (0, 2),
) -> tuple[int, int]:
    """Read the carrier back into two direction-sensitive participant probes."""

    return state[probes[0]], inverse(state)[probes[1]]


def unique_histories() -> list[str]:
    return sorted({"".join(word) for word in itertools.permutations("AABB")})


def null_signature(history: str) -> dict[str, object]:
    """Information available to the prespecified non-relational null family."""

    return {
        "current_A": history.count("A") % 2,
        "current_B": history.count("B") % 2,
        "local_A_history": "".join(event for event in history if event == "A"),
        "local_B_history": "".join(event for event in history if event == "B"),
        "shared_driver_counts": {
            "A": history.count("A"),
            "B": history.count("B"),
        },
        "pre_existing_object": "constant",
    }


def history_rows(
    actions: dict[str, tuple[int, ...]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for history in unique_histories():
        state = carrier(history, actions)
        signature = null_signature(history)
        rows.append(
            {
                "history": history,
                "current_A": signature["current_A"],
                "current_B": signature["current_B"],
                "local_A_history": signature["local_A_history"],
                "local_B_history": signature["local_B_history"],
                "shared_driver_A_count": signature["shared_driver_counts"]["A"],
                "shared_driver_B_count": signature["shared_driver_counts"]["B"],
                "carrier": " ".join(str(value) for value in state),
                "cycle_type": " ".join(str(value) for value in cycle_type(state)),
                "carrier_order": permutation_order(state),
                "feedback_A": feedback(state)[0],
                "feedback_B": feedback(state)[1],
                "nontrivial_carrier": state != IDENTITY,
            }
        )
    return rows


def gauge_rows(
    actions: dict[str, tuple[int, ...]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_states = {
        history: carrier(history, actions) for history in unique_histories()
    }
    for gauge_index, gauge_values in enumerate(itertools.permutations(POINTS)):
        gauge = tuple(gauge_values)
        gauge_inverse = inverse(gauge)
        transformed_actions = {
            name: conjugate(action, gauge) for name, action in actions.items()
        }
        for history, base_state in base_states.items():
            transformed_state = carrier(history, transformed_actions)
            expected_state = conjugate(base_state, gauge)
            transformed_probes = (gauge[0], gauge[2])
            transformed_feedback = feedback(
                transformed_state,
                transformed_probes,
            )
            decoded_feedback = (
                gauge_inverse[transformed_feedback[0]],
                gauge_inverse[transformed_feedback[1]],
            )
            rows.append(
                {
                    "gauge_index": gauge_index,
                    "gauge": " ".join(str(value) for value in gauge),
                    "history": history,
                    "exact_conjugacy": transformed_state == expected_state,
                    "cycle_type_preserved": (
                        cycle_type(transformed_state) == cycle_type(base_state)
                    ),
                    "decoded_feedback_preserved": (
                        decoded_feedback == feedback(base_state)
                    ),
                }
            )
    return rows


def write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fieldnames: list[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary() -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    actions = {"A": A_ACTION, "B": B_ACTION}
    histories = history_rows(actions)
    gauges = gauge_rows(actions)

    states = {
        row["history"]: carrier(str(row["history"]), actions)
        for row in histories
    }
    reference_state = states[REFERENCE_HISTORY]
    holonomy_state = states[HOLONOMY_HISTORY]
    reference_feedback = feedback(reference_state)
    holonomy_feedback = feedback(holonomy_state)

    a_only = carrier("AA", {"A": A_ACTION})
    b_only = carrier("BB", {"B": B_ACTION})
    reset_feedback = feedback(IDENTITY)
    reordered_feedback = feedback(reference_state)
    substitute_state = carrier(
        HOLONOMY_HISTORY,
        {"A": A_ACTION, "B": B_SUBSTITUTE_ACTION},
    )
    substitute_feedback = feedback(substitute_state)

    signatures = {
        json.dumps(null_signature(history), sort_keys=True)
        for history in unique_histories()
    }
    relational_states = set(states.values())

    checks = {
        "J_joint_generation": (
            holonomy_state != IDENTITY
            and a_only == IDENTITY
            and b_only == IDENTITY
        ),
        "H_history_irreducibility": (
            null_signature(REFERENCE_HISTORY)
            == null_signature(HOLONOMY_HISTORY)
            and reference_state != holonomy_state
            and reference_feedback != holonomy_feedback
        ),
        "I_intervention_sensitivity": (
            reset_feedback != holonomy_feedback
            and reordered_feedback != holonomy_feedback
        ),
        "P_pair_specificity": (
            substitute_state == IDENTITY
            and substitute_feedback != holonomy_feedback
        ),
        "G_gauge_invariance": all(
            bool(row["exact_conjugacy"])
            and bool(row["cycle_type_preserved"])
            and bool(row["decoded_feedback_preserved"])
            for row in gauges
        ),
        "N_registered_null_separation": (
            len(signatures) == 1 and len(relational_states) > 1
        ),
        "T_frozen_transfer": (
            len(gauges) == 24 * len(unique_histories())
            and all(
                bool(row["exact_conjugacy"])
                and bool(row["cycle_type_preserved"])
                and bool(row["decoded_feedback_preserved"])
                for row in gauges
            )
        ),
    }

    summary = {
        "schema": SCHEMA,
        "status": "ok" if all(checks.values()) else "failed",
        "experiment": "exact_relational_holonomy",
        "state_space": "S4 acting on four labels",
        "actions": {
            "A": list(A_ACTION),
            "B": list(B_ACTION),
            "B_substitute": list(B_SUBSTITUTE_ACTION),
        },
        "histories_audited": unique_histories(),
        "reference_history": REFERENCE_HISTORY,
        "holonomy_history": HOLONOMY_HISTORY,
        "reference_carrier": list(reference_state),
        "holonomy_carrier": list(holonomy_state),
        "holonomy_cycle_type": list(cycle_type(holonomy_state)),
        "holonomy_order": permutation_order(holonomy_state),
        "reference_feedback": list(reference_feedback),
        "holonomy_feedback": list(holonomy_feedback),
        "substitute_partner_carrier": list(substitute_state),
        "substitute_partner_feedback": list(substitute_feedback),
        "distinct_null_signatures": len(signatures),
        "distinct_relational_carriers": len(relational_states),
        "gauge_transformations": 24,
        "gauge_history_cases": len(gauges),
        "evidence_gates": checks,
        "claim_boundary": {
            "computed": (
                "A path-ordered non-Abelian carrier distinguishes histories "
                "that are identical to the registered non-relational nulls."
            ),
            "system": (
                "The finite benchmark exhibits exact relational holonomy, "
                "feedback, pair sensitivity, and gauge-covariant transfer."
            ),
            "not_established": [
                "human or biological relational carriers",
                "subjectivity",
                "ontological irreducibility",
                "uniqueness of the latent carrier explanation",
                "separation from unrestricted full-history models",
            ],
        },
    }
    return summary, histories, gauges


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary, histories, gauges = build_summary()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.out_dir / "summary.json"
    history_path = args.out_dir / "history_census.csv"
    gauge_path = args.out_dir / "gauge_audit.csv"

    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        history_path,
        histories,
        [
            "history",
            "current_A",
            "current_B",
            "local_A_history",
            "local_B_history",
            "shared_driver_A_count",
            "shared_driver_B_count",
            "carrier",
            "cycle_type",
            "carrier_order",
            "feedback_A",
            "feedback_B",
            "nontrivial_carrier",
        ],
    )
    write_csv(
        gauge_path,
        gauges,
        [
            "gauge_index",
            "gauge",
            "history",
            "exact_conjugacy",
            "cycle_type_preserved",
            "decoded_feedback_preserved",
        ],
    )

    print("status =", summary["status"])
    print("histories_audited =", len(histories))
    print("distinct_null_signatures =", summary["distinct_null_signatures"])
    print("distinct_relational_carriers =", summary["distinct_relational_carriers"])
    print("holonomy_order =", summary["holonomy_order"])
    print("gauge_history_cases =", summary["gauge_history_cases"])
    print("evidence_gates =", summary["evidence_gates"])
    print("wrote", summary_path)

    if args.check and summary["status"] != "ok":
        raise SystemExit("FAIL: acceptance checks did not all pass")


if __name__ == "__main__":
    main()
