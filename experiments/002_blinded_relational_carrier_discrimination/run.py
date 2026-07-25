#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Blinded synthetic discrimination of relational-carrier classes.

The confirmatory sequence is enforced in one process:

1. verify the frozen registration manifest;
2. generate an observed table and a separate ground-truth table;
3. analyse the observed table without passing ground truth;
4. hash the prediction file;
5. unseal ground truth for scoring; and
6. evaluate the preregistered acceptance targets.

The experiment is a synthetic methodological benchmark. It does not identify
an operational unit or a detected carrier with subjectivity.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Sequence


SCHEMA = "siel-experiment-002-blinded-relational-carrier-v1"
DEVELOPMENT_SEED = 2026072501
CONFIRMATORY_SEED = 2026072502

FAMILY_CLASSES = {
    "G0-I": 0,
    "G0-C": 0,
    "G0-D": 0,
    "G0-X": 0,
    "G0-H": 0,
    "G1-F": 1,
    "G2-P": 2,
    "G2-M": 2,
}

CONDITIONS = (
    "reference",
    "holonomy",
    "relation_reset",
    "partner_substitution",
    "remove_A",
    "remove_B",
)

GAUGES = (
    (0, 1, 2),
    (1, 2, 0),
    (1, 0, 2),
    (0, 2, 1),
)

NOISE_PROBABILITIES = (0.00, 0.05, 0.10, 0.20)
REPETITIONS = 16
EPISODE_LENGTH = 32
FORMATION_LENGTH = 8

THRESHOLDS = {
    "categorical_difference": 0.58,
    "counterfactual_margin": 0.25,
    "gauge_consistency": 0.95,
}

ACCEPTANCE = {
    "balanced_accuracy_each_transfer": 0.80,
    "recall_each_class_each_transfer": 0.70,
    "false_class2_rate": 0.10,
    "g2p_recall": 0.80,
    "g2m_recall": 0.70,
    "gauge_consistency": 0.95,
}

OBSERVED_FIELDS = (
    "dataset_id",
    "opaque_pair_id",
    "transfer",
    "repeat",
    "observation_map_id",
    "noise_probability",
    "missing_probability",
    "condition",
    "time",
    "phase",
    "input_A",
    "input_B",
    "driver_marker",
    "y_A",
    "y_B",
    "joint_readout",
)

