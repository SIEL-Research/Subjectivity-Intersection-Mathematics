#!/usr/bin/env python3
"""Integrate domain-native re-entry results only at the causal-order level."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
NULL_REPLICATES = 65536
TOLERANCE = 1e-12


def nonincreasing(values):
    return all(right <= left + TOLERANCE for left, right in zip(values, values[1:]))


def nondecreasing(values):
    return all(right + TOLERANCE >= left for left, right in zip(values, values[1:]))


def average_ranks(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    index = 0
    while index < len(values):
        end = index + 1
        while end < len(values) and values[order[end]] == values[order[index]]:
            end += 1
        ranks[order[index:end]] = 0.5 * (index + end - 1)
        index = end
    return ranks


def spearman(x, y):
    xr = average_ranks(x)
    yr = average_ranks(y)
    if np.std(xr) == 0.0 or np.std(yr) == 0.0:
        return 0.0
    return float(np.corrcoef(xr, yr)[0, 1])


def grouped_monotonicity(rows, group_fields, axis_field, value_getter, direction):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in group_fields)].append(row)
    records = []
    check = nonincreasing if direction == "decreasing" else nondecreasing
    for key, items in sorted(groups.items(), key=lambda item: str(item[0])):
        ordered = sorted(items, key=lambda row: row[axis_field])
        values = [value_getter(row) for row in ordered]
        records.append({
            "group": list(key),
            "axis": [row[axis_field] for row in ordered],
            "values": values,
            "pass": check(values),
        })
    return {
        "direction": direction,
        "group_count": len(records),
        "passing_group_count": sum(item["pass"] for item in records),
        "pass_fraction": float(np.mean([item["pass"] for item in records])),
        "failures": [item for item in records if not item["pass"]],
    }


def marginal_sequence(rows, axis_field, value_getter):
    groups = defaultdict(list)
    for row in rows:
        groups[row[axis_field]].append(value_getter(row))
    axis = sorted(groups)
    return axis, [float(np.mean(groups[value])) for value in axis]


def main() -> None:
    atomic = json.loads((RESULTS / "atomic_reentry_phase_map_summary.json").read_text())
    molecular = json.loads((RESULTS / "molecular_reentry_phase_map_summary.json").read_text())
    cellular = json.loads((RESULTS / "cellular_reentry_window_summary.json").read_text())
    atomic_rows = atomic["rows"]
    molecular_rows = molecular["rows"]
    cellular_rows = cellular["rows"]

    atomic_checks = {
        "longer_removal_lowers_recovery": grouped_monotonicity(
            atomic_rows, ("target", "return_steps"), "removal_steps", lambda row: row["scores"]["correct_return"], "decreasing"
        ),
        "longer_return_raises_recovery": grouped_monotonicity(
            atomic_rows, ("target", "removal_steps"), "return_steps", lambda row: row["scores"]["correct_return"], "increasing"
        ),
    }
    molecular_checks = {
        "longer_removal_lowers_recovery": grouped_monotonicity(
            molecular_rows, ("profile", "temperature", "return_steps"), "removal_steps", lambda row: row["similarities_to_matched_intact"]["correct_return"], "decreasing"
        ),
        "longer_return_raises_recovery": grouped_monotonicity(
            molecular_rows, ("profile", "temperature", "removal_steps"), "return_steps", lambda row: row["similarities_to_matched_intact"]["correct_return"], "increasing"
        ),
    }
    cellular_checks = {
        "later_reinjection_lowers_recovery": grouped_monotonicity(
            cellular_rows, ("damage_amplitude",), "reinjection_minutes", lambda row: row["metrics"]["continuous_recovery_score"]["values"]["correct_return"], "decreasing"
        ),
    }

    sequences = []
    for label, rows, axis, getter, direction in (
        ("atomic_removal", atomic_rows, "removal_steps", lambda row: row["scores"]["correct_return"], -1),
        ("atomic_return", atomic_rows, "return_steps", lambda row: row["scores"]["correct_return"], 1),
        ("molecular_removal", molecular_rows, "removal_steps", lambda row: row["similarities_to_matched_intact"]["correct_return"], -1),
        ("molecular_return", molecular_rows, "return_steps", lambda row: row["similarities_to_matched_intact"]["correct_return"], 1),
        ("cellular_reinjection", cellular_rows, "reinjection_minutes", lambda row: row["metrics"]["continuous_recovery_score"]["values"]["correct_return"], -1),
        ("cellular_damage", cellular_rows, "damage_amplitude", lambda row: row["metrics"]["continuous_recovery_score"]["values"]["correct_return"], -1),
    ):
        x, y = marginal_sequence(rows, axis, getter)
        rho = spearman(x, y)
        sequences.append({"label": label, "axis": x, "mean_recovery": y, "expected_direction": direction, "spearman_rho": rho, "directed_rho": direction * rho})

    observed = float(sum(item["directed_rho"] for item in sequences))
    rng = np.random.default_rng(2026183001)
    null = np.empty(NULL_REPLICATES, dtype=float)
    for replicate in range(NULL_REPLICATES):
        null[replicate] = sum(
            item["expected_direction"] * spearman(item["axis"], rng.permutation(item["mean_recovery"]))
            for item in sequences
        )
    exceedances = int(np.sum(null >= observed - 1e-15))
    p_value = float((exceedances + 1) / (NULL_REPLICATES + 1))

    all_checks = list(atomic_checks.values()) + list(molecular_checks.values()) + list(cellular_checks.values())
    summary = {
        "schema": "siel-e014-cross-domain-dynamic-order-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "claim_tested": "domain-native O3 re-entry recovery decreases with greater interruption burden and increases with greater post-return opportunity",
        "compression_boundary": {
            "shared_quantity_entering_domain_engines": False,
            "domain_native_readouts": {
                "atomic": "full quantum-density fingerprint similarity",
                "molecular": "full coordinate-dynamics fingerprint similarity",
                "cellular": "E009 viability plus exploratory module-recovery diagnostic",
            },
            "cross_domain_comparison_level": "causal order only",
            "source_level_identity_inferred": False,
            "common_scalar_law_inferred": False,
        },
        "monotonicity": {
            "atomic": atomic_checks,
            "molecular": molecular_checks,
            "cellular": cellular_checks,
            "all_registered_direction_groups_pass": all(item["pass_fraction"] == 1.0 for item in all_checks),
            "total_groups": sum(item["group_count"] for item in all_checks),
            "passing_groups": sum(item["passing_group_count"] for item in all_checks),
        },
        "marginal_order_permutation_null": {
            "sequences": sequences,
            "observed_sum_directed_spearman": observed,
            "null_replicates": NULL_REPLICATES,
            "exceedances": exceedances,
            "conservative_monte_carlo_p": p_value,
            "null_mean": float(np.mean(null)),
            "null_standard_deviation": float(np.std(null, ddof=1)),
        },
        "scope": {
            "not_confirmatory": True,
            "axes_readouts_and_order_statistic_selected_after_E012_E013": True,
            "cellular_continuous_readout_is_secondary_and_exploratory": True,
            "does_not_identify_one_cross_domain_substance_or_microscopic_law": True,
        },
    }
    (RESULTS / "cross_domain_dynamic_order_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cross-domain dynamic re-entry order exploration",
        "",
        f"All within-domain directional groups pass: `{summary['monotonicity']['all_registered_direction_groups_pass']}`.",
        f"Passing groups: `{summary['monotonicity']['passing_groups']}/{summary['monotonicity']['total_groups']}`.",
        f"Observed sum of directed marginal Spearman correlations: `{observed:.9f}`.",
        f"Label-permutation null: `{exceedances}/{NULL_REPLICATES}` exceedances; conservative p `{p_value:.9f}`.",
        "",
        "The integration is made at the causal-order level after each independent domain engine has produced its own readout. It does not infer source-level identity from scalar agreement.",
        "This is result-informed local exploration, not confirmatory evidence.",
    ]
    (RESULTS / "CROSS_DOMAIN_DYNAMIC_ORDER_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "all_groups_pass": summary["monotonicity"]["all_registered_direction_groups_pass"],
        "passing_groups": summary["monotonicity"]["passing_groups"],
        "total_groups": summary["monotonicity"]["total_groups"],
        "sequences": sequences,
        "observed_directed_rho_sum": observed,
        "permutation_exceedances": exceedances,
        "permutation_p": p_value,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
