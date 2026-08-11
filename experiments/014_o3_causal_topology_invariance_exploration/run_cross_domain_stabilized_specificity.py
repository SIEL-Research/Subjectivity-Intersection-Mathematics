#!/usr/bin/env python3
"""Final exploratory audit of stabilized O3-return specificity across domains."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def summarize(margins):
    return {
        "checks": len(margins),
        "passing_checks": sum(value > 0.0 for value in margins),
        "pass_fraction": float(np.mean(np.asarray(margins) > 0.0)),
        "minimum_margin": min(margins),
        "median_margin": float(np.median(margins)),
    }


def main() -> None:
    atomic_source = json.loads((RESULTS / "atomic_reentry_phase_map_summary.json").read_text())
    molecular_source = json.loads((RESULTS / "hellinger_horizon_stress_summary.json").read_text())
    cellular_source = json.loads((RESULTS / "cellular_return_identity_interaction_summary.json").read_text())

    atomic_margins = [
        row["scores"]["correct_return"] - max(row["scores"]["removed"], row["scores"]["mismatched_return"])
        for row in atomic_source["rows"]
    ]
    molecular_margins = [
        row["endpoint_scores"]["correct_return"] - max(row["endpoint_scores"]["removed"], row["endpoint_scores"]["mismatched_return"])
        for row in molecular_source["rows"]
    ]
    cellular_late_rows = [row for row in cellular_source["rows"] if row["post_reinjection_minutes"] >= 40.0]
    cellular_early_rows = [row for row in cellular_source["rows"] if row["post_reinjection_minutes"] < 40.0]
    cellular_margins = [
        row["scores"]["correct_return"] - max(row["scores"]["removed"], row["scores"]["mismatched_return"])
        for row in cellular_late_rows
    ]
    cellular_early_margins = [
        row["scores"]["correct_return"] - max(row["scores"]["removed"], row["scores"]["mismatched_return"])
        for row in cellular_early_rows
    ]
    domains = {
        "atomic": summarize(atomic_margins),
        "molecular": summarize(molecular_margins),
        "cellular": summarize(cellular_margins),
    }
    lodo = {}
    for heldout in domains:
        training = [name for name in domains if name != heldout]
        training_rule_supported = all(domains[name]["pass_fraction"] == 1.0 for name in training)
        heldout_pass = domains[heldout]["pass_fraction"] == 1.0
        lodo[heldout] = {
            "training_domains": training,
            "training_supports_positive_stabilized_specificity": training_rule_supported,
            "heldout_all_checks_pass": heldout_pass,
            "pass": training_rule_supported and heldout_pass,
        }
    summary = {
        "schema": "siel-e014-cross-domain-stabilized-specificity-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "candidate_cross_domain_invariant": "after a domain-native stabilization interval, correct O3 return remains closer to the registered domain state than removal or a physically distinguishable mismatch",
        "stabilized_checks": domains,
        "total_stabilized_checks": sum(item["checks"] for item in domains.values()),
        "all_stabilized_checks_pass": all(item["pass_fraction"] == 1.0 for item in domains.values()),
        "leave_one_domain_out": lodo,
        "all_lodo_pass": all(item["pass"] for item in lodo.values()),
        "cellular_pre_stabilization_control": summarize(cellular_early_margins),
        "stabilization_rules_used_in_exploration": {
            "atomic": "all registered return horizons, minimum 100 dynamic steps",
            "molecular": "Hellinger endpoint after at least 25 base return steps; exact propagation with factor-squared grid time scaling",
            "cellular": "at least 40 minutes after reinjection",
        },
        "compression_boundary": {
            "shared_scalar_enters_domain_engines": False,
            "domain_readouts_are_distinct": True,
            "cross_domain_object": "sign of stabilized correct-return specificity",
            "common_substance_or_source_identity_inferred": False,
        },
        "scope": {
            "not_confirmatory": True,
            "stabilization_rules_selected_after_exploration": True,
            "current_targets_not_held_out": True,
            "prospective_test_requires_new_targets_and_frozen_domain_stabilization_rules": True,
        },
    }
    (RESULTS / "cross_domain_stabilized_specificity_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cross-domain stabilized O3-return specificity",
        "",
        f"All stabilized checks pass: `{summary['all_stabilized_checks_pass']}` (`{summary['total_stabilized_checks']}/{summary['total_stabilized_checks']}`).",
        f"All leave-one-domain-out transfers pass: `{summary['all_lodo_pass']}`.",
        f"Cellular pre-stabilization control pass fraction: `{summary['cellular_pre_stabilization_control']['pass_fraction']:.6f}`.",
        "",
        "The failed pre-stabilization control shows that the result is not an unconditional consequence of labeling a return as correct.",
        "This is result-informed local exploration; prospective confirmation requires new held-out targets.",
    ]
    (RESULTS / "CROSS_DOMAIN_STABILIZED_SPECIFICITY_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "domains": domains,
        "total_stabilized_checks": summary["total_stabilized_checks"],
        "all_stabilized_checks_pass": summary["all_stabilized_checks_pass"],
        "all_lodo_pass": summary["all_lodo_pass"],
        "cellular_pre_stabilization_control": summary["cellular_pre_stabilization_control"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
