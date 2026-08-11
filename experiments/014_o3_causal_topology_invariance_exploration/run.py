#!/usr/bin/env python3
"""Broad local exploration of molecular O3 causal-topology invariance."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
CONDITIONS = ("intact", "removed", "mismatched_return", "correct_return")
MAX_OVERLAP = 0.25
TEMPERATURES = (0.0005, 0.001, 0.002, 0.004, 0.008)
REMOVAL_STEPS = (10, 20, 40)
RADII = (0.15, 0.25, 0.35, 0.45, 0.55)
TOTAL_STEPS = 100
LATE_STEPS = 25
SEEDS = tuple(range(2026170001, 2026170065))


def centered_overlap(left, right) -> float:
    left = np.asarray(left, dtype=float) - float(np.mean(left))
    right = np.asarray(right, dtype=float) - float(np.mean(right))
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator <= 0.0:
        raise ValueError("centered candidate has zero norm")
    return float(np.vdot(left, right).real / denominator)


def select_mismatch(candidate: np.ndarray) -> tuple[int, np.ndarray, float]:
    for shift in range(1, len(candidate) // 2 + 1):
        shifted = np.roll(candidate, shift)
        overlap = centered_overlap(candidate, shifted)
        if overlap <= MAX_OVERLAP:
            return shift, shifted, overlap
    raise ValueError("no overlap-admissible cyclic mismatch")


def load_profiles() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    full = defaultdict(dict)
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["mode"] != "full":
                continue
            basis = row["basis"]
            a = round(float(row["a_angstrom"]), 1)
            b = round(float(row["b_angstrom"]), 1)
            full[(basis, b)][a] = float(row["energy_hartree"])
    profiles = {}
    for (basis, b), values in sorted(full.items()):
        a_values = sorted(values)
        profiles[f"{basis}_b{b:.1f}"] = {
            "source": "E010 complete FCI surface line",
            "basis": basis,
            "b_angstrom": b,
            "a_values": a_values,
            "native": [values[a] for a in a_values],
            "reference": [0.0 for _ in a_values],
        }

    checkpoint = json.loads((REPO_ROOT / "experiments/013_domain_prior_o3_generation_transfer/results/molecular_energy_checkpoint.json").read_text())
    keys = sorted(checkpoint, key=lambda item: float(item.split(",")[0]))
    profiles["cc-pvtz_b1.0"] = {
        "source": "E013 fresh full-minus-isolated FCI line",
        "basis": "cc-pvtz",
        "b_angstrom": 1.0,
        "a_values": [float(item.split(",")[0]) for item in keys],
        "native": [checkpoint[item]["full"] for item in keys],
        "reference": [checkpoint[item]["isolated"] for item in keys],
    }
    return profiles


def metropolis(surface: np.ndarray, index: int, rng, temperature: float) -> int:
    neighbors = [item for item in (index - 1, index + 1) if 0 <= item < len(surface)]
    proposed = neighbors[int(rng.integers(len(neighbors)))]
    delta = float(surface[proposed] - surface[index])
    if delta <= 0.0 or rng.random() < math.exp(-delta / temperature):
        return proposed
    return index


def trajectories(
    native: np.ndarray,
    reference: np.ndarray,
    mismatch: np.ndarray,
    temperature: float,
    removal_steps: int,
    seeds=SEEDS,
    total_steps: int = TOTAL_STEPS,
) -> dict:
    minimum = float(np.min(native))
    minima = np.flatnonzero(np.abs(native - minimum) <= 1e-10).tolist()
    start = max(minima)
    reconstructed = reference + (native - reference)
    output = {}
    for condition in CONDITIONS:
        late_indices = []
        for seed in seeds:
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
                    surface = reconstructed
                else:
                    surface = mismatch
                index = metropolis(surface, index, rng, temperature)
                trace.append(index)
            late_indices.append(trace[-min(LATE_STEPS, total_steps):])
        output[condition] = late_indices
    return {"late_indices": output, "minima": minima}


def scores_for_radius(simulation: dict, a_values: list[float], radius: float) -> tuple[dict, dict]:
    minima = simulation["minima"]
    seed_scores = {}
    for condition, seed_traces in simulation["late_indices"].items():
        seed_scores[condition] = [
            float(np.mean([
                min(abs(a_values[index] - a_values[target]) for target in minima) <= radius
                for index in trace
            ]))
            for trace in seed_traces
        ]
    scores = {condition: float(np.mean(values)) for condition, values in seed_scores.items()}
    return scores, seed_scores


def causal_metrics(scores: dict) -> dict:
    edges = {
        "intact_gt_removed": scores["intact"] > scores["removed"],
        "intact_gt_mismatch": scores["intact"] > scores["mismatched_return"],
        "correct_gt_removed": scores["correct_return"] > scores["removed"],
        "correct_gt_mismatch": scores["correct_return"] > scores["mismatched_return"],
    }
    margin = min(scores["intact"], scores["correct_return"]) - max(
        scores["removed"], scores["mismatched_return"]
    )
    return {"edges": edges, "pass": all(edges.values()), "causal_margin": margin}


def paired_seed_support(seed_scores: dict) -> dict:
    comparisons = {
        "intact_gt_removed": ("intact", "removed"),
        "intact_gt_mismatch": ("intact", "mismatched_return"),
        "correct_gt_removed": ("correct_return", "removed"),
        "correct_gt_mismatch": ("correct_return", "mismatched_return"),
    }
    return {
        name: {
            "positive_fraction": float(np.mean(np.asarray(seed_scores[left]) > np.asarray(seed_scores[right]))),
            "mean_paired_difference": float(np.mean(np.asarray(seed_scores[left]) - np.asarray(seed_scores[right]))),
        }
        for name, (left, right) in comparisons.items()
    }


def parameter_sweep(profiles: dict) -> list[dict]:
    rows = []
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        shift, shifted_candidate, overlap = select_mismatch(candidate)
        mismatch = reference + shifted_candidate
        for temperature in TEMPERATURES:
            for removal_steps in REMOVAL_STEPS:
                simulation = trajectories(native, reference, mismatch, temperature, removal_steps)
                for radius in RADII:
                    scores, seed_scores = scores_for_radius(simulation, profile["a_values"], radius)
                    metrics = causal_metrics(scores)
                    rows.append({
                        "profile": name,
                        "basis": profile["basis"],
                        "b_angstrom": profile["b_angstrom"],
                        "source": profile["source"],
                        "temperature": temperature,
                        "removal_steps": removal_steps,
                        "radius": radius,
                        "mismatch_shift_steps": shift,
                        "mismatch_overlap": overlap,
                        "scores": scores,
                        "causal": metrics,
                        "paired_seed_support": paired_seed_support(seed_scores),
                    })
    return rows


def competitor_audit(profiles: dict) -> dict:
    output = {}
    competitor_seeds = tuple(range(2026171001, 2026171065))
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        competitors = {}
        for shift in range(1, len(candidate)):
            competitors[f"cyclic_shift_{shift}"] = reference + np.roll(candidate, shift)
        competitors["reversal"] = reference + candidate[::-1]
        for amplitude in (0.25, 0.50, 0.75, 1.25, 1.50):
            competitors[f"amplitude_{amplitude:.2f}"] = reference + amplitude * candidate
        rng = np.random.default_rng(2026171999)
        for index in range(32):
            competitors[f"permutation_{index + 1:02d}"] = reference + rng.permutation(candidate)

        correct_sim = trajectories(native, reference, native, 0.002, 20, competitor_seeds)
        correct_scores, _ = scores_for_radius(correct_sim, profile["a_values"], 0.35)
        correct = correct_scores["correct_return"]
        records = {}
        for label, surface in competitors.items():
            sim = trajectories(native, reference, surface, 0.002, 20, competitor_seeds)
            score, _ = scores_for_radius(sim, profile["a_values"], 0.35)
            value = score["mismatched_return"]
            records[label] = {"return_score": value, "correct_advantage": correct - value, "correct_strictly_better": correct > value}
        output[name] = {
            "correct_return_score": correct,
            "competitor_count": len(records),
            "correct_better_fraction": float(np.mean([item["correct_strictly_better"] for item in records.values()])),
            "minimum_correct_advantage": min(item["correct_advantage"] for item in records.values()),
            "competitors": records,
        }
    return output


def summarize(rows: list[dict], competitors: dict) -> dict:
    by_profile = {}
    for profile in sorted({row["profile"] for row in rows}):
        selected = [row for row in rows if row["profile"] == profile]
        margins = [row["causal"]["causal_margin"] for row in selected]
        by_profile[profile] = {
            "configurations": len(selected),
            "causal_pass_count": sum(row["causal"]["pass"] for row in selected),
            "causal_pass_fraction": float(np.mean([row["causal"]["pass"] for row in selected])),
            "minimum_margin": min(margins),
            "median_margin": float(np.median(margins)),
            "maximum_margin": max(margins),
            "competitor_correct_better_fraction": competitors[profile]["correct_better_fraction"],
            "competitor_minimum_correct_advantage": competitors[profile]["minimum_correct_advantage"],
        }
    return {
        "configuration_count": len(rows),
        "profile_count": len(by_profile),
        "overall_causal_pass_fraction": float(np.mean([row["causal"]["pass"] for row in rows])),
        "positive_margin_fraction": float(np.mean([row["causal"]["causal_margin"] > 0.0 for row in rows])),
        "all_profiles_majority_causal": all(item["causal_pass_fraction"] > 0.5 for item in by_profile.values()),
        "all_profiles_positive_median_margin": all(item["median_margin"] > 0.0 for item in by_profile.values()),
        "profiles": by_profile,
    }


def write_csv(rows: list[dict]) -> None:
    with (RESULTS / "molecular_parameter_sweep.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("profile", "basis", "b_angstrom", "temperature", "removal_steps", "radius", "intact", "removed", "mismatched_return", "correct_return", "causal_margin", "causal_pass", "mismatch_overlap"))
        for row in rows:
            scores = row["scores"]
            writer.writerow((row["profile"], row["basis"], row["b_angstrom"], row["temperature"], row["removal_steps"], row["radius"], scores["intact"], scores["removed"], scores["mismatched_return"], scores["correct_return"], row["causal"]["causal_margin"], row["causal"]["pass"], row["mismatch_overlap"]))


def main() -> None:
    profiles = load_profiles()
    rows = parameter_sweep(profiles)
    competitors = competitor_audit(profiles)
    summary = {
        "schema": "siel-e014-local-topology-invariance-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "parameter_grid": {"temperatures": TEMPERATURES, "removal_steps": REMOVAL_STEPS, "radii": RADII, "seed_range": [SEEDS[0], SEEDS[-1]], "seeds": len(SEEDS)},
        "summary": summarize(rows, competitors),
        "competitor_audit": competitors,
        "rows": rows,
        "scope": {"not_confirmatory": True, "does_not_change_e013": True, "public_experiment_not_ready_from_this_result_alone": True},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(rows)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    overview = summary["summary"]
    lines = [
        "# E014 molecular topology-invariance exploration",
        "",
        f"Profiles: `{overview['profile_count']}`.",
        f"Parameter configurations: `{overview['configuration_count']}`.",
        f"Overall four-edge causal pass fraction: `{overview['overall_causal_pass_fraction']:.6f}`.",
        f"Positive causal-margin fraction: `{overview['positive_margin_fraction']:.6f}`.",
        f"All profiles have positive median margin: `{overview['all_profiles_positive_median_margin']}`.",
        "",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({key: overview[key] for key in ("profile_count", "configuration_count", "overall_causal_pass_fraction", "positive_margin_fraction", "all_profiles_positive_median_margin")}, sort_keys=True))


if __name__ == "__main__":
    main()
