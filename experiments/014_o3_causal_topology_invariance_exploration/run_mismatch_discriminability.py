#!/usr/bin/env python3
"""Relate specificity outcomes to pre-outcome dynamic distinguishability."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
POOLED_LATE_OBSERVATIONS = 64 * 25


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    base = load("e014_base_discriminability", "run.py")
    fingerprint = load("e014_fingerprint_discriminability", "run_distributional_fingerprint.py")
    physical = load("e014_physical_discriminability", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    previous = json.loads((RESULTS / "distributional_fingerprint_summary.json").read_text())

    rows = []
    for row in previous["rows"]:
        profile = profiles[row["profile"]]
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        alternative_candidate = physical.alternatives_for(row["profile"], profile, profiles)[row["alternative"]][0]
        native_target = fingerprint.stationary_distribution(native, row["temperature"])
        alternative_target = fingerprint.stationary_distribution(reference + alternative_candidate, row["temperature"])
        normalized_js_separation = 1.0 - fingerprint.js_similarity(alternative_target, native_target)
        rows.append({
            "profile": row["profile"],
            "alternative": row["alternative"],
            "family": row["family"],
            "temperature": row["temperature"],
            "removal_steps": row["removal_steps"],
            "normalized_exact_target_js_separation": normalized_js_separation,
            "observed_causal_pass": row["causal"]["js_similarity"]["pass"],
            "observed_causal_margin": row["causal"]["js_similarity"]["margin"],
        })

    thresholds = sorted(set((
        0.0,
        1.0 / POOLED_LATE_OBSERVATIONS,
        2.0 / POOLED_LATE_OBSERVATIONS,
        4.0 / POOLED_LATE_OBSERVATIONS,
        8.0 / POOLED_LATE_OBSERVATIONS,
        0.005,
        0.01,
        0.02,
        0.05,
    )))
    sweep = []
    for threshold in thresholds:
        eligible = [row for row in rows if row["normalized_exact_target_js_separation"] >= threshold]
        sweep.append({
            "minimum_target_js_separation": threshold,
            "eligible_comparisons": len(eligible),
            "excluded_as_dynamically_indistinguishable": len(rows) - len(eligible),
            "causal_pass_fraction": float(np.mean([row["observed_causal_pass"] for row in eligible])) if eligible else None,
            "failure_count": sum(not row["observed_causal_pass"] for row in eligible),
            "minimum_margin": min((row["observed_causal_margin"] for row in eligible), default=None),
        })

    failures = [row for row in rows if not row["observed_causal_pass"]]
    summary = {
        "schema": "siel-e014-mismatch-discriminability-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "comparison_count": len(rows),
            "pooled_late_observations": POOLED_LATE_OBSERVATIONS,
            "eligibility_variable": "exact normalized Jensen-Shannon separation between native and alternative stationary distributions",
            "eligibility_computed_without_observed_trajectory_scores": True,
        },
        "threshold_sweep": sweep,
        "failure_target_separations": [row["normalized_exact_target_js_separation"] for row in failures],
        "minimum_passing_target_separation": min(row["normalized_exact_target_js_separation"] for row in rows if row["observed_causal_pass"]),
        "maximum_failing_target_separation": max(row["normalized_exact_target_js_separation"] for row in failures),
        "rows": rows,
        "scope": {
            "not_confirmatory": True,
            "thresholds_examined_after_fingerprint_results": True,
            "future_threshold_requires_new held_out_targets": True,
        },
    }
    (RESULTS / "mismatch_discriminability_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Mismatch dynamic-discriminability exploration",
        "",
        f"Comparisons: `{len(rows)}`.",
        f"Maximum exact target separation among observed failures: `{summary['maximum_failing_target_separation']:.9f}`.",
        "",
        "A carrier-level transformation is not an operational specificity null when it is indistinguishable under the registered whole-formation readout at the chosen regime.",
        "The threshold sweep is result-informed and cannot be used as confirmatory evidence on these same profiles.",
    ]
    (RESULTS / "MISMATCH_DISCRIMINABILITY_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "maximum_failing_target_separation": summary["maximum_failing_target_separation"],
        "minimum_passing_target_separation": summary["minimum_passing_target_separation"],
        "threshold_sweep": sweep,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
