#!/usr/bin/env python3
"""Execute the frozen E016 pointed-Braid CKM derivation confirmation."""

from fractions import Fraction
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
INPUT = json.loads((HERE / "frozen_input.json").read_text())


def cmat(raw):
    return np.array([
        [complex(float(Fraction(x["re"])), float(Fraction(x["im"]))) for x in row]
        for row in raw
    ])


def basis(matrix):
    values, vectors = np.linalg.eigh(matrix @ matrix.conj().T)
    return vectors[:, np.argsort(values)]


def block(left, right, matter):
    return left @ matter @ right + right @ matter @ left


def derive(clock_weights, matter_weights, matter, use_star=True):
    clock = np.asarray(clock_weights, dtype=float)
    clock /= clock.sum()
    marks = np.asarray(matter_weights, dtype=float)
    marks /= marks.sum()
    q = np.sqrt(clock * marks)
    q /= q.sum()
    p3 = np.diag([1.0, 0.0, 0.0])
    p2 = np.diag([0.0, 1.0, 0.0])
    p1 = np.diag([0.0, 0.0, 1.0])
    response = (
        q[2] * q[0] * block(p3, p2, matter)
        + q[2] * q[1] * block(p3, p1, matter)
    ) if use_star else np.zeros_like(matter)
    mixing = basis(matter + response).conj().T @ basis(matter - response)
    return q, np.array([q[2] * q[0], q[2] * q[1], 0.0]), mixing


def main():
    matter = cmat(INPUT["matter_base"])
    primary_q, primary_coefficients, mixing = derive(
        INPUT["clock_weights"], INPUT["matter_weights_in_word_order"], matter
    )
    derived = np.abs(mixing)

    _, _, uniform = derive([1, 1, 1], INPUT["matter_weights_in_word_order"], matter)
    _, _, broken = derive(INPUT["clock_weights"], [10, 4, 10], matter)
    _, _, no_star = derive(
        INPUT["clock_weights"], INPUT["matter_weights_in_word_order"], matter, False
    )

    final_q = np.asarray(INPUT["frozen_final_law"]["hellinger_cross_state"])
    c = INPUT["frozen_final_law"]["pair_star_coefficients"]
    final_coefficients = np.array([c["e3_e2"], c["e3_e1"], c["e2_e1"]])
    expected = np.asarray(INPUT["frozen_expected_ckm_modulus"])
    observed = np.asarray(INPUT["post_derivation_measurement_table"]["central"])
    sigma = np.asarray(INPUT["post_derivation_measurement_table"]["one_sigma"])
    tol = INPUT["tolerances"]
    pulls = np.abs(derived - observed) / sigma

    tests = {
        "source_words_and_pointing_fixed": (
            INPUT["clock_words"] == ["r1", "r2", "r121"]
            and INPUT["word_to_axis"] == {"r1": "e2", "r2": "e1", "r121": "e3"}
        ),
        "source_weights_fixed": (
            INPUT["clock_weights"] == [7, 4, 4]
            and INPUT["matter_weights_in_word_order"] == [4, 10, 10]
        ),
        "final_cross_state_reproduced": bool(np.max(np.abs(primary_q - final_q)) < tol["exact_reproduction"]),
        "final_pair_star_reproduced": bool(np.max(np.abs(primary_coefficients - final_coefficients)) < tol["exact_reproduction"]),
        "frozen_ckm_reproduced": bool(np.max(np.abs(derived - expected)) < tol["exact_reproduction"]),
        "unitary": bool(np.linalg.norm(mixing.conj().T @ mixing - np.eye(3)) < tol["exact_reproduction"]),
        "all_nine_within_five_sigma": bool(np.max(pulls) <= tol["maximum_element_pull_sigma"]),
        "uniform_clock_changes_output": bool(np.linalg.norm(derived - np.abs(uniform)) > tol["minimum_control_distance"]),
        "broken_pointing_changes_output": bool(np.linalg.norm(derived - np.abs(broken)) > tol["minimum_control_distance"]),
        "removed_pair_star_changes_output": bool(np.linalg.norm(derived - np.abs(no_star)) > tol["minimum_control_distance"]),
    }

    result = {
        "schema": "siel.e016.braid-ckm-derivation-confirmation.result.v1",
        "experiment_id": "E016",
        "status": "PASS" if all(tests.values()) else "FAIL",
        "derived_ckm_modulus": derived.tolist(),
        "hellinger_cross_state": primary_q.tolist(),
        "pair_star_coefficients": {
            "e3_e2": float(primary_coefficients[0]),
            "e3_e1": float(primary_coefficients[1]),
            "e2_e1": float(primary_coefficients[2]),
        },
        "unitarity_residual": float(np.linalg.norm(mixing.conj().T @ mixing - np.eye(3))),
        "frozen_output_max_abs_residual": float(np.max(np.abs(derived - expected))),
        "measurement_comparison": {
            "frobenius_distance": float(np.linalg.norm(derived - observed)),
            "maximum_element_pull_sigma": float(np.max(pulls)),
            "all_nine_within_five_sigma": bool(np.max(pulls) <= tol["maximum_element_pull_sigma"]),
        },
        "controls": {
            "uniform_clock_distance": float(np.linalg.norm(derived - np.abs(uniform))),
            "broken_pointing_distance": float(np.linalg.norm(derived - np.abs(broken))),
            "pair_star_removed_distance": float(np.linalg.norm(derived - np.abs(no_star))),
        },
        "tests": tests,
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
