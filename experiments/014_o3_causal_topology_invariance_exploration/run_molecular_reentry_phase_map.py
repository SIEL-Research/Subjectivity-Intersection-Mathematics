#!/usr/bin/env python3
"""Exact molecular removal-return phase map for history-dependent O3 re-entry."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TEMPERATURES = (0.0005, 0.001, 0.002, 0.004, 0.008)
REMOVAL_DURATIONS = (5, 10, 20, 40, 80, 160, 320)
RETURN_DURATIONS = (10, 25, 50, 100, 200, 400, 800)


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def transition(surface: np.ndarray, temperature: float) -> np.ndarray:
    size = len(surface)
    matrix = np.zeros((size, size), dtype=float)
    for index in range(size):
        neighbours = [item for item in (index - 1, index + 1) if 0 <= item < size]
        for proposed in neighbours:
            log_acceptance = -float(surface[proposed] - surface[index]) / temperature
            acceptance = 1.0 if log_acceptance >= 0.0 else math.exp(max(log_acceptance, -745.0))
            proposal = 1.0 / len(neighbours)
            matrix[index, proposed] += proposal * acceptance
            matrix[index, index] += proposal * (1.0 - acceptance)
    return matrix


def propagate(distribution: np.ndarray, matrix: np.ndarray, steps: int) -> np.ndarray:
    output = distribution @ np.linalg.matrix_power(matrix, steps)
    output = np.maximum(output, 0.0)
    return output / float(np.sum(output))


def select_nonperiodic_mismatch(base, physical, profile_name, profile, profiles):
    native = np.asarray(profile["native"], dtype=float)
    reference = np.asarray(profile["reference"], dtype=float)
    candidate = native - reference
    alternatives = physical.alternatives_for(profile_name, profile, profiles)
    eligible = []
    for label, (alternative, family) in alternatives.items():
        if family not in ("nonperiodic_coordinate_translation", "finite_coordinate_reflection", "affine_coordinate_warp"):
            continue
        overlap = base.centered_overlap(candidate, alternative)
        if overlap <= base.MAX_OVERLAP:
            priority = {"nonperiodic_coordinate_translation": 0, "affine_coordinate_warp": 1, "finite_coordinate_reflection": 2}[family]
            displacement = abs(int(label.rsplit("_", 1)[1])) if family == "nonperiodic_coordinate_translation" else 99
            eligible.append((priority, displacement, -overlap, label, family, alternative, overlap))
    if not eligible:
        raise RuntimeError(f"no structurally distinct physical mismatch for {profile_name}")
    _, _, _, label, family, alternative, overlap = min(eligible, key=lambda item: item[:4])
    return label, family, alternative, overlap


def main() -> None:
    base = load("e014_base_phase", "run.py")
    fingerprint = load("e014_fingerprint_phase", "run_distributional_fingerprint.py")
    physical = load("e014_physical_phase", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    rows = []
    selections = []
    for profile_name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        label, family, alternative_candidate, overlap = select_nonperiodic_mismatch(base, physical, profile_name, profile, profiles)
        mismatch = reference + alternative_candidate
        start = max(np.flatnonzero(np.abs(native - float(np.min(native))) <= 1e-10).tolist())
        initial = np.zeros(len(native), dtype=float)
        initial[start] = 1.0
        selections.append({"profile": profile_name, "alternative": label, "family": family, "centered_overlap": overlap})
        for temperature in TEMPERATURES:
            native_matrix = transition(native, temperature)
            reference_matrix = transition(reference, temperature)
            mismatch_matrix = transition(mismatch, temperature)
            for removal_steps in REMOVAL_DURATIONS:
                removed_state = propagate(initial, reference_matrix, removal_steps)
                intact_at_return = propagate(initial, native_matrix, removal_steps)
                pre_return_dislocation = 1.0 - fingerprint.js_similarity(
                    removed_state, intact_at_return
                )
                for return_steps in RETURN_DURATIONS:
                    total_steps = removal_steps + return_steps
                    intact = propagate(initial, native_matrix, total_steps)
                    removed = propagate(initial, reference_matrix, total_steps)
                    correct = propagate(removed_state, native_matrix, return_steps)
                    mismatched = propagate(removed_state, mismatch_matrix, return_steps)
                    similarities = {
                        "intact": 1.0,
                        "removed": fingerprint.js_similarity(removed, intact),
                        "mismatched_return": fingerprint.js_similarity(mismatched, intact),
                        "correct_return": fingerprint.js_similarity(correct, intact),
                    }
                    margin = similarities["correct_return"] - max(similarities["removed"], similarities["mismatched_return"])
                    rows.append({
                        "profile": profile_name,
                        "basis": profile["basis"],
                        "temperature": temperature,
                        "removal_steps": removal_steps,
                        "return_steps": return_steps,
                        "return_to_removal_ratio": return_steps / removal_steps,
                        "pre_return_dislocation": pre_return_dislocation,
                        "alternative": label,
                        "family": family,
                        "similarities_to_matched_intact": similarities,
                        "return_gain_over_removed": similarities["correct_return"] - similarities["removed"],
                        "specificity_gain_over_mismatch": similarities["correct_return"] - similarities["mismatched_return"],
                        "causal_margin": margin,
                        "causal_pass": margin > 0.0,
                    })

    def aggregate(selected):
        return {
            "configurations": len(selected),
            "pass_fraction": float(np.mean([row["causal_pass"] for row in selected])),
            "minimum_margin": min(row["causal_margin"] for row in selected),
            "median_margin": float(np.median([row["causal_margin"] for row in selected])),
            "mean_correct_similarity": float(np.mean([row["similarities_to_matched_intact"]["correct_return"] for row in selected])),
        }

    by_removal = {str(value): aggregate([row for row in rows if row["removal_steps"] == value]) for value in REMOVAL_DURATIONS}
    by_return = {str(value): aggregate([row for row in rows if row["return_steps"] == value]) for value in RETURN_DURATIONS}
    by_temperature = {str(value): aggregate([row for row in rows if row["temperature"] == value]) for value in TEMPERATURES}
    groups = defaultdict(list)
    for row in rows:
        groups[(row["profile"], row["temperature"], row["removal_steps"])].append(row)
    recovery_windows = []
    for (profile, temperature, removal), items in sorted(groups.items()):
        passing = sorted(row["return_steps"] for row in items if row["causal_pass"])
        recovery_windows.append({
            "profile": profile,
            "temperature": temperature,
            "removal_steps": removal,
            "minimum_passing_return_steps": passing[0] if passing else None,
            "any_return_passes": bool(passing),
            "all_tested_returns_pass": len(passing) == len(RETURN_DURATIONS),
        })
    nonmonotone_groups = []
    for key, items in groups.items():
        ordered = sorted(items, key=lambda row: row["return_steps"])
        similarities = [row["similarities_to_matched_intact"]["correct_return"] for row in ordered]
        if any(right + 1e-12 < left for left, right in zip(similarities, similarities[1:])):
            nonmonotone_groups.append({"profile": key[0], "temperature": key[1], "removal_steps": key[2]})

    summary = {
        "schema": "siel-e014-molecular-reentry-phase-map-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_count": len(profiles),
            "temperatures": list(TEMPERATURES),
            "removal_durations": list(REMOVAL_DURATIONS),
            "return_durations": list(RETURN_DURATIONS),
            "propagation": "exact finite-state transition-matrix propagation",
            "whole_fingerprint": "normalized Jensen-Shannon similarity to matched intact dynamics at equal total time",
            "periodic_mismatches": False,
        },
        "overall": aggregate(rows),
        "by_removal": by_removal,
        "by_return": by_return,
        "by_temperature": by_temperature,
        "recovery_windows": recovery_windows,
        "groups_without_any_passing_return": sum(not item["any_return_passes"] for item in recovery_windows),
        "groups_with_all_returns_passing": sum(item["all_tested_returns_pass"] for item in recovery_windows),
        "nonmonotone_correct_recovery_group_count": len(nonmonotone_groups),
        "nonmonotone_correct_recovery_groups": nonmonotone_groups,
        "selections": selections,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "phase_axes_selected_after_prior dynamic failures": True,
            "reduced_molecular_models_only": True,
        },
    }
    (RESULTS / "molecular_reentry_phase_map_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Molecular O3 re-entry phase-map exploration",
        "",
        f"Configurations: `{summary['overall']['configurations']}`.",
        f"Causal pass fraction: `{summary['overall']['pass_fraction']:.6f}`.",
        f"Profile-temperature-removal groups with no passing return duration: `{summary['groups_without_any_passing_return']}`.",
        f"Groups with every tested return duration passing: `{summary['groups_with_all_returns_passing']}`.",
        f"Groups with nonmonotone correct-recovery similarity: `{summary['nonmonotone_correct_recovery_group_count']}`.",
        "",
        "The phase map treats failed or delayed recovery as a history-dependent re-entry boundary, not as evidence that correct carrier identity is irrelevant.",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "MOLECULAR_REENTRY_PHASE_MAP_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "overall": summary["overall"],
        "by_removal": by_removal,
        "by_return": by_return,
        "by_temperature": by_temperature,
        "groups_without_any_passing_return": summary["groups_without_any_passing_return"],
        "groups_with_all_returns_passing": summary["groups_with_all_returns_passing"],
        "nonmonotone_groups": summary["nonmonotone_correct_recovery_group_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
