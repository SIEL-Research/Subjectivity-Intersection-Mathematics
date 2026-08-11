#!/usr/bin/env python3
"""Exploratory cc-pVTZ line-landscape trajectory with generated residual removal."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
CHECKPOINT = RESULTS / "cc_pvtz_line_energies.json"
SPARSE_CHECKPOINT = RESULTS / "sparse_energies.json"
MODES = ("full", "without_edge_01")
CONDITIONS = ("intact", "removed", "mismatched_return", "correct_return")
LINE_POINTS = tuple((round(a, 1), 0.9) for a in np.arange(1.3, 2.5 + 0.05, 0.1))


def load_e010():
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/run.py"
    spec = importlib.util.spec_from_file_location("e010_for_e013_line", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load E010")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def initialize_checkpoint() -> dict:
    records = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {}
    if SPARSE_CHECKPOINT.exists():
        sparse = json.loads(SPARSE_CHECKPOINT.read_text()).get("cc-pvtz", {})
        for point, values in sparse.items():
            a, b = (float(item) for item in point.split(","))
            if (round(a, 1), round(b, 1)) in LINE_POINTS:
                records.setdefault(point, {}).update(values)
    return records


def save(records: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")


def compute_line() -> dict:
    e010 = load_e010()
    records = initialize_checkpoint()
    for a, b in LINE_POINTS:
        key = f"{a:.1f},{b:.1f}"
        record = records.setdefault(key, {})
        missing = [mode for mode in MODES if mode not in record]
        if not missing:
            continue
        built = e010.build_target("cc-pvtz", a, b)
        record["n_orbitals"] = int(built["h_full"].shape[0])
        for mode in missing:
            record[mode] = e010.fci_solution(built, mode)[0]
            save(records)
    return records


def load_cc_pvdz_line() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    records = {mode: {} for mode in MODES}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            point = (round(float(row["a_angstrom"]), 1), round(float(row["b_angstrom"]), 1))
            if row["basis"] == "cc-pvdz" and row["mode"] in MODES and point in LINE_POINTS:
                records[row["mode"]][point] = float(row["energy_hartree"])
    return records


def as_surfaces(records: dict) -> dict:
    return {
        mode: {
            tuple(float(value) for value in key.split(",")): float(record[mode])
            for key, record in records.items()
        }
        for mode in MODES
    }


def trajectory_scores(
    surfaces: dict,
    seeds: tuple[int, ...],
    radius: float = 0.35,
    total_steps: int = 100,
    removal_steps: int = 20,
) -> dict:
    full, mismatch = surfaces["full"], surfaces["without_edge_01"]
    reference = {point: 0.0 for point in full}
    minimum = min(full.values())
    minima = [point for point, energy in full.items() if abs(energy - minimum) <= 1e-10]
    start = minima[0]

    def step(surface, point, rng):
        candidates = [
            candidate for candidate in ((round(point[0] - 0.1, 1), 0.9), (round(point[0] + 0.1, 1), 0.9))
            if candidate in surface
        ]
        proposed = candidates[int(rng.integers(len(candidates)))]
        delta = surface[proposed] - surface[point]
        if delta <= 0.0 or rng.random() < math.exp(-delta / 0.002):
            return proposed
        return point

    output = {}
    for condition in CONDITIONS:
        seed_scores = []
        for seed in seeds:
            rng, point, trajectory = np.random.default_rng(seed), start, []
            for index in range(total_steps):
                if condition == "intact":
                    surface = full
                elif condition == "removed":
                    surface = reference
                elif index < removal_steps:
                    surface = reference
                elif condition == "correct_return":
                    surface = full
                else:
                    surface = mismatch
                point = step(surface, point, rng)
                trajectory.append(point)
            late = trajectory[-25:]
            seed_scores.append(float(np.mean([min(abs(p[0] - m[0]) for m in minima) <= radius for p in late])))
        output[condition] = {"whole_score": float(np.mean(seed_scores)), "seed_scores": seed_scores}
    scores = {condition: output[condition]["whole_score"] for condition in CONDITIONS}
    output["gates"] = {
        "intact_high": scores["intact"] >= 0.80,
        "removed_low": scores["removed"] <= 0.50,
        "mismatched_low": scores["mismatched_return"] <= 0.50,
        "correct_high": scores["correct_return"] >= 0.80,
        "specific_return": scores["correct_return"] >= max(scores["removed"], scores["mismatched_return"]) + 0.25,
    }
    output["pass"] = all(output["gates"].values())
    output["full_minima"] = [list(point) for point in minima]
    output["mismatch_minimum"] = list(min(mismatch, key=mismatch.get))
    return output


def main() -> None:
    records = compute_line()
    cc_pvtz = as_surfaces(records)
    cc_pvdz = load_cc_pvdz_line()
    seeds = tuple(range(2026130001, 2026130033))
    robustness_seeds = tuple(range(2026131001, 2026131513))
    profiles = {
        "cc-pvdz_line_control": cc_pvdz,
        "cc-pvtz_line_target": cc_pvtz,
    }
    summary = {
        "schema": "siel-e013-high-basis-line-local-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "line": {"b_angstrom": 0.9, "a_minimum": 1.3, "a_maximum": 2.5, "step": 0.1},
        "trajectory_seeds": [seeds[0], seeds[-1]],
        "bases": {name: trajectory_scores(surface, seeds) for name, surface in profiles.items()},
        "robustness": {
            "seed_count": len(robustness_seeds),
            "radius_sweep": {
                f"{radius:.2f}": {
                    name: trajectory_scores(surface, robustness_seeds, radius=radius)
                    for name, surface in profiles.items()
                }
                for radius in (0.25, 0.35, 0.45)
            },
        },
        "scope": {
            "not_confirmatory": True,
            "one_dimensional_line_not_full_e010_surface": True,
            "does_not_change_public_e012": True,
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "high_basis_line_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# High-basis line-trajectory exploration",
        "",
        "| Profile | Intact | Removed | Mismatched | Correct | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, record in summary["bases"].items():
        lines.append(
            f"| {name} | {record['intact']['whole_score']:.6f} | {record['removed']['whole_score']:.6f} | "
            f"{record['mismatched_return']['whole_score']:.6f} | {record['correct_return']['whole_score']:.6f} | {record['pass']} |"
        )
    lines.extend(["", "This is a one-dimensional result-informed exploration, not a full-surface confirmation."])
    lines.extend(["", "## 512-seed radius sensitivity", "", "| Radius | Profile | Removed | Mismatched | Pass |", "|---:|---|---:|---:|---:|"])
    for radius, profiles_at_radius in summary["robustness"]["radius_sweep"].items():
        for name, record in profiles_at_radius.items():
            lines.append(
                f"| {radius} | {name} | {record['removed']['whole_score']:.6f} | "
                f"{record['mismatched_return']['whole_score']:.6f} | {record['pass']} |"
            )
    (RESULTS / "HIGH_BASIS_LINE_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({name: record["pass"] for name, record in summary["bases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
