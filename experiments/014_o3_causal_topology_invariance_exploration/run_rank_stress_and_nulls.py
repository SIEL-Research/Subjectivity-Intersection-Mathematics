#!/usr/bin/env python3
"""Stress-test the native-energy-rank readout and its noncircularity controls."""

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
STRESS_TEMPERATURES = (0.0001, 0.00025, 0.0005, 0.001, 0.002, 0.004, 0.008, 0.016)
STRESS_TOTAL_STEPS = (40, 100, 200)
REMOVAL_FRACTIONS = (0.10, 0.20, 0.40)
STRESS_SEEDS = tuple(range(2026173001, 2026173033))
COMPETITOR_SEEDS = tuple(range(2026174001, 2026174065))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rank_readout(native: np.ndarray) -> np.ndarray:
    order = np.argsort(np.argsort(native, kind="stable"), kind="stable")
    return 1.0 - order / max(len(native) - 1, 1)


def score_late(late_indices: list[list[int]], readout: np.ndarray) -> tuple[float, list[float]]:
    seed_scores = [float(np.mean(readout[np.asarray(trace, dtype=int)])) for trace in late_indices]
    return float(np.mean(seed_scores)), seed_scores


def return_trajectory(base, native, reference, returned, temperature, removal_steps, total_steps, seeds):
    minimum = float(np.min(native))
    minima = np.flatnonzero(np.abs(native - minimum) <= 1e-10).tolist()
    start = max(minima)
    output = []
    for seed in seeds:
        rng = np.random.default_rng(int(seed))
        index = start
        trace = []
        for step in range(total_steps):
            surface = reference if step < removal_steps else returned
            index = base.metropolis(surface, index, rng, temperature)
            trace.append(index)
        output.append(trace[-min(base.LATE_STEPS, total_steps):])
    return output


def stress_sweep(base, profiles: dict) -> tuple[list[dict], dict]:
    rows = []
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        shift, shifted, overlap = base.select_mismatch(candidate)
        mismatch = reference + shifted
        readout = rank_readout(native)
        for temperature in STRESS_TEMPERATURES:
            for total_steps in STRESS_TOTAL_STEPS:
                for removal_fraction in REMOVAL_FRACTIONS:
                    removal_steps = max(1, int(round(total_steps * removal_fraction)))
                    simulation = base.trajectories(
                        native,
                        reference,
                        mismatch,
                        temperature,
                        removal_steps,
                        seeds=STRESS_SEEDS,
                        total_steps=total_steps,
                    )
                    scores = {}
                    seed_scores = {}
                    for condition, traces in simulation["late_indices"].items():
                        scores[condition], seed_scores[condition] = score_late(traces, readout)
                    rows.append({
                        "profile": name,
                        "basis": profile["basis"],
                        "temperature": temperature,
                        "total_steps": total_steps,
                        "removal_fraction": removal_fraction,
                        "removal_steps": removal_steps,
                        "mismatch_overlap": overlap,
                        "scores": scores,
                        "causal": base.causal_metrics(scores),
                        "paired_seed_support": base.paired_seed_support(seed_scores),
                    })
    by_axis = {}
    for axis in ("basis", "temperature", "total_steps", "removal_fraction"):
        groups = defaultdict(list)
        for row in rows:
            groups[str(row[axis])].append(row["causal"]["pass"])
        by_axis[axis] = {key: float(np.mean(values)) for key, values in sorted(groups.items())}
    profile_groups = defaultdict(list)
    for row in rows:
        profile_groups[row["profile"]].append(row)
    profile_summary = {
        name: {
            "pass_fraction": float(np.mean([row["causal"]["pass"] for row in values])),
            "minimum_margin": min(row["causal"]["causal_margin"] for row in values),
            "median_margin": float(np.median([row["causal"]["causal_margin"] for row in values])),
        }
        for name, values in profile_groups.items()
    }
    summary = {
        "configurations": len(rows),
        "overall_pass_fraction": float(np.mean([row["causal"]["pass"] for row in rows])),
        "minimum_margin": min(row["causal"]["causal_margin"] for row in rows),
        "median_margin": float(np.median([row["causal"]["causal_margin"] for row in rows])),
        "all_profiles_all_configs_pass": all(item["pass_fraction"] == 1.0 for item in profile_summary.values()),
        "by_axis": by_axis,
        "profiles": profile_summary,
    }
    return rows, summary


def admissible_competitor_audit(base, profiles: dict) -> dict:
    output = {}
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        readout = rank_readout(native)
        competitors = {}
        for shift in range(1, len(candidate)):
            shifted = np.roll(candidate, shift)
            overlap = base.centered_overlap(candidate, shifted)
            if overlap <= base.MAX_OVERLAP:
                competitors[f"cyclic_{shift}"] = (reference + shifted, overlap, "cyclic_isometry")
        reversed_candidate = candidate[::-1]
        reverse_overlap = base.centered_overlap(candidate, reversed_candidate)
        if reverse_overlap <= base.MAX_OVERLAP:
            competitors["reversal"] = (reference + reversed_candidate, reverse_overlap, "reversal_isometry")
        rng = np.random.default_rng(2026174999)
        accepted = 0
        attempts = 0
        while accepted < 64 and attempts < 4096:
            attempts += 1
            permuted = rng.permutation(candidate)
            overlap = base.centered_overlap(candidate, permuted)
            if overlap <= base.MAX_OVERLAP:
                accepted += 1
                competitors[f"permutation_{accepted:02d}"] = (reference + permuted, overlap, "permutation_isometry")

        correct_trace = return_trajectory(base, native, reference, native, 0.002, 20, 100, COMPETITOR_SEEDS)
        correct_score, _ = score_late(correct_trace, readout)
        records = {}
        for label, (surface, overlap, family) in competitors.items():
            trace = return_trajectory(base, native, reference, surface, 0.002, 20, 100, COMPETITOR_SEEDS)
            score, _ = score_late(trace, readout)
            records[label] = {"family": family, "centered_overlap": overlap, "score": score, "correct_advantage": correct_score - score, "correct_strictly_better": correct_score > score}
        output[name] = {
            "correct_score": correct_score,
            "admissible_competitor_count": len(records),
            "correct_better_fraction": float(np.mean([item["correct_strictly_better"] for item in records.values()])),
            "minimum_correct_advantage": min(item["correct_advantage"] for item in records.values()),
            "records": records,
        }
    return output


