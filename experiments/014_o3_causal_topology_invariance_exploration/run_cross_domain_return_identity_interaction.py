#!/usr/bin/env python3
"""Cross-domain transfer audit of O3 return-identity by recovery-time interaction."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
NULL_REPLICATES = 65536


def headroom_fraction(initial: float, final: float) -> float:
    return (final - initial) / max(1.0 - initial, 1e-12)


def phase_interactions(rows, group_fields, score_getter):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in group_fields)].append(row)
    output = []
    for key, items in sorted(groups.items(), key=lambda item: str(item[0])):
        ordered = sorted(items, key=lambda row: row["return_steps"])
        fractions = {
            condition: headroom_fraction(score_getter(ordered[0], condition), score_getter(ordered[-1], condition))
            for condition in ("removed", "mismatched_return", "correct_return")
        }
        output.append({
            "group": list(key),
            "headroom_normalized_recovery": fractions,
            "correct_minus_mismatch_interaction": fractions["correct_return"] - fractions["mismatched_return"],
            "correct_minus_removed_interaction": fractions["correct_return"] - fractions["removed"],
        })
    return output


def summarize(records):
    mismatch = [item["correct_minus_mismatch_interaction"] for item in records]
    removed = [item["correct_minus_removed_interaction"] for item in records]
    return {
        "group_count": len(records),
        "all_correct_exceeds_mismatch": all(value > 0.0 for value in mismatch),
        "all_correct_exceeds_removed": all(value > 0.0 for value in removed),
        "minimum_correct_minus_mismatch": min(mismatch),
        "median_correct_minus_mismatch": float(np.median(mismatch)),
        "minimum_correct_minus_removed": min(removed),
        "median_correct_minus_removed": float(np.median(removed)),
    }


def main() -> None:
    atomic_source = json.loads((RESULTS / "atomic_reentry_phase_map_summary.json").read_text())
    molecular_source = json.loads((RESULTS / "molecular_reentry_phase_map_summary.json").read_text())
    cellular_source = json.loads((RESULTS / "cellular_return_identity_interaction_summary.json").read_text())
    atomic = phase_interactions(
        atomic_source["rows"], ("target", "removal_steps"), lambda row, condition: row["scores"][condition]
    )
    molecular = phase_interactions(
        molecular_source["rows"], ("profile", "temperature", "removal_steps"), lambda row, condition: row["similarities_to_matched_intact"][condition]
    )
    cellular = []
    for item in cellular_source["interactions"]:
        fractions = item["headroom_normalized_recovery"]
        cellular.append({
            "group": [item["damage_amplitude"], item["reinjection_minutes"]],
            "headroom_normalized_recovery": fractions,
            "correct_minus_mismatch_interaction": fractions["correct_return"] - fractions["mismatched_return"],
            "correct_minus_removed_interaction": fractions["correct_return"] - fractions["removed"],
        })
    domains = {"atomic": atomic, "molecular": molecular, "cellular": cellular}
    domain_summaries = {name: summarize(records) for name, records in domains.items()}

    lodo = {}
    for heldout in domains:
        training = [name for name in domains if name != heldout]
        inferred = all(
            domain_summaries[name]["all_correct_exceeds_mismatch"]
            and domain_summaries[name]["all_correct_exceeds_removed"]
            for name in training
        )
        heldout_pass = (
            domain_summaries[heldout]["all_correct_exceeds_mismatch"]
            and domain_summaries[heldout]["all_correct_exceeds_removed"]
        )
        lodo[heldout] = {
            "training_domains": training,
            "training_infers_positive_return_identity_interaction": inferred,
            "heldout_all_groups_pass": heldout_pass,
            "pass": inferred and heldout_pass,
        }

    all_records = [(domain, item) for domain, records in domains.items() for item in records]
    observed = float(np.mean([item["correct_minus_mismatch_interaction"] for _, item in all_records]))
    rng = np.random.default_rng(2026185001)
    null = np.empty(NULL_REPLICATES, dtype=float)
    interactions = np.asarray([item["correct_minus_mismatch_interaction"] for _, item in all_records])
    for replicate in range(NULL_REPLICATES):
        # Swapping correct and mismatch labels reverses the interaction sign
        # while preserving every group magnitude and domain composition.
        signs = rng.choice((-1.0, 1.0), size=len(interactions))
        null[replicate] = float(np.mean(signs * interactions))
    exceedances = int(np.sum(null >= observed - 1e-15))
    p_value = float((exceedances + 1) / (NULL_REPLICATES + 1))

    summary = {
        "schema": "siel-e014-cross-domain-return-identity-interaction-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "hypothesis": "additional recovery opportunity preferentially closes the remaining domain-native recovery gap when the returned O3 relation is correct rather than removed or physically mismatched",
        "domain_summaries": domain_summaries,
        "leave_one_domain_out": lodo,
        "all_lodo_pass": all(item["pass"] for item in lodo.values()),
        "total_groups": len(all_records),
        "all_groups_correct_exceeds_mismatch": all(item["correct_minus_mismatch_interaction"] > 0.0 for _, item in all_records),
        "all_groups_correct_exceeds_removed": all(item["correct_minus_removed_interaction"] > 0.0 for _, item in all_records),
        "condition_label_sign_flip_null": {
            "observed_mean_correct_minus_mismatch_interaction": observed,
            "replicates": NULL_REPLICATES,
            "exceedances": exceedances,
            "conservative_monte_carlo_p": p_value,
            "null_mean": float(np.mean(null)),
            "null_standard_deviation": float(np.std(null, ddof=1)),
        },
        "records": domains,
        "compression_boundary": {
            "shared_quantity_entering_domain_engines": False,
            "interaction_computed_only_after_domain_native_dynamics": True,
            "common_source_identity_inferred": False,
            "common_scalar_law_inferred": False,
            "transferred_object": "direction of the return-identity by recovery-opportunity interaction",
        },
        "scope": {
            "not_confirmatory": True,
            "headroom_normalization_selected_after_raw_gain ceiling effects": True,
            "current targets previously inspected": True,
            "prospective confirmation_requires_new_heldout_targets": True,
        },
    }
    (RESULTS / "cross_domain_return_identity_interaction_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Cross-domain O3 return-identity interaction exploration",
        "",
        f"All groups correct > mismatch interaction: `{summary['all_groups_correct_exceeds_mismatch']}` (`{len(all_records)}/{len(all_records)}`).",
        f"All groups correct > removed interaction: `{summary['all_groups_correct_exceeds_removed']}`.",
        f"All leave-one-domain-out transfers pass: `{summary['all_lodo_pass']}`.",
        f"Condition-label sign-flip null: `{exceedances}/{NULL_REPLICATES}` exceedances; conservative p `{p_value:.9f}`.",
        "",
        "The transferred object is the direction of an identity-by-time causal interaction, not a common scalar mediator or source-level substance.",
        "This is result-informed local exploration and requires new held-out targets for prospective confirmation.",
    ]
    (RESULTS / "CROSS_DOMAIN_RETURN_IDENTITY_INTERACTION_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "domain_summaries": domain_summaries,
        "all_lodo_pass": summary["all_lodo_pass"],
        "total_groups": len(all_records),
        "all_correct_gt_mismatch": summary["all_groups_correct_exceeds_mismatch"],
        "all_correct_gt_removed": summary["all_groups_correct_exceeds_removed"],
        "null_exceedances": exceedances,
        "null_p": p_value,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