PREDICTION_FIELDS = (
    "dataset_id",
    "transfer",
    "predicted_class",
    "J_joint_generation",
    "H_history",
    "I_intervention",
    "P_pair_specificity",
    "G_gauge_invariance",
    "N_null_separation",
    "T_frozen_transfer",
    "bilateral_feedback",
    "history_joint_mismatch",
    "history_A_mismatch",
    "history_B_mismatch",
    "reset_margin",
    "partner_margin",
    "remove_A_margin",
    "remove_B_margin",
    "driver_history_mismatch",
    "gauge_consistency",
)


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def stable_int(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


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


def compose_permutation(
    left: tuple[int, ...],
    right: tuple[int, ...],
) -> tuple[int, ...]:
    return tuple(left[right[index]] for index in range(len(left)))


def inverse_permutation(
    permutation: tuple[int, ...],
) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def conjugate_permutation(
    value: tuple[int, ...],
    gauge: tuple[int, ...],
) -> tuple[int, ...]:
    return compose_permutation(
        compose_permutation(gauge, value),
        inverse_permutation(gauge),
    )


PERMUTATION_IDENTITY = (0, 1, 2, 3)
PERMUTATION_A = (1, 0, 2, 3)
PERMUTATION_B = (0, 2, 1, 3)
PERMUTATION_B_SUBSTITUTE = (0, 1, 3, 2)


def permutation_carrier(
    pair_tag: str,
    condition: str,
) -> tuple[int, ...]:
    gauges = tuple(itertools.permutations(PERMUTATION_IDENTITY))
    pair_gauge = tuple(gauges[stable_int("G2-P", pair_tag) % len(gauges)])
    actions = {
        "A": conjugate_permutation(PERMUTATION_A, pair_gauge),
        "B": conjugate_permutation(PERMUTATION_B, pair_gauge),
    }
    histories = {
        "reference": "AABB",
        "holonomy": "ABAB",
        "relation_reset": "",
        "partner_substitution": "ABAB",
        "remove_A": "BB",
        "remove_B": "AA",
    }
    if condition == "partner_substitution":
        actions["B"] = conjugate_permutation(
            PERMUTATION_B_SUBSTITUTE,
            pair_gauge,
        )
    state = PERMUTATION_IDENTITY
    for event in histories[condition]:
        state = compose_permutation(actions[event], state)
    return state


Matrix = tuple[int, int, int, int]
MATRIX_IDENTITY: Matrix = (1, 0, 0, 1)
MATRIX_A: Matrix = (2, 0, 0, 1)
MATRIX_B: Matrix = (1, 1, 0, 2)
MATRIX_B_SUBSTITUTE: Matrix = (1, 0, 0, 2)


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    a, b, c, d = left
    e, f, g, h = right
    return (
        (a * e + b * g) % 3,
        (a * f + b * h) % 3,
        (c * e + d * g) % 3,
        (c * f + d * h) % 3,
    )


def matrix_determinant(value: Matrix) -> int:
    a, b, c, d = value
    return (a * d - b * c) % 3


def matrix_inverse(value: Matrix) -> Matrix:
    a, b, c, d = value
    determinant = matrix_determinant(value)
    if determinant == 0:
        raise ValueError("matrix is singular")
    inverse_determinant = 1 if determinant == 1 else 2
    return (
        d * inverse_determinant % 3,
        -b * inverse_determinant % 3,
        -c * inverse_determinant % 3,
        a * inverse_determinant % 3,
    )


def invertible_matrices() -> tuple[Matrix, ...]:
    return tuple(
        values
        for values in itertools.product(range(3), repeat=4)
        if matrix_determinant(values) != 0
    )


def conjugate_matrix(value: Matrix, gauge: Matrix) -> Matrix:
    return matrix_multiply(
        matrix_multiply(gauge, value),
        matrix_inverse(gauge),
    )


def matrix_carrier(pair_tag: str, condition: str) -> Matrix:
    gauges = invertible_matrices()
    pair_gauge = gauges[stable_int("G2-M", pair_tag) % len(gauges)]
    actions = {
        "A": conjugate_matrix(MATRIX_A, pair_gauge),
        "B": conjugate_matrix(MATRIX_B, pair_gauge),
    }
    histories = {
        "reference": "AABB",
        "holonomy": "ABAB",
        "relation_reset": "",
        "partner_substitution": "ABAB",
        "remove_A": "BB",
        "remove_B": "AA",
    }
    if condition == "partner_substitution":
        actions["B"] = conjugate_matrix(
            MATRIX_B_SUBSTITUTE,
            pair_gauge,
        )
    state = MATRIX_IDENTITY
    for event in histories[condition]:
        state = matrix_multiply(actions[event], state)
    return state


def full_adder_carry(condition: str) -> int:
    histories = {
        "reference": ((1, 1), (0, 0)),
        "holonomy": ((0, 0), (1, 1)),
        "relation_reset": (),
        "partner_substitution": ((0, 0), (1, 1)),
        "remove_A": ((0, 0), (0, 1)),
        "remove_B": ((0, 0), (1, 0)),
    }
    carry = 0
    for left, right in histories[condition]:
        carry = (left & right) | (carry & (left ^ right))
    return carry


def exact_self_test() -> dict[str, bool]:
    pair = "self-test-pair"
    permutation_holonomy = permutation_carrier(pair, "holonomy")
    matrix_holonomy = matrix_carrier(pair, "holonomy")
    checks = {
        "permutation_reference_identity": (
            permutation_carrier(pair, "reference")
            == PERMUTATION_IDENTITY
        ),
        "permutation_holonomy_nontrivial": (
            permutation_holonomy != PERMUTATION_IDENTITY
        ),
        "permutation_substitution_identity": (
            permutation_carrier(pair, "partner_substitution")
            == PERMUTATION_IDENTITY
        ),
        "matrix_reference_identity": (
            matrix_carrier(pair, "reference") == MATRIX_IDENTITY
        ),
        "matrix_holonomy_nontrivial": (
            matrix_holonomy != MATRIX_IDENTITY
        ),
        "matrix_substitution_identity": (
            matrix_carrier(pair, "partner_substitution")
            == MATRIX_IDENTITY
        ),
        "full_adder_reference_zero": (
            full_adder_carry("reference") == 0
        ),
        "full_adder_holonomy_one": (
            full_adder_carry("holonomy") == 1
        ),
        "full_adder_pair_independent": (
            full_adder_carry("partner_substitution") == 1
        ),
        "gl23_size_48": len(invertible_matrices()) == 48,
    }
    return checks


def registered_pair_splits() -> dict[str, tuple[tuple[str, str], ...]]:
    seen = tuple(f"S{index:02d}" for index in range(16))
    held = tuple(f"H{index:02d}" for index in range(8))
    training_pairs = tuple(
        (seen[index], seen[index + 1])
        for index in range(0, 16, 2)
    )
    t2_pairs = (
        (seen[0], seen[2]),
        (seen[1], seen[3]),
        (seen[4], seen[6]),
        (seen[5], seen[7]),
        (seen[8], seen[10]),
        (seen[9], seen[11]),
        (seen[12], seen[14]),
        (seen[13], seen[15]),
    )
    t3_pairs = tuple(
        (held[index], held[index + 1])
        for index in range(0, 8, 2)
    )
    return {
        "T1": training_pairs,
        "T2": t2_pairs,
        "T3": t3_pairs,
    }


def validate_pair_splits() -> dict[str, bool]:
    splits = registered_pair_splits()
    t1 = set(splits["T1"])
    t2 = set(splits["T2"])
    t3 = set(splits["T3"])
    t1_ids = {unit for pair in t1 for unit in pair}
    t3_ids = {unit for pair in t3 for unit in pair}
    return {
        "no_pair_overlap_T1_T2": not (t1 & t2),
        "no_pair_overlap_T1_T3": not (t1 & t3),
        "no_pair_overlap_T2_T3": not (t2 & t3),
        "heldout_identities_excluded_from_T1": not (t1_ids & t3_ids),
        "expected_pair_counts": (
            len(t1) == 8 and len(t2) == 8 and len(t3) == 4
        ),
    }


def formation_inputs(
    family: str,
    condition: str,
    time_index: int,
) -> tuple[int, int]:
    if time_index >= FORMATION_LENGTH:
        return 0, 0
    if family == "G1-F":
        histories = {
            "reference": ((1, 1), (0, 0)),
            "holonomy": ((0, 0), (1, 1)),
            "relation_reset": ((0, 0), (1, 1)),
            "partner_substitution": ((0, 0), (1, 1)),
            "remove_A": ((0, 0), (0, 1)),
            "remove_B": ((0, 0), (1, 0)),
        }
        sequence = histories[condition]
        return sequence[time_index % len(sequence)]
    histories = {
        "reference": "AABB",
        "holonomy": "ABAB",
        "relation_reset": "ABAB",
        "partner_substitution": "ABAB",
        "remove_A": "BBBB",
        "remove_B": "AAAA",
    }
    event = histories[condition][time_index % 4]
    return (1, 0) if event == "A" else (0, 1)


def carrier_effect(
    family: str,
    pair_tag: str,
    condition: str,
    readout_index: int,
) -> tuple[int, int, int, int]:
    """Return A, B, joint, and common-driver effects in GF(3)."""

    if family in {"G0-I", "G0-C", "G0-X"}:
        return 0, 0, 0, 0

    if family == "G0-D":
        if condition == "reference":
            return 0, 0, 0, 0
        pattern = 1 if readout_index % 2 == 0 else 2
        return pattern, (-pattern) % 3, pattern, 1

    if family == "G0-H":
        if condition == "reference":
            return 0, 0, 0, 0
        pattern = 1 if readout_index % 2 == 0 else 2
        return 0, 0, pattern, 0

    if family == "G1-F":
        carry = full_adder_carry(condition)
        return 0, 0, carry, 0

    if family == "G2-P":
        state: object = permutation_carrier(pair_tag, condition)
        identity: object = PERMUTATION_IDENTITY
    elif family == "G2-M":
        state = matrix_carrier(pair_tag, condition)
        identity = MATRIX_IDENTITY
    else:
        raise ValueError("unknown family " + family)

    if state == identity:
        return 0, 0, 0, 0
    code = 1 + stable_int(family, pair_tag, state) % 2
    pattern = code if readout_index % 2 == 0 else (-code) % 3
    return pattern, (-pattern) % 3, pattern, 0


def corrupt(
    value: int,
    probability: float,
    rng: random.Random,
) -> int:
    if rng.random() >= probability:
        return value
    alternatives = tuple(candidate for candidate in range(3) if candidate != value)
    return alternatives[rng.randrange(len(alternatives))]


def render_value(
    value: int,
    gauge: tuple[int, int, int],
    noise_probability: float,
    missing_probability: float,
    rng: random.Random,
) -> str:
    corrupted = corrupt(value, noise_probability, rng)
    if rng.random() < missing_probability:
        return ""
    return str(gauge[corrupted])


def iter_datasets(
    seed: int,
) -> Iterator[tuple[str, str, str, str, str]]:
    for transfer, pairs in registered_pair_splits().items():
        for family in FAMILY_CLASSES:
            for unit_a, unit_b in pairs:
                pair_tag = unit_a + ":" + unit_b
                dataset_id = hashlib.sha256(
                    f"{seed}|{transfer}|{family}|{pair_tag}".encode("utf-8")
                ).hexdigest()[:20]
                opaque_pair_id = hashlib.sha256(
                    f"pair|{seed}|{pair_tag}".encode("utf-8")
                ).hexdigest()[:16]
                yield dataset_id, opaque_pair_id, transfer, family, pair_tag


def generate_bank(
    seed: int,
    observed_path: Path,
    truth_path: Path,
) -> dict[str, object]:
    truth_rows: list[dict[str, object]] = []
    row_count = 0
    with observed_path.open("wb") as raw_handle:
        with gzip.GzipFile(
            fileobj=raw_handle,
            mode="wb",
            filename="",
            mtime=0,
        ) as gzip_handle:
            with io.TextIOWrapper(
                gzip_handle,
                encoding="utf-8",
                newline="",
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=OBSERVED_FIELDS)
                writer.writeheader()
                for (
                    dataset_id,
                    opaque_pair_id,
                    transfer,
                    family,
                    pair_tag,
                ) in iter_datasets(seed):
                    unit_a, unit_b = pair_tag.split(":")
                    truth_rows.append(
                        {
                            "dataset_id": dataset_id,
                            "transfer": transfer,
                            "family": family,
                            "true_class": FAMILY_CLASSES[family],
                            "unit_A": unit_a,
                            "unit_B": unit_b,
                            "pair_tag": pair_tag,
                        }
                    )
                    for repeat in range(REPETITIONS):
                        gauge_index = repeat % len(GAUGES)
                        gauge = GAUGES[gauge_index]
                        noise_probability = NOISE_PROBABILITIES[
                            (repeat // len(GAUGES))
                            % len(NOISE_PROBABILITIES)
                        ]
                        missing_probability = (
                            0.05 if (repeat // 2) % 2 else 0.00
                        )
                        for condition in CONDITIONS:
                            for time_index in range(EPISODE_LENGTH):
                                phase = (
                                    "formation"
                                    if time_index < FORMATION_LENGTH
                                    else "readout"
                                )
                                input_a, input_b = formation_inputs(
                                    family,
                                    condition,
                                    time_index,
                                )
                                base_a = (
                                    stable_int(
                                        "base-a",
                                        seed,
                                        pair_tag,
                                        repeat,
                                    )
                                    + time_index
                                ) % 3
                                base_b = (
                                    stable_int(
                                        "base-b",
                                        seed,
                                        pair_tag,
                                        repeat,
                                    )
                                    + 2 * time_index
                                ) % 3
                                if family == "G0-C":
                                    base_a, base_b = (
                                        (base_a + base_b) % 3,
                                        (base_b + 2 * base_a) % 3,
                                    )
                                base_joint = (base_a + 2 * base_b) % 3
                                effect_a = 0
                                effect_b = 0
                                effect_joint = 0
                                driver = 0
                                if phase == "readout":
                                    (
                                        effect_a,
                                        effect_b,
                                        effect_joint,
                                        driver,
                                    ) = carrier_effect(
                                        family,
                                        pair_tag,
                                        condition,
                                        time_index - FORMATION_LENGTH,
                                    )
                                if family == "G0-X" and phase == "formation":
                                    base_joint = (
                                        base_joint + input_a * input_b
                                    ) % 3
                                true_a = (base_a + effect_a) % 3
                                true_b = (base_b + effect_b) % 3
                                true_joint = (
                                    base_joint + effect_joint
                                ) % 3
                                row = {
                                    "dataset_id": dataset_id,
                                    "opaque_pair_id": opaque_pair_id,
                                    "transfer": transfer,
                                    "repeat": repeat,
                                    "observation_map_id": f"G{gauge_index}",
                                    "noise_probability": (
                                        f"{noise_probability:.2f}"
                                    ),
                                    "missing_probability": (
                                        f"{missing_probability:.2f}"
                                    ),
                                    "condition": condition,
                                    "time": time_index,
                                    "phase": phase,
                                    "input_A": input_a,
                                    "input_B": input_b,
                                    "driver_marker": driver,
                                    "y_A": render_value(
                                        true_a,
                                        gauge,
                                        noise_probability,
                                        missing_probability,
                                        random.Random(
                                            stable_int(
                                                seed,
                                                dataset_id,
                                                repeat,
                                                condition,
                                                time_index,
                                                "A",
                                            )
                                        ),
                                    ),
                                    "y_B": render_value(
                                        true_b,
                                        gauge,
                                        noise_probability,
                                        missing_probability,
                                        random.Random(
                                            stable_int(
                                                seed,
                                                dataset_id,
                                                repeat,
                                                condition,
                                                time_index,
                                                "B",
                                            )
                                        ),
                                    ),
                                    "joint_readout": render_value(
                                        true_joint,
                                        gauge,
                                        noise_probability,
                                        missing_probability,
                                        random.Random(
                                            stable_int(
                                                seed,
                                                dataset_id,
                                                repeat,
                                                condition,
                                                time_index,
                                                "J",
                                            )
                                        ),
                                    ),
                                }
                                writer.writerow(row)
                                row_count += 1
    truth_payload = {
        "schema": SCHEMA,
        "seed": seed,
        "ground_truth": truth_rows,
    }
    write_json(truth_path, truth_payload)
    return {
        "dataset_count": len(truth_rows),
        "observed_row_count": row_count,
        "observed_sha256": sha256_file(observed_path),
        "ground_truth_sha256": sha256_file(truth_path),
    }


def parse_observed_value(value: str) -> int | None:
    return None if value == "" else int(value)


def mismatch_rate(
    records: dict[tuple[str, int, str, int], dict[str, str]],
    gauge: str,
    left_condition: str,
    right_condition: str,
    field: str,
) -> float:
    mismatches = 0
    count = 0
    for (record_gauge, repeat, condition, time_index), left in records.items():
        if record_gauge != gauge or condition != left_condition:
            continue
        right = records.get((gauge, repeat, right_condition, time_index))
        if right is None:
            continue
        left_value = parse_observed_value(left[field])
        right_value = parse_observed_value(right[field])
        if left_value is None or right_value is None:
            continue
        mismatches += left_value != right_value
        count += 1
    if count == 0:
        return 0.0
    return mismatches / count


def gauge_metrics(
    records: dict[tuple[str, int, str, int], dict[str, str]],
    gauge: str,
) -> dict[str, float]:
    history_joint = mismatch_rate(
        records, gauge, "holonomy", "reference", "joint_readout"
    )
    history_a = mismatch_rate(records, gauge, "holonomy", "reference", "y_A")
    history_b = mismatch_rate(records, gauge, "holonomy", "reference", "y_B")

    reset_margin = mismatch_rate(
        records, gauge, "holonomy", "relation_reset", "joint_readout"
    ) - mismatch_rate(
        records, gauge, "reference", "relation_reset", "joint_readout"
    )
    partner_margin = mismatch_rate(
        records,
        gauge,
        "holonomy",
        "partner_substitution",
        "joint_readout",
    ) - mismatch_rate(
        records,
        gauge,
        "reference",
        "partner_substitution",
        "joint_readout",
    )
    remove_a_margin = mismatch_rate(
        records, gauge, "holonomy", "remove_A", "joint_readout"
    ) - mismatch_rate(
        records, gauge, "reference", "remove_A", "joint_readout"
    )
    remove_b_margin = mismatch_rate(
        records, gauge, "holonomy", "remove_B", "joint_readout"
    ) - mismatch_rate(
        records, gauge, "reference", "remove_B", "joint_readout"
    )
    driver_history = mismatch_rate(
        records, gauge, "holonomy", "reference", "driver_marker"
    )
    return {
        "history_joint_mismatch": history_joint,
        "history_A_mismatch": history_a,
        "history_B_mismatch": history_b,
        "reset_margin": reset_margin,
        "partner_margin": partner_margin,
        "remove_A_margin": remove_a_margin,
        "remove_B_margin": remove_b_margin,
        "driver_history_mismatch": driver_history,
    }


def classify(
    metrics: dict[str, float],
    gauge_pass: bool,
) -> tuple[int, dict[str, bool], bool]:
    difference = THRESHOLDS["categorical_difference"]
    margin = THRESHOLDS["counterfactual_margin"]
    bilateral = min(
        metrics["history_A_mismatch"],
        metrics["history_B_mismatch"],
    ) >= difference
    gates = {
        "J_joint_generation": (
            metrics["remove_A_margin"] >= margin
            and metrics["remove_B_margin"] >= margin
        ),
        "H_history": metrics["history_joint_mismatch"] >= difference,
        "I_intervention": metrics["reset_margin"] >= margin,
        "P_pair_specificity": metrics["partner_margin"] >= margin,
        "G_gauge_invariance": gauge_pass,
        "N_null_separation": (
            metrics["driver_history_mismatch"] < difference
        ),
        "T_frozen_transfer": True,
    }
    if all(gates.values()) and bilateral:
        predicted_class = 2
    elif gates["H_history"] and gates["I_intervention"]:
        predicted_class = 1
    else:
        predicted_class = 0
    return predicted_class, gates, bilateral


def analyse_dataset(
    dataset_id: str,
    rows: Iterable[dict[str, str]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    records: dict[tuple[str, int, str, int], dict[str, str]] = {}
    transfer = ""
    for row in rows:
        transfer = row["transfer"]
        if row["phase"] != "readout":
            continue
        key = (
            row["observation_map_id"],
            int(row["repeat"]),
            row["condition"],
            int(row["time"]),
        )
        records[key] = row
    gauges = sorted({key[0] for key in records})
    per_gauge: list[dict[str, object]] = []
    gauge_classes: list[int] = []
    metric_rows: list[dict[str, float]] = []
    for gauge in gauges:
        metrics = gauge_metrics(records, gauge)
        predicted, gates, bilateral = classify(metrics, True)
        gauge_classes.append(predicted)
        metric_rows.append(metrics)
        per_gauge.append(
            {
                "dataset_id": dataset_id,
                "transfer": transfer,
                "observation_map_id": gauge,
                "predicted_class": predicted,
                "bilateral_feedback": bilateral,
                **gates,
                **metrics,
            }
        )
    modal_class = Counter(gauge_classes).most_common(1)[0][0]
    gauge_consistency = (
        sum(value == modal_class for value in gauge_classes)
        / len(gauge_classes)
    )
    aggregate = {
        name: sum(row[name] for row in metric_rows) / len(metric_rows)
        for name in metric_rows[0]
    }
    predicted_class, gates, bilateral = classify(
        aggregate,
        gauge_consistency >= THRESHOLDS["gauge_consistency"],
    )
    prediction = {
        "dataset_id": dataset_id,
        "transfer": transfer,
        "predicted_class": predicted_class,
        **gates,
        "bilateral_feedback": bilateral,
        **{name: f"{value:.12f}" for name, value in aggregate.items()},
        "gauge_consistency": f"{gauge_consistency:.12f}",
    }
    return prediction, per_gauge


def analyse_observed(
    observed_path: Path,
    predictions_path: Path,
    gauge_path: Path,
) -> dict[str, object]:
    predictions: list[dict[str, object]] = []
    gauge_rows: list[dict[str, object]] = []
    with gzip.open(observed_path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for dataset_id, group in itertools.groupby(
            reader,
            key=lambda row: row["dataset_id"],
        ):
            prediction, per_gauge = analyse_dataset(dataset_id, group)
            predictions.append(prediction)
            gauge_rows.extend(per_gauge)
    write_csv(predictions_path, predictions, PREDICTION_FIELDS)
    gauge_fields = tuple(gauge_rows[0].keys())
    write_csv(gauge_path, gauge_rows, gauge_fields)
    prediction_hash = sha256_file(predictions_path)
    prediction_hash_path = predictions_path.with_suffix(
        predictions_path.suffix + ".sha256"
    )
    prediction_hash_path.write_text(
        prediction_hash + "  " + predictions_path.name + "\n",
        encoding="ascii",
    )
    return {
        "prediction_count": len(predictions),
        "gauge_prediction_count": len(gauge_rows),
        "predictions_sha256": prediction_hash,
        "gauge_predictions_sha256": sha256_file(gauge_path),
    }


def read_predictions(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            row["dataset_id"]: row
            for row in csv.DictReader(handle)
        }


def recall_for(
    truth_rows: Sequence[dict[str, object]],
    predictions: dict[str, dict[str, str]],
    true_class: int,
) -> float:
    selected = [
        row for row in truth_rows if int(row["true_class"]) == true_class
    ]
    return (
        sum(
            int(predictions[str(row["dataset_id"])]["predicted_class"])
            == true_class
            for row in selected
        )
        / len(selected)
    )


def score_predictions(
    truth_path: Path,
    predictions_path: Path,
    metrics_path: Path,
) -> dict[str, object]:
    hash_path = predictions_path.with_suffix(predictions_path.suffix + ".sha256")
    registered_hash = hash_path.read_text(encoding="ascii").split()[0]
    if sha256_file(predictions_path) != registered_hash:
        fail("prediction hash changed before scoring")

    truth_payload = json.loads(truth_path.read_text(encoding="utf-8"))
    truth_rows = truth_payload["ground_truth"]
    predictions = read_predictions(predictions_path)
    truth_ids = {str(row["dataset_id"]) for row in truth_rows}
    if set(predictions) != truth_ids:
        fail("prediction and ground-truth dataset IDs differ")

    metric_rows: list[dict[str, object]] = []
    transfer_summary: dict[str, object] = {}
    required_checks: dict[str, bool] = {}
    for transfer in ("T1", "T2", "T3"):
        selected = [
            row for row in truth_rows if row["transfer"] == transfer
        ]
        recalls = {
            str(true_class): recall_for(selected, predictions, true_class)
            for true_class in (0, 1, 2)
        }
        balanced_accuracy = sum(recalls.values()) / 3
        non_class2 = [
            row for row in selected if int(row["true_class"]) < 2
        ]
        false_class2 = (
            sum(
                int(predictions[str(row["dataset_id"])]["predicted_class"])
                == 2
                for row in non_class2
            )
            / len(non_class2)
        )
        transfer_summary[transfer] = {
            "balanced_accuracy": balanced_accuracy,
            "recall_by_class": recalls,
            "false_class2_rate": false_class2,
        }
        required_checks[f"{transfer}_balanced_accuracy"] = (
            balanced_accuracy
            >= ACCEPTANCE["balanced_accuracy_each_transfer"]
        )
        required_checks[f"{transfer}_class_recalls"] = all(
            value >= ACCEPTANCE["recall_each_class_each_transfer"]
            for value in recalls.values()
        )
        metric_rows.append(
            {
                "scope": transfer,
                "balanced_accuracy": f"{balanced_accuracy:.12f}",
                "class0_recall": f"{recalls['0']:.12f}",
                "class1_recall": f"{recalls['1']:.12f}",
                "class2_recall": f"{recalls['2']:.12f}",
                "false_class2_rate": f"{false_class2:.12f}",
            }
        )

    all_non_class2 = [
        row for row in truth_rows if int(row["true_class"]) < 2
    ]
    overall_false_class2 = (
        sum(
            int(predictions[str(row["dataset_id"])]["predicted_class"]) == 2
            for row in all_non_class2
        )
        / len(all_non_class2)
    )

    family_recalls: dict[str, float] = {}
    for family in FAMILY_CLASSES:
        selected = [row for row in truth_rows if row["family"] == family]
        family_recalls[family] = (
            sum(
                int(predictions[str(row["dataset_id"])]["predicted_class"])
                == int(row["true_class"])
                for row in selected
            )
            / len(selected)
        )

    gauge_consistency = sum(
        float(row["gauge_consistency"])
        for row in predictions.values()
    ) / len(predictions)

    required_checks.update(
        {
            "overall_false_class2_rate": (
                overall_false_class2 <= ACCEPTANCE["false_class2_rate"]
            ),
            "G2-P_recall": (
                family_recalls["G2-P"] >= ACCEPTANCE["g2p_recall"]
            ),
            "G2-M_recall": (
                family_recalls["G2-M"] >= ACCEPTANCE["g2m_recall"]
            ),
            "gauge_consistency": (
                gauge_consistency >= ACCEPTANCE["gauge_consistency"]
            ),
        }
    )
    write_csv(
        metrics_path,
        metric_rows,
        (
            "scope",
            "balanced_accuracy",
            "class0_recall",
            "class1_recall",
            "class2_recall",
            "false_class2_rate",
        ),
    )
    return {
        "status": "ok" if all(required_checks.values()) else "failed",
        "transfer": transfer_summary,
        "overall_false_class2_rate": overall_false_class2,
        "family_recall": family_recalls,
        "gauge_consistency": gauge_consistency,
        "required_checks": required_checks,
        "predictions_sha256_verified_before_unblinding": registered_hash,
    }


def source_paths() -> dict[str, Path]:
    directory = Path(__file__).resolve().parent
    return {
        "README.md": directory / "README.md",
        "PREREGISTRATION.md": directory / "PREREGISTRATION.md",
        "PREREGISTRATION_EMAIL.md": directory / "PREREGISTRATION_EMAIL.md",
        "run.py": directory / "run.py",
        "test_run.py": directory / "test_run.py",
    }


def verify_registration_manifest() -> dict[str, object]:
    directory = Path(__file__).resolve().parent
    manifest_path = directory / "registration_manifest.json"
    if not manifest_path.is_file():
        fail("missing registration_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hashes = manifest.get("source_sha256", {})
    for name, path in source_paths().items():
        observed = sha256_file(path)
        if expected_hashes.get(name) != observed:
            fail(f"registered source hash mismatch: {name}")
    if manifest.get("confirmatory_seed") != CONFIRMATORY_SEED:
        fail("confirmatory seed differs from registration manifest")
    if manifest.get("thresholds") != THRESHOLDS:
        fail("thresholds differ from registration manifest")
    if manifest.get("acceptance") != ACCEPTANCE:
        fail("acceptance targets differ from registration manifest")
    return manifest


def run_bank(
    mode: str,
    out_dir: Path,
    check: bool,
) -> dict[str, object]:
    if out_dir.exists():
        fail("output directory already exists: " + str(out_dir))
    if mode == "confirmatory":
        registration_manifest = verify_registration_manifest()
        seed = CONFIRMATORY_SEED
    elif mode == "development":
        registration_manifest = {"status": "development-only"}
        seed = DEVELOPMENT_SEED
    else:
        raise ValueError(mode)

    out_dir.mkdir(parents=True)
    observed_path = out_dir / "observed.csv.gz"
    truth_path = out_dir / "ground_truth.sealed.json"
    predictions_path = out_dir / "predictions.csv"
    gauge_path = out_dir / "gauge_predictions.csv"
    metrics_path = out_dir / "metrics.csv"

    generation = generate_bank(seed, observed_path, truth_path)
    analysis = analyse_observed(observed_path, predictions_path, gauge_path)
    scoring = score_predictions(truth_path, predictions_path, metrics_path)

    exact_checks = exact_self_test()
    split_checks = validate_pair_splits()
    status = (
        "ok"
        if scoring["status"] == "ok"
        and all(exact_checks.values())
        and all(split_checks.values())
        else "failed"
    )
    first_sequence_step = (
        "registration hashes verified"
        if mode == "confirmatory"
        else "development source loaded"
    )
    summary = {
        "schema": SCHEMA,
        "mode": mode,
        "status": status,
        "seed": seed,
        "registration_manifest": registration_manifest,
        "sequence": [
            first_sequence_step,
            "observed and sealed ground-truth tables generated",
            "observed table analysed without ground truth",
            "prediction file hashed",
            "ground truth unsealed for scoring",
            "registered acceptance targets evaluated",
        ],
        "generation": generation,
        "analysis": analysis,
        "scoring": scoring,
        "exact_checks": exact_checks,
        "split_checks": split_checks,
        "claim_boundary": {
            "computed": (
                "The frozen classifier was evaluated on the registered "
                "synthetic generator bank."
            ),
            "not_established": [
                "a relational carrier in an external measurement system",
                "identity between an operational carrier and subjectivity",
                "ontological irreducibility",
                "uniqueness outside the registered alternatives",
            ],
        },
    }
    write_json(out_dir / "summary.json", summary)
    output_files = {
        path.name: sha256_file(path)
        for path in sorted(out_dir.iterdir())
        if path.is_file()
    }
    write_json(
        out_dir / "output_manifest.json",
        {
            "schema": SCHEMA,
            "mode": mode,
            "files_before_manifest": output_files,
        },
    )

    print("status =", status)
    for transfer, values in scoring["transfer"].items():
        print(
            transfer,
            "balanced_accuracy =",
            f"{values['balanced_accuracy']:.6f}",
            "recall =",
            values["recall_by_class"],
        )
    print(
        "false_class2_rate =",
        f"{scoring['overall_false_class2_rate']:.6f}",
    )
    print("G2-P_recall =", f"{scoring['family_recall']['G2-P']:.6f}")
    print("G2-M_recall =", f"{scoring['family_recall']['G2-M']:.6f}")
    print("gauge_consistency =", f"{scoring['gauge_consistency']:.6f}")
    print("wrote", out_dir)
    if check and status != "ok":
        fail("registered acceptance targets failed")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("self-test", "development", "confirmatory"),
        required=True,
    )
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "self-test":
        checks = {**exact_self_test(), **validate_pair_splits()}
        for name, passed in checks.items():
            print(name, "=", passed)
        if args.check and not all(checks.values()):
            fail("self-test failed")
        return
    if args.out_dir is None:
        fail("--out-dir is required for development and confirmatory modes")
    run_bank(args.mode, args.out_dir.resolve(), args.check)


if __name__ == "__main__":
    main()
