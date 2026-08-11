#!/usr/bin/env python3
"""Audit nonperiodic, coordinate-grounded alternatives to correct O3 return."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TEMPERATURES = (0.0005, 0.001, 0.002, 0.004, 0.008)
REMOVAL_STEPS = (10, 20, 40)
TOTAL_STEPS = 100
SEEDS = tuple(range(2026177001, 2026177033))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def nonperiodic_shift(values: np.ndarray, steps: int) -> np.ndarray:
    output = np.empty_like(values)
    if steps > 0:
        output[:steps] = values[0]
        output[steps:] = values[:-steps]
    else:
        count = -steps
        output[-count:] = values[-1]
        output[:-count] = values[count:]
    return output


def coordinate_warp(a_values: np.ndarray, values: np.ndarray, scale: float) -> np.ndarray:
    centre = 0.5 * (float(a_values[0]) + float(a_values[-1]))
    source = centre + scale * (a_values - centre)
    return np.interp(source, a_values, values, left=values[0], right=values[-1])


def alternatives_for(name: str, profile: dict, profiles: dict) -> dict:
    a_values = np.asarray(profile["a_values"], dtype=float)
    candidate = np.asarray(profile["native"], dtype=float) - np.asarray(profile["reference"], dtype=float)
    alternatives = {"coordinate_reflection": (candidate[::-1], "finite_coordinate_reflection")}
    for steps in (-4, -3, -2, -1, 1, 2, 3, 4):
        alternatives[f"nonperiodic_shift_{steps:+d}"] = (nonperiodic_shift(candidate, steps), "nonperiodic_coordinate_translation")
    for scale in (0.70, 0.85, 1.15, 1.30):
        alternatives[f"coordinate_warp_{scale:.2f}"] = (coordinate_warp(a_values, candidate, scale), "affine_coordinate_warp")

    basis = profile["basis"]
    b_value = float(profile["b_angstrom"])
    for other_name, other in profiles.items():
        if other_name == name or other["basis"] != basis:
            continue
        if len(other["a_values"]) != len(a_values) or not np.allclose(other["a_values"], a_values):
            continue
        other_b = float(other["b_angstrom"])
        if abs(other_b - b_value) <= 0.1000001:
            other_candidate = np.asarray(other["native"], dtype=float) - np.asarray(other["reference"], dtype=float)
            alternatives[f"adjacent_b_{other_b:.1f}"] = (other_candidate, "adjacent_transverse_geometry")
    return alternatives


def score(base, rank_module, native, reference, returned, readout, temperature, removal_steps):
    traces = rank_module.return_trajectory(
        base, native, reference, returned, temperature, removal_steps, TOTAL_STEPS, SEEDS,
    )
    value, _ = rank_module.score_late(traces, readout)
    return value


def main() -> None:
    base = load("e014_base_physical_mismatch", "run.py")
    rank_module = load("e014_rank_physical_mismatch", "run_rank_stress_and_nulls.py")
    profiles = base.load_profiles()
    rows = []
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        readout = rank_module.rank_readout(native)
        alternatives = alternatives_for(name, profile, profiles)
        for temperature in TEMPERATURES:
            for removal in REMOVAL_STEPS:
                correct = score(base, rank_module, native, reference, native, readout, temperature, removal)
                for label, (alternative_candidate, family) in alternatives.items():
                    overlap = base.centered_overlap(candidate, alternative_candidate)
                    alternative = score(base, rank_module, native, reference, reference + alternative_candidate, readout, temperature, removal)
                    rows.append({
                        "profile": name,
                        "basis": profile["basis"],
                        "alternative": label,
                        "family": family,
                        "temperature": temperature,
                        "removal_steps": removal,
                        "centered_overlap": overlap,
                        "structurally_distinct": overlap <= base.MAX_OVERLAP,
                        "correct_score": correct,
                        "alternative_score": alternative,
                        "correct_advantage": correct - alternative,
                        "correct_strictly_better": correct > alternative,
                    })

    def aggregate(selected):
        return {
            "comparisons": len(selected),
            "correct_better_fraction": float(np.mean([row["correct_strictly_better"] for row in selected])) if selected else None,
            "positive_advantage_fraction": float(np.mean([row["correct_advantage"] > 0.0 for row in selected])) if selected else None,
            "median_advantage": float(np.median([row["correct_advantage"] for row in selected])) if selected else None,
            "minimum_advantage": min((row["correct_advantage"] for row in selected), default=None),
        }

    families = defaultdict(list)
    for row in rows:
        families[row["family"]].append(row)
    distinct = [row for row in rows if row["structurally_distinct"]]
    summary = {
        "schema": "siel-e014-physical-mismatch-audit-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_count": len(profiles),
            "temperatures": list(TEMPERATURES),
            "removal_steps": list(REMOVAL_STEPS),
            "seeds": list(SEEDS),
            "periodic_wraparound_used": False,
            "structurally_distinct_overlap_maximum": base.MAX_OVERLAP,
        },
        "all_alternatives": aggregate(rows),
        "structurally_distinct_alternatives": aggregate(distinct),
        "by_family": {family: {"all": aggregate(items), "structurally_distinct": aggregate([row for row in items if row["structurally_distinct"]])} for family, items in sorted(families.items())},
        "failures": sorted([
            {key: row[key] for key in ("profile", "alternative", "family", "temperature", "removal_steps", "centered_overlap", "correct_advantage")}
            for row in distinct if not row["correct_strictly_better"]
        ], key=lambda item: item["correct_advantage"]),
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "alternative_families_selected_after_prior_results": True,
            "high_overlap_nearby_alternatives_not_treated_as_structural_mismatches": True,
        },
    }
    (RESULTS / "physical_mismatch_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Physical mismatch audit",
        "",
        "This audit replaces periodic array rolls with nonperiodic coordinate translations, finite-coordinate reflection, affine coordinate warps, and adjacent transverse-geometry carriers.",
        "",
        f"All comparisons: `{summary['all_alternatives']['comparisons']}`; correct-better fraction `{summary['all_alternatives']['correct_better_fraction']:.6f}`.",
        f"Structurally distinct comparisons: `{summary['structurally_distinct_alternatives']['comparisons']}`; correct-better fraction `{summary['structurally_distinct_alternatives']['correct_better_fraction']:.6f}`.",
        f"Structurally distinct failures: `{len(summary['failures'])}`.",
        "",
        "High-overlap nearby alternatives are retained in the record but are not classified as generated structural mismatches.",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "PHYSICAL_MISMATCH_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all": summary["all_alternatives"],
        "structurally_distinct": summary["structurally_distinct_alternatives"],
        "structurally_distinct_failures": len(summary["failures"]),
        "by_family": summary["by_family"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
