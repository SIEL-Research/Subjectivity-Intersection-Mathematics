#!/usr/bin/env python3
"""Broad synthetic atomic parameter stress without executing reserved isotope targets."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
MASS_RATIOS = (1.0, 10.0, 100.0, 1000.0, 10000.0)
CHARGES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
REMOVAL_STEPS = 400
RETURN_STEPS = (100, 200, 400, 800)


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    fingerprint = load("e014_fingerprint_atomic_stress", "run_distributional_fingerprint.py")
    n = 512
    half_width = 100.0
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=dx)
    reference = np.zeros_like(x)
    rows = []
    for mass_ratio in MASS_RATIOS:
        reduced_mass = mass_ratio / (mass_ratio + 1.0)
        for charge in CHARGES:
            native = -charge / np.sqrt(x * x + 0.8**2)
            mismatch = -charge / np.sqrt((x - 8.0) ** 2 + 0.8**2)

            def step(psi, potential, damping):
                dt = 0.02
                complex_time = damping + 1j
                psi = np.exp(-complex_time * potential * dt / 2.0) * psi
                kinetic = k * k / (2.0 * reduced_mass)
                psi = np.fft.ifft(np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi))
                psi = np.exp(-complex_time * potential * dt / 2.0) * psi
                return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))

            ground = np.exp(-x * x / 2.0).astype(complex)
            ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
            for _ in range(4000):
                ground = step(ground, native, 0.50)

            def advance(initial, potential, steps):
                state = initial.copy()
                for _ in range(steps):
                    state = step(state, potential, 0.08)
                return state

            def snapshots(initial, potential, requested):
                state = initial.copy()
                output = {}
                for index in range(1, max(requested) + 1):
                    state = step(state, potential, 0.08)
                    if index in requested:
                        output[index] = state.copy()
                return output

            removed_at_return = advance(ground, reference, REMOVAL_STEPS)
            totals = tuple(REMOVAL_STEPS + value for value in RETURN_STEPS)
            intact_states = snapshots(ground, native, totals)
            removed_states = snapshots(ground, reference, totals)
            correct_states = snapshots(removed_at_return, native, RETURN_STEPS)
            mismatch_states = snapshots(removed_at_return, mismatch, RETURN_STEPS)
            checkpoints = {}
            for returned in RETURN_STEPS:
                densities = {
                    "intact": np.abs(intact_states[REMOVAL_STEPS + returned]) ** 2 * dx,
                    "removed": np.abs(removed_states[REMOVAL_STEPS + returned]) ** 2 * dx,
                    "correct_return": np.abs(correct_states[returned]) ** 2 * dx,
                    "mismatched_return": np.abs(mismatch_states[returned]) ** 2 * dx,
                }
                for key in densities:
                    densities[key] /= float(np.sum(densities[key]))
                scores = {
                    "intact": 1.0,
                    "removed": fingerprint.js_similarity(densities["removed"], densities["intact"]),
                    "correct_return": fingerprint.js_similarity(densities["correct_return"], densities["intact"]),
                    "mismatched_return": fingerprint.js_similarity(densities["mismatched_return"], densities["intact"]),
                }
                checkpoints[returned] = scores
            for returned, scores in sorted(checkpoints.items()):
                margin = scores["correct_return"] - max(scores["removed"], scores["mismatched_return"])
                rows.append({
                    "mass_ratio": mass_ratio,
                    "charge": charge,
                    "reduced_mass": reduced_mass,
                    "return_steps": returned,
                    "scores": scores,
                    "specificity_margin": margin,
                    "specificity_pass": margin > 0.0,
                })
    late = [row for row in rows if row["return_steps"] >= 200]
    summary = {
        "schema": "siel-e014-atomic-parameter-stress-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "mass_ratios": list(MASS_RATIOS),
            "charges": list(CHARGES),
            "grid_points": n,
            "return_steps": list(RETURN_STEPS),
            "reserved_named_isotope_targets_executed": False,
        },
        "all_checks": {
            "count": len(rows),
            "pass_fraction": float(np.mean([row["specificity_pass"] for row in rows])),
            "minimum_margin": min(row["specificity_margin"] for row in rows),
        },
        "stabilized_checks_return_200_or_later": {
            "count": len(late),
            "pass_fraction": float(np.mean([row["specificity_pass"] for row in late])),
            "minimum_margin": min(row["specificity_margin"] for row in late),
        },
        "failures": [row for row in rows if not row["specificity_pass"]],
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "synthetic_parameter_stress_not_isotope_confirmation": True,
            "reduced_soft_coulomb_models_only": True,
        },
    }
    (RESULTS / "atomic_parameter_stress_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Atomic parameter stress",
        "",
        f"All checks pass fraction: `{summary['all_checks']['pass_fraction']:.6f}`.",
        f"Stabilized checks pass fraction: `{summary['stabilized_checks_return_200_or_later']['pass_fraction']:.6f}`.",
        f"Stabilized minimum margin: `{summary['stabilized_checks_return_200_or_later']['minimum_margin']:.9f}`.",
        "",
        "Named reserved isotope targets were not executed. This is synthetic result-informed exploration.",
    ]
    (RESULTS / "ATOMIC_PARAMETER_STRESS_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all": summary["all_checks"],
        "stabilized": summary["stabilized_checks_return_200_or_later"],
        "failure_count": len(summary["failures"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
