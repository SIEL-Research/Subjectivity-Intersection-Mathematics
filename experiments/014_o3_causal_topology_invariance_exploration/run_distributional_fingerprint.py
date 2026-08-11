#!/usr/bin/env python3
"""Test full dynamic fingerprints instead of a minimum-centred scalar readout."""

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
REMOVAL_STEPS = (10, 20, 40)
TOTAL_STEPS = 100
SEEDS = tuple(range(2026180001, 2026180065))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def distribution(traces: list[list[int]], size: int) -> np.ndarray:
    counts = np.zeros(size, dtype=float)
    for trace in traces:
        counts += np.bincount(np.asarray(trace, dtype=int), minlength=size)
    counts += 0.5
    return counts / float(np.sum(counts))


def stationary_distribution(native: np.ndarray, temperature: float) -> np.ndarray:
    shifted = native - float(np.min(native))
    weights = np.exp(-shifted / temperature)
    degrees = np.full(len(native), 2.0)
    degrees[0] = degrees[-1] = 1.0
    weights *= degrees
    return weights / float(np.sum(weights))


def js_similarity(observed: np.ndarray, target: np.ndarray) -> float:
    midpoint = 0.5 * (observed + target)
    observed_support = observed > 0.0
    target_support = target > 0.0
    divergence = 0.5 * float(np.sum(observed[observed_support] * np.log(observed[observed_support] / midpoint[observed_support])))
    divergence += 0.5 * float(np.sum(target[target_support] * np.log(target[target_support] / midpoint[target_support])))
    return 1.0 - divergence / math.log(2.0)


def wasserstein_similarity(observed: np.ndarray, target: np.ndarray, coordinates: np.ndarray) -> float:
    widths = np.diff(coordinates)
    distance = float(np.sum(np.abs(np.cumsum(observed)[:-1] - np.cumsum(target)[:-1]) * widths))
    return 1.0 - distance / float(coordinates[-1] - coordinates[0])


def score(traces, size, target, coordinates):
    observed = distribution(traces, size)
    return {
        "js_similarity": js_similarity(observed, target),
        "wasserstein_similarity": wasserstein_similarity(observed, target, coordinates),
    }


def causal(scores: dict, method: str) -> dict:
    values = {condition: item[method] for condition, item in scores.items()}
    edges = {
        "intact_gt_removed": values["intact"] > values["removed"],
        "intact_gt_mismatch": values["intact"] > values["mismatched_return"],
        "correct_gt_removed": values["correct_return"] > values["removed"],
        "correct_gt_mismatch": values["correct_return"] > values["mismatched_return"],
    }
    return {
        "pass": all(edges.values()),
        "edges": edges,
        "margin": min(values["intact"], values["correct_return"]) - max(values["removed"], values["mismatched_return"]),
    }


def main() -> None:
    base = load("e014_base_fingerprint", "run.py")
    rank_module = load("e014_rank_fingerprint", "run_rank_stress_and_nulls.py")
    physical = load("e014_physical_fingerprint", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    rows = []
    for profile_name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        coordinates = np.asarray(profile["a_values"], dtype=float)
        candidate = native - reference
        alternatives = physical.alternatives_for(profile_name, profile, profiles)
        alternatives = {
            name: (values, family, base.centered_overlap(candidate, values))
            for name, (values, family) in alternatives.items()
            if base.centered_overlap(candidate, values) <= base.MAX_OVERLAP
        }
        for temperature in TEMPERATURES:
            target = stationary_distribution(native, temperature)
            for removal_steps in REMOVAL_STEPS:
                # The placeholder mismatch is not used for intact/removed/correct.
                common = base.trajectories(native, reference, reference, temperature, removal_steps, seeds=SEEDS, total_steps=TOTAL_STEPS)
                common_scores = {
                    condition: score(common["late_indices"][condition], len(native), target, coordinates)
                    for condition in ("intact", "removed", "correct_return")
                }
                for alternative_name, (alternative_candidate, family, overlap) in alternatives.items():
                    mismatch_surface = reference + alternative_candidate
                    mismatch_traces = rank_module.return_trajectory(
                        base, native, reference, mismatch_surface, temperature, removal_steps, TOTAL_STEPS, SEEDS,
                    )
                    scores = dict(common_scores)
                    scores["mismatched_return"] = score(mismatch_traces, len(native), target, coordinates)
                    rows.append({
                        "profile": profile_name,
                        "basis": profile["basis"],
                        "alternative": alternative_name,
                        "family": family,
                        "centered_overlap": overlap,
                        "temperature": temperature,
                        "removal_steps": removal_steps,
                        "scores": scores,
                        "causal": {method: causal(scores, method) for method in ("js_similarity", "wasserstein_similarity")},
                    })

    summary_methods = {}
    for method in ("js_similarity", "wasserstein_similarity"):
        summary_methods[method] = {
            "comparisons": len(rows),
            "pass_fraction": float(np.mean([row["causal"][method]["pass"] for row in rows])),
            "minimum_margin": min(row["causal"][method]["margin"] for row in rows),
            "median_margin": float(np.median([row["causal"][method]["margin"] for row in rows])),
            "failure_count": sum(not row["causal"][method]["pass"] for row in rows),
        }
    failure_union = [row for row in rows if not all(row["causal"][method]["pass"] for method in summary_methods)]
    by_family = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row)
    summary = {
        "schema": "siel-e014-distributional-fingerprint-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_count": len(profiles),
            "comparison_count": len(rows),
            "target": "exact stationary coordinate distribution of each native implemented Metropolis chain",
            "readouts": ["Jensen-Shannon similarity", "normalised one-dimensional Wasserstein similarity"],
            "pseudocount_per_coordinate": 0.5,
            "periodic_mismatches": False,
        },
        "methods": summary_methods,
        "by_family": {
            family: {
                method: {
                    "comparisons": len(items),
                    "pass_fraction": float(np.mean([row["causal"][method]["pass"] for row in items])),
                    "minimum_margin": min(row["causal"][method]["margin"] for row in items),
                }
                for method in summary_methods
            }
            for family, items in sorted(by_family.items())
        },
        "failure_union_count": len(failure_union),
        "failures": failure_union,
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "distributional_readouts_selected_after_energy_rank_failure_analysis": True,
            "stationary_target_is_model_native_not_empirically_independent": True,
        },
    }
    (RESULTS / "distributional_fingerprint_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Distributional whole-fingerprint exploration",
        "",
        "The readout compares the complete late coordinate distribution with the exact stationary fingerprint of the native implemented chain; it is not restricted to occupancy near the minimum.",
        "",
    ]
    for method, item in summary_methods.items():
        lines.append(f"- {method}: `{item['pass_fraction']:.6f}` pass fraction; `{item['failure_count']}` failures; minimum margin `{item['minimum_margin']:.9f}`.")
    lines += ["", "This is result-informed local exploration, not confirmatory evidence."]
    (RESULTS / "DISTRIBUTIONAL_FINGERPRINT_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"methods": summary_methods, "by_family": summary["by_family"], "failure_union_count": len(failure_union)}, sort_keys=True))


if __name__ == "__main__":
    main()
