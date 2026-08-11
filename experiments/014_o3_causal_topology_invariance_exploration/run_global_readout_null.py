#!/usr/bin/env python3
"""Global randomized-readout null for the exploratory molecular O3 audit.

The statistic is fixed here as the mean, across all molecular profiles, of the
correct-return minus generated-mismatch score under the native energy-rank
readout.  Each null replicate independently permutes the readout labels within
every profile while preserving both trajectory ensembles and the readout value
distribution.  This asks whether the cross-profile effect survives severing the
link between native energy order and the visited molecular coordinates.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
NULL_REPLICATES = 4096
BASELINE_TEMPERATURE = 0.002
BASELINE_REMOVAL_STEPS = 20
BASELINE_TOTAL_STEPS = 100
BASELINE_SEEDS = tuple(range(2026174001, 2026174065))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def visitation_distribution(traces: list[list[int]], size: int) -> np.ndarray:
    counts = np.zeros(size, dtype=float)
    for trace in traces:
        counts += np.bincount(np.asarray(trace, dtype=int), minlength=size)
    return counts / float(np.sum(counts))


def main() -> None:
    base = load("e014_base_global_null", "run.py")
    rank_module = load("e014_rank_global_null", "run_rank_stress_and_nulls.py")
    profiles = base.load_profiles()

    records = []
    for name, profile in profiles.items():
        native = np.asarray(profile["native"], dtype=float)
        reference = np.asarray(profile["reference"], dtype=float)
        candidate = native - reference
        shift, shifted, overlap = base.select_mismatch(candidate)
        mismatch = reference + shifted

        correct = rank_module.return_trajectory(
            base, native, reference, native,
            BASELINE_TEMPERATURE, BASELINE_REMOVAL_STEPS,
            BASELINE_TOTAL_STEPS, BASELINE_SEEDS,
        )
        mismatched = rank_module.return_trajectory(
            base, native, reference, mismatch,
            BASELINE_TEMPERATURE, BASELINE_REMOVAL_STEPS,
            BASELINE_TOTAL_STEPS, BASELINE_SEEDS,
        )
        contrast = visitation_distribution(correct, len(native)) - visitation_distribution(mismatched, len(native))
        readout = rank_module.rank_readout(native)
        advantage = float(np.dot(contrast, readout))
        records.append({
            "profile": name,
            "basis": profile["basis"],
            "mismatch_shift_steps": shift,
            "mismatch_overlap": overlap,
            "native_rank_advantage": advantage,
            "contrast": contrast,
            "readout": readout,
        })

    observed = float(np.mean([item["native_rank_advantage"] for item in records]))
    rng = np.random.default_rng(2026176001)
    null_statistics = np.empty(NULL_REPLICATES, dtype=float)
    for replicate in range(NULL_REPLICATES):
        null_statistics[replicate] = float(np.mean([
            np.dot(item["contrast"], rng.permutation(item["readout"]))
            for item in records
        ]))

    exceedances = int(np.sum(null_statistics >= observed - 1e-15))
    conservative_p = float((exceedances + 1) / (NULL_REPLICATES + 1))
    null_sd = float(np.std(null_statistics, ddof=1))
    z_score = float((observed - float(np.mean(null_statistics))) / null_sd)
    summary = {
        "schema": "siel-e014-global-randomized-readout-null-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "design": {
            "profile_count": len(records),
            "null_replicates": NULL_REPLICATES,
            "temperature": BASELINE_TEMPERATURE,
            "removal_steps": BASELINE_REMOVAL_STEPS,
            "total_steps": BASELINE_TOTAL_STEPS,
            "seeds": list(BASELINE_SEEDS),
            "statistic": "mean profile-level correct-return minus generated-mismatch native-energy-rank advantage",
            "null": "independent within-profile permutation of rank-readout labels; trajectories and readout distributions fixed",
        },
        "result": {
            "observed_global_mean_advantage": observed,
            "all_profile_advantages_positive": all(item["native_rank_advantage"] > 0.0 for item in records),
            "minimum_profile_advantage": min(item["native_rank_advantage"] for item in records),
            "median_profile_advantage": float(np.median([item["native_rank_advantage"] for item in records])),
            "null_mean": float(np.mean(null_statistics)),
            "null_standard_deviation": null_sd,
            "z_score": z_score,
            "exceedances": exceedances,
            "conservative_monte_carlo_p": conservative_p,
        },
        "profiles": [{key: value for key, value in item.items() if key not in ("contrast", "readout")} for item in records],
        "scope": {
            "not_confirmatory": True,
            "readout_selected_after_exploration": True,
            "does_not_establish_projection_uniqueness": True,
        },
    }
    (RESULTS / "global_readout_null_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Global randomized-readout null exploration",
        "",
        f"Profiles: `{len(records)}`.",
        f"Null replicates: `{NULL_REPLICATES}`.",
        f"Observed global mean advantage: `{observed:.9f}`.",
        f"All profile advantages positive: `{summary['result']['all_profile_advantages_positive']}`.",
        f"Minimum profile advantage: `{summary['result']['minimum_profile_advantage']:.9f}`.",
        f"Null mean (SD): `{summary['result']['null_mean']:.9f}` (`{null_sd:.9f}`).",
        f"Global z score: `{z_score:.6f}`.",
        f"Conservative Monte Carlo p: `{conservative_p:.9f}` ({exceedances}/{NULL_REPLICATES} raw exceedances).",
        "",
        "The aggregate native-energy-rank advantage survives a null that preserves the trajectories but severs the coordinate-to-energy-rank assignment independently in every profile.",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "GLOBAL_READOUT_NULL_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary["result"], sort_keys=True))


if __name__ == "__main__":
    main()