def randomized_readout_null(base, profiles: dict) -> dict:
    output = {}
    for profile_index, (name, profile) in enumerate(profiles.items()):
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        _, shifted, _ = base.select_mismatch(candidate)
        mismatch = reference + shifted
        correct_trace = return_trajectory(base, native, reference, native, 0.002, 20, 100, COMPETITOR_SEEDS)
        mismatch_trace = return_trajectory(base, native, reference, mismatch, 0.002, 20, 100, COMPETITOR_SEEDS)
        native_rank = rank_readout(native)
        correct_native, _ = score_late(correct_trace, native_rank)
        mismatch_native, _ = score_late(mismatch_trace, native_rank)
        observed = correct_native - mismatch_native
        rng = np.random.default_rng(2026175000 + profile_index)
        null_advantages = []
        for _ in range(512):
            sham = rng.permutation(native_rank)
            correct_sham, _ = score_late(correct_trace, sham)
            mismatch_sham, _ = score_late(mismatch_trace, sham)
            null_advantages.append(correct_sham - mismatch_sham)
        output[name] = {
            "native_rank_advantage": observed,
            "null_mean": float(np.mean(null_advantages)),
            "null_standard_deviation": float(np.std(null_advantages, ddof=1)),
            "null_fraction_at_least_observed": float(np.mean(np.asarray(null_advantages) >= observed - 1e-15)),
            "native_advantage_positive": observed > 0.0,
        }
    return output


def affine_covariance(profiles: dict) -> dict:
    output = {}
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference_rank = rank_readout(native)
        maximum = 0.0
        for scale in (0.01, 0.1, 1.0, 10.0, 100.0):
            for offset in (-1000.0, -1.0, 0.0, 1.0, 1000.0):
                transformed = rank_readout(scale * native + offset)
                maximum = max(maximum, float(np.max(np.abs(reference_rank - transformed))))
        output[name] = {"maximum_rank_readout_difference": maximum, "pass": maximum <= 1e-12}
    return output


def main() -> None:
    base = load("e014_base_stress", "run.py")
    profiles = base.load_profiles()
    rows, stress = stress_sweep(base, profiles)
    competitors = admissible_competitor_audit(base, profiles)
    readout_null = randomized_readout_null(base, profiles)
    covariance = affine_covariance(profiles)
    summary = {
        "schema": "siel-e014-energy-rank-stress-null-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "stress": stress,
        "admissible_competitors": {
            "all_profiles_correct_better_than_every_competitor": all(item["correct_better_fraction"] == 1.0 for item in competitors.values()),
            "mean_correct_better_fraction": float(np.mean([item["correct_better_fraction"] for item in competitors.values()])),
            "profiles": competitors,
        },
        "randomized_readout_null": {
            "all_native_advantages_positive": all(item["native_advantage_positive"] for item in readout_null.values()),
            "maximum_null_fraction_at_least_observed": max(item["null_fraction_at_least_observed"] for item in readout_null.values()),
            "profiles": readout_null,
        },
        "affine_representation_covariance": {
            "all_profiles_pass": all(item["pass"] for item in covariance.values()),
            "profiles": covariance,
        },
        "rows": rows,
        "scope": {"not_confirmatory": True, "energy_rank_selected_after_method_comparison": True},
    }
    (RESULTS / "rank_stress_null_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Energy-rank stress and null exploration",
        "",
        f"Stress configurations: `{stress['configurations']}`.",
        f"Causal pass fraction: `{stress['overall_pass_fraction']:.6f}`.",
        f"Minimum causal margin: `{stress['minimum_margin']:.9f}`.",
        f"All profiles/all stress configurations pass: `{stress['all_profiles_all_configs_pass']}`.",
        f"Correct return beats every admissible competitor in every profile: `{summary['admissible_competitors']['all_profiles_correct_better_than_every_competitor']}`.",
        f"Mean admissible-competitor specificity fraction: `{summary['admissible_competitors']['mean_correct_better_fraction']:.6f}`.",
        f"All native-rank advantages positive against randomized-readout nulls: `{summary['randomized_readout_null']['all_native_advantages_positive']}`.",
        f"Maximum null tail fraction: `{summary['randomized_readout_null']['maximum_null_fraction_at_least_observed']:.6f}`.",
        f"Positive-affine representation covariance: `{summary['affine_representation_covariance']['all_profiles_pass']}`.",
        "",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "RANK_STRESS_NULL_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "stress_pass_fraction": stress["overall_pass_fraction"],
        "minimum_margin": stress["minimum_margin"],
        "all_stress_pass": stress["all_profiles_all_configs_pass"],
        "all_competitors_rejected": summary["admissible_competitors"]["all_profiles_correct_better_than_every_competitor"],
        "mean_competitor_specificity": summary["admissible_competitors"]["mean_correct_better_fraction"],
        "all_native_null_advantages_positive": summary["randomized_readout_null"]["all_native_advantages_positive"],
        "maximum_null_tail": summary["randomized_readout_null"]["maximum_null_fraction_at_least_observed"],
        "affine_covariance": summary["affine_representation_covariance"]["all_profiles_pass"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
