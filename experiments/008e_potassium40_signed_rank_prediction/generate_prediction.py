#!/usr/bin/env python3
"""Generate the target-free E008E potassium-40 numerical prediction."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
CONSTRUCTION = json.loads(
    (ROOT / "construction_sources.json").read_text(encoding="utf-8")
)


def _central(row: dict[str, float]) -> float:
    return float(row["value"])


def second_order_constants(
    spin: float,
    magnetic_moment: float,
    quadrupole_moment: float,
    t1: float,
    t2: float,
    fine_structure_cm_inverse: float,
    wavenumber_to_mhz: float,
) -> dict[str, float]:
    """Return eta and zeta in kHz for P_1/2 <-> P_3/2 mixing."""
    if spin <= 0.5:
        raise ValueError("M1-E2 construction requires nuclear spin above one half")
    denominator_mhz = fine_structure_cm_inverse * wavenumber_to_mhz
    nuclear_factor = (spin + 1.0) * (2.0 * spin + 1.0) / spin
    eta_khz = (
        nuclear_factor
        * magnetic_moment**2
        * t1**2
        / denominator_mhz
        * 1000.0
    )
    zeta_khz = (
        nuclear_factor
        * math.sqrt((2.0 * spin + 3.0) / (2.0 * spin - 1.0))
        * magnetic_moment
        * quadrupole_moment
        * t1
        * t2
        / denominator_mhz
        * 1000.0
    )
    return {"eta_khz": eta_khz, "zeta_khz": zeta_khz}


def correction_coefficients(spin: float) -> dict[str, float]:
    """General-I coefficients for the leading P-state second-order returns."""
    eta_a12 = 1.0 / (6.0 * spin * (spin + 1.0) * (2.0 * spin + 1.0))
    zeta_a12 = eta_a12 * math.sqrt(
        3.0 * (2.0 * spin - 1.0) * (2.0 * spin + 3.0) / 5.0
    )
    return {
        "A_P1_2_from_eta": eta_a12,
        "A_P1_2_from_zeta": zeta_a12,
        "A_P3_2_from_eta": eta_a12 / 2.0,
        "A_P3_2_from_zeta": -zeta_a12 / 10.0,
        "B_P3_2_from_eta": spin * (2.0 * spin - 1.0) * eta_a12,
        "B_P3_2_from_zeta": 3.0 * spin / (2.0 * spin + 3.0) * zeta_a12,
    }


def corrections(spin: float, constants: dict[str, float]) -> dict[str, float]:
    coefficients = correction_coefficients(spin)
    eta = constants["eta_khz"]
    zeta = constants["zeta_khz"]
    return {
        "delta_A_P1_2_khz": (
            coefficients["A_P1_2_from_eta"] * eta
            + coefficients["A_P1_2_from_zeta"] * zeta
        ),
        "delta_A_P3_2_khz": (
            coefficients["A_P3_2_from_eta"] * eta
            + coefficients["A_P3_2_from_zeta"] * zeta
        ),
        "delta_B_P3_2_khz": (
            coefficients["B_P3_2_from_eta"] * eta
            + coefficients["B_P3_2_from_zeta"] * zeta
        ),
    }


def calculate_isotope(
    isotope: dict[str, Any], t1: float, t2: float, fine_structure: float
) -> dict[str, Any]:
    spin = float(isotope["nuclear_spin_I"])
    constants = second_order_constants(
        spin,
        _central(isotope["magnetic_moment_mu_N"]),
        _central(isotope["quadrupole_moment_barn"]),
        t1,
        t2,
        fine_structure,
        float(CONSTRUCTION["physical_constants"]["wavenumber_to_MHz"]),
    )
    return {
        "nuclear_spin_I": spin,
        "second_order_constants": constants,
        "coefficient_map": correction_coefficients(spin),
        "predicted_corrections": corrections(spin, constants),
    }


def _endpoints(row: dict[str, float], uncertainty_key: str) -> tuple[float, float]:
    value = float(row["value"])
    uncertainty = float(row[uncertainty_key])
    return value - uncertainty, value + uncertainty


def _common_corners() -> Iterable[tuple[float, float, float]]:
    electronic = CONSTRUCTION["electronic_inputs"]
    ranges = [
        _endpoints(electronic["T1_MHz_per_muN"], "display_rounding_half_width"),
        _endpoints(electronic["T2_MHz_per_barn"], "display_rounding_half_width"),
        _endpoints(
            electronic["fine_structure_interval_cm_inverse"],
            "display_rounding_half_width",
        ),
    ]
    return itertools.product(*ranges)


def isotope_envelope(name: str) -> dict[str, dict[str, float]]:
    isotope = CONSTRUCTION["nuclear_inputs"][name]
    spin = float(isotope["nuclear_spin_I"])
    mu_range = _endpoints(isotope["magnetic_moment_mu_N"], "quoted_uncertainty")
    q_range = _endpoints(isotope["quadrupole_moment_barn"], "quoted_uncertainty")
    samples: dict[str, list[float]] = {
        "eta_khz": [],
        "zeta_khz": [],
        "delta_A_P1_2_khz": [],
        "delta_A_P3_2_khz": [],
        "delta_B_P3_2_khz": [],
    }
    for t1, t2, fine_structure in _common_corners():
        for mu, quadrupole in itertools.product(mu_range, q_range):
            constants = second_order_constants(
                spin,
                mu,
                quadrupole,
                t1,
                t2,
                fine_structure,
                float(CONSTRUCTION["physical_constants"]["wavenumber_to_MHz"]),
            )
            values = {**constants, **corrections(spin, constants)}
            for key in samples:
                samples[key].append(values[key])
    return {
        key: {"min": min(values), "max": max(values)}
        for key, values in samples.items()
    }


def ratio_envelope(numerator: str, denominator: str) -> dict[str, dict[str, float]]:
    isotopes = CONSTRUCTION["nuclear_inputs"]
    top = isotopes[numerator]
    bottom = isotopes[denominator]
    top_mu = _endpoints(top["magnetic_moment_mu_N"], "quoted_uncertainty")
    top_q = _endpoints(top["quadrupole_moment_barn"], "quoted_uncertainty")
    bottom_mu = _endpoints(
        bottom["magnetic_moment_mu_N"], "quoted_uncertainty"
    )
    bottom_q = _endpoints(
        bottom["quadrupole_moment_barn"], "quoted_uncertainty"
    )
    keys = ("delta_A_P1_2_khz", "delta_A_P3_2_khz", "delta_B_P3_2_khz")
    samples = {key: [] for key in keys}
    for t1, t2, fine_structure in _common_corners():
        for mu_top, q_top, mu_bottom, q_bottom in itertools.product(
            top_mu, top_q, bottom_mu, bottom_q
        ):
            top_constants = second_order_constants(
                float(top["nuclear_spin_I"]),
                mu_top,
                q_top,
                t1,
                t2,
                fine_structure,
                float(CONSTRUCTION["physical_constants"]["wavenumber_to_MHz"]),
            )
            bottom_constants = second_order_constants(
                float(bottom["nuclear_spin_I"]),
                mu_bottom,
                q_bottom,
                t1,
                t2,
                fine_structure,
                float(CONSTRUCTION["physical_constants"]["wavenumber_to_MHz"]),
            )
            top_corrections = corrections(float(top["nuclear_spin_I"]), top_constants)
            bottom_corrections = corrections(
                float(bottom["nuclear_spin_I"]), bottom_constants
            )
            for key in keys:
                samples[key].append(top_corrections[key] / bottom_corrections[key])
    return {
        key: {"min": min(values), "max": max(values)}
        for key, values in samples.items()
    }


def generate() -> dict[str, Any]:
    electronic = CONSTRUCTION["electronic_inputs"]
    t1 = _central(electronic["T1_MHz_per_muN"])
    t2 = _central(electronic["T2_MHz_per_barn"])
    fine_structure = _central(electronic["fine_structure_interval_cm_inverse"])
    isotopes = {
        name: calculate_isotope(row, t1, t2, fine_structure)
        for name, row in CONSTRUCTION["nuclear_inputs"].items()
    }
    target = isotopes["K-40"]
    ratios = {}
    for denominator in ("K-39", "K-41"):
        ratios[f"K-40_over_{denominator}"] = {
            key: target["predicted_corrections"][key]
            / isotopes[denominator]["predicted_corrections"][key]
            for key in target["predicted_corrections"]
        }
    return {
        "schema": "siel-e008e-prediction-before-benchmark-v1",
        "experiment": "008e_potassium40_signed_rank_prediction",
        "prediction_status": "NOVEL_NUMERICAL_PREDICTION_AWAITING_INDEPENDENT_BENCHMARK",
        "target_values_loaded": False,
        "known_K40_second_order_values_loaded": False,
        "free_fitted_parameters": 0,
        "primary_target": "K-40 neutral-potassium 4P second-order delta_A(P_1/2) in kHz",
        "secondary_targets": [
            "K-40 delta_A(P_3/2) in kHz",
            "K-40 delta_B(P_3/2) in kHz",
            "K-40/K-39 and K-40/K-41 generated correction ratios"
        ],
        "construction": {
            "electronic_relation": "rank-one T1 and rank-two T2 are connected separately before second-order composition",
            "fine_structure_interval_cm_inverse": fine_structure,
            "T1_MHz_per_muN": t1,
            "T2_MHz_per_barn": t2,
        },
        "isotope_predictions": isotopes,
        "input_uncertainty_envelopes": {
            name: isotope_envelope(name) for name in isotopes
        },
        "generated_ratios": ratios,
        "generated_ratio_envelopes": {
            "K-40_over_K-39": ratio_envelope("K-40", "K-39"),
            "K-40_over_K-41": ratio_envelope("K-40", "K-41"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(generate(), indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")
        print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
