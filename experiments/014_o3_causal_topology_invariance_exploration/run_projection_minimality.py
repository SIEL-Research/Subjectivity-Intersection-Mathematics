#!/usr/bin/env python3
"""Audit whether complete severing is distinguishable from partial references."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
SEEDS = tuple(range(2026176001, 2026176065))
TEMPERATURES = (0.001, 0.002, 0.004)
REMOVAL_STEPS = (10, 20, 40)


def load_base():
    spec = importlib.util.spec_from_file_location("e014_projection_base", ROOT / "run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rank_readout(native: np.ndarray) -> np.ndarray:
    order = np.argsort(np.argsort(native, kind="stable"), kind="stable")
    return 1.0 - order / max(len(native) - 1, 1)


def load_e010_lines() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    records = defaultdict(lambda: defaultdict(dict))
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], round(float(row["b_angstrom"]), 1))
            mode = row["mode"]
            a = round(float(row["a_angstrom"]), 1)
            records[key][mode][a] = float(row["energy_hartree"])
    output = {}
    for (basis, b), modes in sorted(records.items()):
        a_values = sorted(modes["full"])
        output[f"{basis}_b{b:.1f}"] = {
            "basis": basis,
            "b_angstrom": b,
            "a_values": a_values,
            "full": np.asarray([modes["full"][a] for a in a_values]),
            "one_electron_cross_deleted": np.asarray([modes["one_electron_cross_deleted"][a] for a in a_values]),
            "without_edge_01": np.asarray([modes["without_edge_01"][a] for a in a_values]),
        }
    return output


def moving_average(values: np.ndarray, width: int) -> np.ndarray:
    pad = width // 2
    padded = np.pad(values, pad, mode="edge")
    return np.convolve(padded, np.ones(width) / width, mode="valid")


def references(native: np.ndarray, modes: dict) -> dict:
    flat = np.full_like(native, float(np.mean(native)))
    output = {
        "complete_flat_severing": flat,
        "partial_one_electron_deletion": modes["one_electron_cross_deleted"],
        "partial_single_edge_deletion": modes["without_edge_01"],
        "smoothed_width_3": moving_average(native, 3),
        "smoothed_width_5": moving_average(native, 5),
    }
    for retained in (0.10, 0.25, 0.50, 0.75, 0.90):
        output[f"retained_native_{retained:.2f}"] = flat + retained * (native - flat)
    return output


def score_rank(simulation: dict, readout: np.ndarray) -> tuple[dict, dict]:
    seed_scores = {
        condition: [float(np.mean(readout[np.asarray(trace, dtype=int)])) for trace in traces]
        for condition, traces in simulation["late_indices"].items()
    }
    return (
        {condition: float(np.mean(values)) for condition, values in seed_scores.items()},
        seed_scores,
    )


def main() -> None:
    base = load_base()
    lines = load_e010_lines()
    rows = []
    generation_failures = []
    for profile, modes in lines.items():
        native = modes["full"]
        readout = rank_readout(native)
        for reference_name, reference in references(native, modes).items():
            candidate = native - reference
            try:
                shift, shifted, overlap = base.select_mismatch(candidate)
            except ValueError as error:
                generation_failures.append({"profile": profile, "reference": reference_name, "error": str(error)})
                continue
            mismatch = reference + shifted
            for temperature in TEMPERATURES:
                for removal_steps in REMOVAL_STEPS:
                    simulation = base.trajectories(native, reference, mismatch, temperature, removal_steps, seeds=SEEDS)
                    scores, seed_scores = score_rank(simulation, readout)
                    rows.append({
                        "profile": profile,
                        "basis": modes["basis"],
                        "reference": reference_name,
                        "temperature": temperature,
                        "removal_steps": removal_steps,
                        "candidate_norm": float(np.linalg.norm(candidate)),
                        "candidate_fraction_of_complete": float(np.linalg.norm(candidate) / np.linalg.norm(native - np.mean(native))),
                        "mismatch_overlap": overlap,
                        "scores": scores,
                        "causal": base.causal_metrics(scores),
                        "paired_seed_support": base.paired_seed_support(seed_scores),
                    })
    reference_summary = {}
    for reference in sorted({row["reference"] for row in rows}):
        selected = [row for row in rows if row["reference"] == reference]
        margins = [row["causal"]["causal_margin"] for row in selected]
        reference_summary[reference] = {
            "configurations": len(selected),
            "causal_pass_fraction": float(np.mean([row["causal"]["pass"] for row in selected])),
            "positive_margin_fraction": float(np.mean([margin > 0.0 for margin in margins])),
            "minimum_margin": min(margins),
            "median_margin": float(np.median(margins)),
            "mean_candidate_fraction_of_complete": float(np.mean([row["candidate_fraction_of_complete"] for row in selected])),
        }
    summary = {
        "schema": "siel-e014-projection-minimality-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "reference_summary": reference_summary,
        "generation_failures": generation_failures,
        "rows": rows,
        "scope": {"not_confirmatory": True, "projection_family_selected_after_e013": True},
    }
    (RESULTS / "projection_minimality_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines_out = [
        "# Projection minimality exploration",
        "",
        "| Reference construction | Candidate fraction | Pass fraction | Median margin | Minimum margin |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, item in sorted(reference_summary.items(), key=lambda pair: pair[1]["mean_candidate_fraction_of_complete"], reverse=True):
        lines_out.append(
            f"| {name} | {item['mean_candidate_fraction_of_complete']:.6f} | {item['causal_pass_fraction']:.6f} | "
            f"{item['median_margin']:.6f} | {item['minimum_margin']:.6f} |"
        )
    lines_out.extend(["", f"Mismatch-generation failures: `{len(generation_failures)}`.", "", "This is result-informed local exploration."])
    (RESULTS / "PROJECTION_MINIMALITY_RESULT.md").write_text("\n".join(lines_out) + "\n")
    print(json.dumps(reference_summary, sort_keys=True))


if __name__ == "__main__":
    main()
