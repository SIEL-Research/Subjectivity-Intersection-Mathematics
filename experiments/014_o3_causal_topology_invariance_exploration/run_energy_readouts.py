#!/usr/bin/env python3
"""Compare coordinate-free or native-energy-derived whole-formation readouts."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def load_base():
    spec = importlib.util.spec_from_file_location("e014_base", ROOT / "run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def readout_vector(native: np.ndarray, temperature: float, method: str) -> np.ndarray:
    delta = native - float(np.min(native))
    positive = np.sort(np.unique(delta[delta > 1e-12]))
    depth = max(float(np.max(delta)), 1e-12)
    gap = float(positive[0]) if len(positive) else depth
    ranks = np.empty(len(native), dtype=float)
    order = np.argsort(np.argsort(native, kind="stable"), kind="stable")
    ranks[:] = 1.0 - order / max(len(native) - 1, 1)
    if method == "exact_minimum":
        return (delta <= 1e-10).astype(float)
    if method == "boltzmann_temperature":
        return np.exp(-delta / max(temperature, 1e-12))
    if method == "native_depth_exponential":
        return np.exp(-delta / depth)
    if method == "native_depth_linear":
        return np.clip(1.0 - delta / depth, 0.0, 1.0)
    if method == "first_gap_exponential":
        return np.exp(-delta / gap)
    if method == "energy_rank":
        return ranks
    if method.startswith("native_quantile_"):
        quantile = float(method.rsplit("_", 1)[1])
        cutoff = float(np.quantile(native, quantile))
        return (native <= cutoff).astype(float)
    raise ValueError(method)


def score_simulation(simulation: dict, readout: np.ndarray) -> tuple[dict, dict]:
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
    profiles = base.load_profiles()
    methods = (
        "exact_minimum",
        "boltzmann_temperature",
        "native_depth_exponential",
        "native_depth_linear",
        "first_gap_exponential",
        "energy_rank",
        "native_quantile_0.10",
        "native_quantile_0.20",
        "native_quantile_0.25",
        "native_quantile_0.33",
    )
    rows = []
    for profile_name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        shift, shifted, overlap = base.select_mismatch(candidate)
        mismatch = reference + shifted
        for temperature in base.TEMPERATURES:
            vectors = {method: readout_vector(native, temperature, method) for method in methods}
            for removal_steps in base.REMOVAL_STEPS:
                simulation = base.trajectories(native, reference, mismatch, temperature, removal_steps)
                for method, vector in vectors.items():
                    scores, seed_scores = score_simulation(simulation, vector)
                    causal = base.causal_metrics(scores)
                    rows.append({
                        "profile": profile_name,
                        "basis": profile["basis"],
                        "b_angstrom": profile["b_angstrom"],
                        "temperature": temperature,
                        "removal_steps": removal_steps,
                        "method": method,
                        "mismatch_shift_steps": shift,
                        "mismatch_overlap": overlap,
                        "scores": scores,
                        "causal": causal,
                        "paired_seed_support": base.paired_seed_support(seed_scores),
                    })
    method_summary = {}
    for method in methods:
        selected = [row for row in rows if row["method"] == method]
        profiles_pass = defaultdict(list)
        for row in selected:
            profiles_pass[row["profile"]].append(row["causal"]["pass"])
        method_summary[method] = {
            "configurations": len(selected),
            "causal_pass_fraction": float(np.mean([row["causal"]["pass"] for row in selected])),
            "positive_margin_fraction": float(np.mean([row["causal"]["causal_margin"] > 0.0 for row in selected])),
            "minimum_margin": min(row["causal"]["causal_margin"] for row in selected),
            "median_margin": float(np.median([row["causal"]["causal_margin"] for row in selected])),
            "profiles_with_all_configs_passing": sum(all(values) for values in profiles_pass.values()),
            "profiles_with_positive_majority": sum(float(np.mean(values)) > 0.5 for values in profiles_pass.values()),
            "profile_count": len(profiles_pass),
        }
    summary = {
        "schema": "siel-e014-native-energy-readout-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "methods": method_summary,
        "rows": rows,
        "scope": {"not_confirmatory": True, "method_comparison_is_result_informed": True},
    }
    (RESULTS / "energy_readout_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Native-energy readout comparison",
        "",
        "| Method | Pass fraction | Median margin | Minimum margin | All-pass profiles | Positive-majority profiles |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, item in sorted(method_summary.items(), key=lambda pair: pair[1]["causal_pass_fraction"], reverse=True):
        lines.append(
            f"| {method} | {item['causal_pass_fraction']:.6f} | {item['median_margin']:.6f} | "
            f"{item['minimum_margin']:.6f} | {item['profiles_with_all_configs_passing']}/{item['profile_count']} | "
            f"{item['profiles_with_positive_majority']}/{item['profile_count']} |"
        )
    lines.extend(["", "All methods were compared after E013 and are exploratory."])
    (RESULTS / "ENERGY_READOUT_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(method_summary, sort_keys=True))


if __name__ == "__main__":
    main()
