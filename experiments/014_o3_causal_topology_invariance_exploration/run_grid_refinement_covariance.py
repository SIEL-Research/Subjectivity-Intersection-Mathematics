#!/usr/bin/env python3
"""Grid-refinement covariance of the distributional O3 causal topology."""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TEMPERATURES = (0.001, 0.002, 0.004)
FACTORS = (1, 2, 4)
BASE_TOTAL_STEPS = 100
BASE_REMOVAL_STEPS = 20
BASE_LATE_STEPS = 25
SEEDS = tuple(range(2026181001, 2026181033))
DISCRIMINABILITY_FLOOR = 1.0 / (64 * 25)


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def refine(values: np.ndarray, factor: int) -> np.ndarray:
    old = np.linspace(0.0, 1.0, len(values))
    new = np.linspace(0.0, 1.0, (len(values) - 1) * factor + 1)
    return np.interp(new, old, values)


def transformed_candidate(label: str, coordinates: np.ndarray, candidate: np.ndarray, factor: int, adjacent: np.ndarray | None) -> np.ndarray:
    if label == "coordinate_reflection":
        return candidate[::-1]
    if label.startswith("nonperiodic_shift_"):
        original_steps = int(re.search(r"([+-]\d+)$", label).group(1))
        physical_steps = original_steps * factor
        output = np.empty_like(candidate)
        if physical_steps > 0:
            output[:physical_steps] = candidate[0]
            output[physical_steps:] = candidate[:-physical_steps]
        else:
            count = -physical_steps
            output[-count:] = candidate[-1]
            output[:-count] = candidate[count:]
        return output
    if label.startswith("coordinate_warp_"):
        scale = float(label.rsplit("_", 1)[1])
        centre = 0.5 * (float(coordinates[0]) + float(coordinates[-1]))
        source = centre + scale * (coordinates - centre)
        return np.interp(source, coordinates, candidate, left=candidate[0], right=candidate[-1])
    if label.startswith("adjacent_b_") and adjacent is not None:
        return adjacent
    raise ValueError(f"unsupported alternative {label}")


def simulate(base, native, reference, mismatch, temperature, factor):
    total_steps = BASE_TOTAL_STEPS * factor * factor
    removal_steps = BASE_REMOVAL_STEPS * factor * factor
    late_steps = BASE_LATE_STEPS * factor * factor
    minimum = float(np.min(native))
    start = max(np.flatnonzero(np.abs(native - minimum) <= 1e-10).tolist())
    output = {}
    for condition in ("intact", "removed", "mismatched_return", "correct_return"):
        late = []
        for seed in SEEDS:
            rng = np.random.default_rng(int(seed))
            index = start
            trace = []
            for step in range(total_steps):
                if condition == "intact":
                    surface = native
                elif condition == "removed":
                    surface = reference
                elif step < removal_steps:
                    surface = reference
                elif condition == "correct_return":
                    surface = native
                else:
                    surface = mismatch
                index = base.metropolis(surface, index, rng, temperature)
                trace.append(index)
            late.append(trace[-late_steps:])
        output[condition] = late
    return output


def distribution(traces, size, pseudocount):
    counts = np.full(size, pseudocount, dtype=float)
    for trace in traces:
        counts += np.bincount(np.asarray(trace, dtype=int), minlength=size)
    return counts / float(np.sum(counts))


