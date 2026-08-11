#!/usr/bin/env python3
"""Higher-power adjudication of failures found by the physical mismatch audit."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
SEEDS = tuple(range(2026178001, 2026179025))
TOTAL_STEPS = 100


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    base = load("e014_base_failure_adjudication", "run.py")
    rank_module = load("e014_rank_failure_adjudication", "run_rank_stress_and_nulls.py")
    physical = load("e014_physical_failure_adjudication", "run_physical_mismatch_audit.py")
    profiles = base.load_profiles()
    prior = json.loads((RESULTS / "physical_mismatch_summary.json").read_text())
    scenarios = sorted({
        (item["profile"], item["alternative"], float(item["temperature"]), int(item["removal_steps"]))
        for item in prior["failures"]
    })

    records = []
    correct_cache = {}
    for profile_name, alternative_name, temperature, removal_steps in scenarios:
        profile = profiles[profile_name]
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        alternatives = physical.alternatives_for(profile_name, profile, profiles)
        alternative_candidate, family = alternatives[alternative_name]
        alternative = reference + alternative_candidate
        readout = rank_module.rank_readout(native)
        cache_key = (profile_name, temperature, removal_steps)
        if cache_key not in correct_cache:
            correct_cache[cache_key] = rank_module.return_trajectory(
                base, native, reference, native, temperature, removal_steps, TOTAL_STEPS, SEEDS,
            )
        alternative_traces = rank_module.return_trajectory(
            base, native, reference, alternative, temperature, removal_steps, TOTAL_STEPS, SEEDS,
        )
        correct_score, correct_seed = rank_module.score_late(correct_cache[cache_key], readout)
        alternative_score, alternative_seed = rank_module.score_late(alternative_traces, readout)
        differences = np.asarray(correct_seed) - np.asarray(alternative_seed)
        mean = float(np.mean(differences))
        standard_error = float(np.std(differences, ddof=1) / math.sqrt(len(differences)))
        lower = mean - 1.96 * standard_error
        upper = mean + 1.96 * standard_error
        if lower > 0.0:
            decision = "CORRECT_RETURN_SUPPORTED"
        elif upper < 0.0:
            decision = "ALTERNATIVE_RETURN_SUPPORTED"
        else:
            decision = "INCONCLUSIVE"
        records.append({
            "profile": profile_name,
            "alternative": alternative_name,
            "family": family,
            "temperature": temperature,
            "removal_steps": removal_steps,
            "seed_count": len(SEEDS),
            "correct_score": correct_score,
            "alternative_score": alternative_score,
            "paired_mean_advantage": mean,
            "paired_standard_error": standard_error,
            "normal_95_interval": [lower, upper],
            "positive_seed_fraction": float(np.mean(differences > 0.0)),
            "decision": decision,
        })

    counts = {label: sum(item["decision"] == label for item in records) for label in (
        "CORRECT_RETURN_SUPPORTED", "ALTERNATIVE_RETURN_SUPPORTED", "INCONCLUSIVE"
    )}
    summary = {
        "schema": "siel-e014-mismatch-failure-adjudication-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "source": "all structurally distinct non-wins from physical_mismatch_summary.json",
            "scenario_count": len(records),
            "seed_count": len(SEEDS),
            "paired_common_seed_analysis": True,
            "interval": "unadjusted normal 95% interval for paired mean difference",
        },
        "decision_counts": counts,
        "records": records,
        "scope": {
            "not_confirmatory": True,
            "result_informed_targeted_followup": True,
            "intervals_not_multiplicity_adjusted": True,
        },
    }
    (RESULTS / "mismatch_failure_adjudication_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Physical mismatch failure adjudication",
        "",
        f"Scenarios carried forward: `{len(records)}`.",
        f"Seeds per scenario: `{len(SEEDS)}`.",
        f"Correct return supported: `{counts['CORRECT_RETURN_SUPPORTED']}`.",
        f"Alternative return supported: `{counts['ALTERNATIVE_RETURN_SUPPORTED']}`.",
        f"Inconclusive: `{counts['INCONCLUSIVE']}`.",
        "",
        "Every non-win from the lower-power physical mismatch audit is preserved. This targeted follow-up is result-informed and nonconfirmatory.",
    ]
    (RESULTS / "MISMATCH_FAILURE_ADJUDICATION_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"decision_counts": counts, "records": records}, sort_keys=True))


if __name__ == "__main__":
    main()
