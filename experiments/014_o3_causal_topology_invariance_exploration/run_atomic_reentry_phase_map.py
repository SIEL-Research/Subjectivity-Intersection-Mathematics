#!/usr/bin/env python3
"""Atomic O3 removal-return phase map using full density fingerprints."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REPO_ROOT = ROOT.parents[1]
REMOVAL_DURATIONS = (50, 100, 200, 400, 800)
RETURN_DURATIONS = (100, 200, 400, 800, 1200)
TARGETS = {
    "tritium": {"mass_ratio": 5496.92153551, "charge": 1.0},
    "helium3_hydrogenic": {"mass_ratio": 5495.88527984, "charge": 2.0},
}


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def snapshots(initial, potential, requested, step):
    state = initial.copy()
    output = {}
    for index in range(1, max(requested) + 1):
        state = step(state, potential)
        if index in requested:
            output[index] = state.copy()
    return output


def main() -> None:
    fingerprint = load("e014_fingerprint_atomic_phase", "run_distributional_fingerprint.py")
    n = 1024
    half_width = 100.0
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=dx)
    reference = np.zeros_like(x)
    softening = 0.8
    mismatch_shift = 8.0
    rows = []
    for target_name, target in TARGETS.items():
        reduced_mass = target["mass_ratio"] / (target["mass_ratio"] + 1.0)
        native = -target["charge"] / np.sqrt(x * x + softening * softening)
        mismatch = -target["charge"] / np.sqrt((x - mismatch_shift) ** 2 + softening * softening)

        def make_step(damping):
            def step(psi, potential):
                dt = 0.02
                complex_time = damping + 1j
                psi = np.exp(-complex_time * potential * dt / 2.0) * psi
                kinetic = k * k / (2.0 * reduced_mass)
                psi = np.fft.ifft(np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi))
                psi = np.exp(-complex_time * potential * dt / 2.0) * psi
                return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))
            return step

        ground_step = make_step(0.50)
        dynamic_step = make_step(0.08)
        ground = np.exp(-x * x / 2.0).astype(complex)
        ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
        for _ in range(4000):
            ground = ground_step(ground, native)

        totals = sorted({removal + returned for removal in REMOVAL_DURATIONS for returned in RETURN_DURATIONS})
        intact_states = snapshots(ground, native, totals, dynamic_step)
        removed_states = snapshots(ground, reference, sorted(set(REMOVAL_DURATIONS) | set(totals)), dynamic_step)
        for removal in REMOVAL_DURATIONS:
            removed_at_return = removed_states[removal]
            correct_states = snapshots(removed_at_return, native, RETURN_DURATIONS, dynamic_step)
            mismatch_states = snapshots(removed_at_return, mismatch, RETURN_DURATIONS, dynamic_step)
            for returned in RETURN_DURATIONS:
                intact_density = np.abs(intact_states[removal + returned]) ** 2 * dx
                removed_density = np.abs(removed_states[removal + returned]) ** 2 * dx
                correct_density = np.abs(correct_states[returned]) ** 2 * dx
                mismatch_density = np.abs(mismatch_states[returned]) ** 2 * dx
                intact_density /= float(np.sum(intact_density))
                removed_density /= float(np.sum(removed_density))
                correct_density /= float(np.sum(correct_density))
                mismatch_density /= float(np.sum(mismatch_density))
                scores = {
                    "intact": 1.0,
                    "removed": fingerprint.js_similarity(removed_density, intact_density),
                    "mismatched_return": fingerprint.js_similarity(mismatch_density, intact_density),
                    "correct_return": fingerprint.js_similarity(correct_density, intact_density),
                }
                margin = scores["correct_return"] - max(scores["removed"], scores["mismatched_return"])
                rows.append({
                    "target": target_name,
                    "nuclear_charge": target["charge"],
                    "reduced_mass": reduced_mass,
                    "removal_steps": removal,
                    "return_steps": returned,
                    "return_to_removal_ratio": returned / removal,
                    "scores": scores,
                    "causal_margin": margin,
                    "causal_pass": margin > 0.0,
                })

    def aggregate(selected):
        return {
            "configurations": len(selected),
            "pass_fraction": float(np.mean([row["causal_pass"] for row in selected])),
            "minimum_margin": min(row["causal_margin"] for row in selected),
            "median_margin": float(np.median([row["causal_margin"] for row in selected])),
            "mean_correct_similarity": float(np.mean([row["scores"]["correct_return"] for row in selected])),
        }
    summary = {
        "schema": "siel-e014-atomic-reentry-phase-map-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "targets": TARGETS,
            "removal_durations": list(REMOVAL_DURATIONS),
            "return_durations": list(RETURN_DURATIONS),
            "mismatch": "nonperiodic physical translation of the soft-Coulomb centre by 8 bohr",
            "whole_fingerprint": "normalized Jensen-Shannon similarity of the full density to matched intact dynamics",
        },
        "overall": aggregate(rows),
        "by_target": {name: aggregate([row for row in rows if row["target"] == name]) for name in TARGETS},
        "by_removal": {str(value): aggregate([row for row in rows if row["removal_steps"] == value]) for value in REMOVAL_DURATIONS},
        "by_return": {str(value): aggregate([row for row in rows if row["return_steps"] == value]) for value in RETURN_DURATIONS},
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "targets_previously_used_in_E013": True,
            "density_fingerprint_selected_after_molecular_exploration": True,
            "reduced_soft_coulomb_models_only": True,
        },
    }
    (RESULTS / "atomic_reentry_phase_map_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Atomic O3 re-entry phase-map exploration",
        "",
        f"Configurations: `{summary['overall']['configurations']}`.",
        f"Pass fraction: `{summary['overall']['pass_fraction']:.6f}`.",
        f"Minimum causal margin: `{summary['overall']['minimum_margin']:.9f}`.",
        "",
        "This is result-informed local exploration in reduced soft-Coulomb models.",
    ]
    (RESULTS / "ATOMIC_REENTRY_PHASE_MAP_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"overall": summary["overall"], "by_target": summary["by_target"], "by_removal": summary["by_removal"], "by_return": summary["by_return"]}, sort_keys=True))


if __name__ == "__main__":
    main()