def main() -> None:
    base = load("e014_base_grid", "run.py")
    fingerprint = load("e014_fingerprint_grid", "run_distributional_fingerprint.py")
    physical = load("e014_physical_grid", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    rows = []
    selections = []
    for profile_name, profile in profiles.items():
        original_native = np.asarray(profile["native"], dtype=float)
        original_reference = np.asarray(profile["reference"], dtype=float)
        original_candidate = original_native - original_reference
        original_coordinates = np.asarray(profile["a_values"], dtype=float)
        raw_alternatives = physical.alternatives_for(profile_name, profile, profiles)
        for temperature in TEMPERATURES:
            native_target = fingerprint.stationary_distribution(original_native, temperature)
            eligible = []
            for label, (alternative_candidate, family) in raw_alternatives.items():
                overlap = base.centered_overlap(original_candidate, alternative_candidate)
                if overlap > base.MAX_OVERLAP:
                    continue
                alternative_target = fingerprint.stationary_distribution(original_reference + alternative_candidate, temperature)
                separation = 1.0 - fingerprint.js_similarity(alternative_target, native_target)
                if separation >= DISCRIMINABILITY_FLOOR:
                    eligible.append((separation, label, family, alternative_candidate))
            if not eligible:
                raise RuntimeError(f"no eligible alternative for {profile_name} at {temperature}")
            separation, label, family, original_alternative = min(eligible, key=lambda item: (item[0], item[1]))
            selections.append({"profile": profile_name, "temperature": temperature, "alternative": label, "family": family, "target_js_separation": separation})

            adjacent_original = original_alternative if label.startswith("adjacent_b_") else None
            for factor in FACTORS:
                coordinates = np.linspace(original_coordinates[0], original_coordinates[-1], (len(original_coordinates) - 1) * factor + 1)
                native = refine(original_native, factor)
                reference = refine(original_reference, factor)
                candidate = native - reference
                adjacent = refine(adjacent_original, factor) if adjacent_original is not None else None
                alternative_candidate = transformed_candidate(label, coordinates, candidate, factor, adjacent)
                mismatch = reference + alternative_candidate
                traces = simulate(base, native, reference, mismatch, temperature, factor)
                target = fingerprint.stationary_distribution(native, temperature)
                pseudocount = 0.5 * len(original_native) / len(native)
                scores = {
                    condition: fingerprint.js_similarity(distribution(condition_traces, len(native), pseudocount), target)
                    for condition, condition_traces in traces.items()
                }
                causal = base.causal_metrics(scores)
                rows.append({
                    "profile": profile_name,
                    "basis": profile["basis"],
                    "temperature": temperature,
                    "factor": factor,
                    "grid_points": len(native),
                    "alternative": label,
                    "family": family,
                    "selection_target_js_separation": separation,
                    "scores": scores,
                    "causal": causal,
                })

    by_factor = {}
    for factor in FACTORS:
        selected = [row for row in rows if row["factor"] == factor]
        by_factor[str(factor)] = {
            "configurations": len(selected),
            "pass_fraction": float(np.mean([row["causal"]["pass"] for row in selected])),
            "minimum_margin": min(row["causal"]["causal_margin"] for row in selected),
            "median_margin": float(np.median([row["causal"]["causal_margin"] for row in selected])),
        }
    groups = {}
    for row in rows:
        key = (row["profile"], row["temperature"])
        groups.setdefault(key, []).append(row)
    covariance = {
        f"{profile}|{temperature}": {
            "all_factors_pass": all(row["causal"]["pass"] for row in items),
            "margin_range": max(row["causal"]["causal_margin"] for row in items) - min(row["causal"]["causal_margin"] for row in items),
        }
        for (profile, temperature), items in groups.items()
    }
    summary = {
        "schema": "siel-e014-grid-refinement-covariance-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_count": len(profiles),
            "temperatures": list(TEMPERATURES),
            "grid_refinement_factors": list(FACTORS),
            "diffusive_time_scaling": "all step windows multiplied by factor squared",
            "alternative_selection": "lowest exact target JS separation above the exploratory discriminability floor among structurally distinct physical alternatives",
            "discriminability_floor": DISCRIMINABILITY_FLOOR,
        },
        "by_factor": by_factor,
        "all_profile_temperature_groups_all_factors_pass": all(item["all_factors_pass"] for item in covariance.values()),
        "maximum_margin_range_across_factors": max(item["margin_range"] for item in covariance.values()),
        "covariance": covariance,
        "selections": selections,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "discriminability_floor_selected_after_exploration": True,
            "linear_interpolation_is_a_numerical_representation_control_not_new_quantum_chemistry": True,
        },
    }
    (RESULTS / "grid_refinement_covariance_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Grid-refinement covariance exploration",
        "",
        f"All profile-temperature groups pass at every factor: `{summary['all_profile_temperature_groups_all_factors_pass']}`.",
        f"Maximum within-group causal-margin range: `{summary['maximum_margin_range_across_factors']:.9f}`.",
        "",
    ]
    for factor, item in by_factor.items():
        lines.append(f"- factor {factor}: pass fraction `{item['pass_fraction']:.6f}`, minimum margin `{item['minimum_margin']:.9f}`.")
    lines += ["", "This is result-informed local exploration, not confirmatory evidence."]
    (RESULTS / "GRID_REFINEMENT_COVARIANCE_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "by_factor": by_factor,
        "all_groups_all_factors_pass": summary["all_profile_temperature_groups_all_factors_pass"],
        "maximum_margin_range": summary["maximum_margin_range_across_factors"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
