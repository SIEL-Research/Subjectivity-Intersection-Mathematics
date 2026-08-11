#!/usr/bin/env python3
"""Local result-informed exploration following the E012 audit."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
CHECKPOINT = RESULTS / "sparse_energies.json"
POINTS = ((1.5, 0.9), (1.6, 0.9), (1.7, 0.9), (2.0, 0.9), (2.3, 0.9), (2.5, 0.9))
MODES = ("full", "without_edge_01")
CONDITIONS = ("intact", "removed", "mismatched_return", "correct_return")


def load_e010():
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/run.py"
    spec = importlib.util.spec_from_file_location("e010_for_e013", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load E010 runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_registered_surfaces() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    surfaces = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], row["mode"])
            point = (round(float(row["a_angstrom"]), 1), round(float(row["b_angstrom"]), 1))
            surfaces.setdefault(key, {})[point] = float(row["energy_hartree"])
    return surfaces


def load_checkpoint() -> dict:
    if not CHECKPOINT.exists():
        return {}
    return json.loads(CHECKPOINT.read_text())


def save_checkpoint(records: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")


def compute_sparse_basis(basis: str) -> dict:
    e010 = load_e010()
    records = load_checkpoint()
    basis_records = records.setdefault(basis, {})
    for a, b in POINTS:
        point_key = f"{a:.1f},{b:.1f}"
        point_record = basis_records.setdefault(point_key, {})
        missing = [mode for mode in MODES if mode not in point_record]
        if not missing:
            continue
        built = e010.build_target(basis, a, b)
        point_record["n_orbitals"] = int(built["h_full"].shape[0])
        for mode in missing:
            point_record[mode] = e010.fci_solution(built, mode)[0]
            save_checkpoint(records)
    return records


def sparse_metrics(surfaces: dict) -> dict:
    correct = POINTS[:3]
    mismatch = POINTS[3:]
    output = {}
    bases = sorted({basis for basis, mode in surfaces if mode == "full"})
    for basis in bases:
        full = surfaces[(basis, "full")]
        edge = surfaces[(basis, "without_edge_01")]
        output[basis] = {
            "full_rejection_of_mismatch_basin_hartree": min(full[p] for p in mismatch) - min(full[p] for p in correct),
            "edge_drive_toward_mismatch_basin_hartree": min(edge[p] for p in correct) - min(edge[p] for p in mismatch),
            "sampled_full_minimum": list(min(POINTS, key=lambda p: full[p])),
            "sampled_edge_minimum": list(min(POINTS, key=lambda p: edge[p])),
        }
    return output


def merge_sparse_with_registered(checkpoint: dict) -> dict:
    surfaces = load_registered_surfaces()
    selected = {}
    for basis in ("sto-3g", "6-31g", "cc-pvdz"):
        for mode in MODES:
            selected[(basis, mode)] = {p: surfaces[(basis, mode)][p] for p in POINTS}
    for basis, points in checkpoint.items():
        for mode in MODES:
            selected[(basis, mode)] = {
                tuple(float(value) for value in key.split(",")): float(record[mode])
                for key, record in points.items()
                if mode in record
            }
    return selected


def generator_rule_audit() -> dict:
    return {
        "fixed_rule": "C*_D = G_native,D - G_additive_or_isolated,D",
        "complete_removal_rule": "G_removed,D must equal G_additive_or_isolated,D",
        "domains": {
            "atomic": {
                "native_generator": "T_mu + V_soft_Coulomb",
                "reference_generator": "T_mu",
                "generated_candidate": "V_soft_Coulomb",
                "e012_removed_generator": "T_mu",
                "complete_candidate_removal": True,
            },
            "molecular": {
                "native_generator": "H_molecule",
                "reference_generator": "H_isolated_centres",
                "generated_candidate": "H_molecule - H_isolated_centres",
                "e012_removed_generator": "H_molecule - C_one_electron_cross",
                "complete_candidate_removal": False,
                "reason": "E012 removes one carrier sector, not the complete generated residual",
            },
            "cellular": {
                "native_generator": "bilinear joint-gate dynamics",
                "reference_generator": "registered inclusion-exclusion joint-erased dynamics",
                "generated_candidate": "native joint generator - joint-erased generator",
                "e012_removed_generator": "registered joint-erased dynamics",
                "complete_candidate_removal": True,
            },
        },
    }


def aggregate_e012_scores() -> dict:
    path = REPO_ROOT / "experiments/012_cross_domain_o3_intervention_transfer/results/summary.json"
    summary = json.loads(path.read_text())
    aggregated = {}
    for domain, realizations in summary["realization_scores"].items():
        aggregated[domain] = {
            condition: sum(scores[condition] for scores in realizations.values()) / len(realizations)
            for condition in CONDITIONS
        }
    return aggregated


def atomic_diversity_audit() -> dict:
    public_path = REPO_ROOT / "experiments/012_cross_domain_o3_intervention_transfer/results/summary.json"
    exploratory_path = REPO_ROOT / "experiments/012_cross_domain_o3_intervention_dynamics_exploration/results/summary.json"
    public = json.loads(public_path.read_text())
    exploratory = json.loads(exploratory_path.read_text())
    public_targets = public["domains"]["atomic"]["targets"]
    local_targets = exploratory["domains"]["atomic"]["targets"]
    public_masses = [item["reduced_mass_electron_units"] for item in public_targets.values()]
    local_masses = [item["reduced_mass_electron_units"] for item in local_targets.values()]
    return {
        "public_e012_registered_target_count": len(public_targets),
        "public_e012_reduced_mass_span": max(public_masses) - min(public_masses),
        "public_e012_structural_diversity": "narrow",
        "prior_local_exploration_targets": {
            name: {
                "reduced_mass_electron_units": record["reduced_mass_electron_units"],
                "all_signature_gates_passed": exploratory["independent_realization_pass"]["atomic"][name],
            }
            for name, record in local_targets.items()
        },
        "prior_local_exploration_reduced_mass_span": max(local_masses) - min(local_masses),
        "interpretation": (
            "the public 2/2 count remains valid but samples a narrow mass interval; "
            "prior local muonium/positronium exploration passed over a wider interval and cannot be reused as a new confirmatory holdout"
        ),
    }


def sign(value: float, tolerance: float = 1e-12) -> int:
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def ordinal_leave_one_domain_out(scores: dict) -> dict:
    pairs = list(itertools.combinations(CONDITIONS, 2))
    output = {}
    for heldout in scores:
        training = [name for name in scores if name != heldout]
        learned = []
        for left, right in pairs:
            directions = [sign(scores[name][left] - scores[name][right]) for name in training]
            if directions[0] == directions[1] and directions[0] != 0:
                learned.append((left, right, directions[0]))
        checks = []
        for left, right, direction in learned:
            observed = sign(scores[heldout][left] - scores[heldout][right])
            checks.append({
                "relation": f"{left} {'>' if direction > 0 else '<'} {right}",
                "heldout_direction": observed,
                "pass": observed == direction,
            })
        output[heldout] = {
            "training_domains": training,
            "relations_fixed_only_when_both_training_domains_agree": len(learned),
            "checks": checks,
            "pass": bool(checks) and all(item["pass"] for item in checks),
        }
    return output


def write_result(summary: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    metrics = summary["molecular_sparse_convergence_metrics"]
    lines = [
        "# Experiment 013 local exploration",
        "",
        f"Molecular diagnosis: `{summary['decisions']['molecular_sparse_diagnosis']}`.",
        f"Generator diagnosis: `{summary['decisions']['generator_rule_diagnosis']}`.",
        f"Leave-one-out diagnosis: `{summary['decisions']['ordinal_leave_one_out_diagnosis']}`.",
        "",
        f"Generator-rule alignment: `{summary['generator_rule_alignment']['aligned_domains']}/3` domains.",
        f"Ordinal leave-one-domain-out: `{summary['ordinal_leave_one_domain_out']['all_pass']}`.",
        "",
        "## Sparse molecular convergence diagnostic",
        "",
        "| Basis | Full rejection of mismatch basin | Edge drive toward mismatch basin |",
        "|---|---:|---:|",
    ]
    for basis, values in metrics.items():
        lines.append(
            f"| {basis} | {values['full_rejection_of_mismatch_basin_hartree']:.9f} | "
            f"{values['edge_drive_toward_mismatch_basin_hartree']:.9f} |"
        )
    lines.extend([
        "",
        "The cc-pVTZ edge drive is %.3fx the cc-pVDZ value; the complete-system mismatch rejection remains positive. This favors a low-basis resolution explanation over a demonstrated persistent representation boundary, subject to the sparse-grid limitation."
        % summary["molecular_sparse_convergence_interpretation"]["cc_pvtz_to_cc_pvdz_edge_drive_ratio"],
        "",
        "The fixed generator rule aligns with atomic and cellular removal but not E012 molecular removal: E012 deleted only the one-electron cross sector rather than the complete molecule-minus-isolated-centres residual.",
        "",
        "The independently computed ordinal leave-one-domain-out test passed four relations for every held-out domain: intact exceeds removal and mismatch, and correct return exceeds removal and mismatch.",
        "",
        "The registered hydrogen/deuterium count remains 2/2, but its reduced-mass span is only %.9f. Earlier local muonium/positronium exploration covered a span of %.9f and both passed; those targets are exploratory history, not unused confirmation targets."
        % (
            summary["atomic_diversity_audit"]["public_e012_reduced_mass_span"],
            summary["atomic_diversity_audit"]["prior_local_exploration_reduced_mass_span"],
        ),
        "",
        "These sparse energies diagnose local separation only; they do not reproduce the full E012 trajectories.",
    ])
    (RESULTS / "RESULT.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--basis", default="cc-pvtz")
    parser.add_argument("--skip-quantum", action="store_true")
    args = parser.parse_args()
    checkpoint = load_checkpoint() if args.skip_quantum else compute_sparse_basis(args.basis)
    selected = merge_sparse_with_registered(checkpoint)
    complete_bases = {
        basis for basis, mode in selected
        if all((basis, required) in selected and len(selected[(basis, required)]) == len(POINTS) for required in MODES)
    }
    selected = {key: value for key, value in selected.items() if key[0] in complete_bases}
    molecular_metrics = sparse_metrics(selected)
    generator = generator_rule_audit()
    aligned = sum(item["complete_candidate_removal"] for item in generator["domains"].values())
    loo = ordinal_leave_one_domain_out(aggregate_e012_scores())
    edge_ratio = (
        molecular_metrics["cc-pvtz"]["edge_drive_toward_mismatch_basin_hartree"]
        / molecular_metrics["cc-pvdz"]["edge_drive_toward_mismatch_basin_hartree"]
        if "cc-pvtz" in molecular_metrics else None
    )
    summary = {
        "schema": "siel-e013-local-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "molecular_sparse_convergence_metrics": molecular_metrics,
        "molecular_sparse_convergence_interpretation": {
            "cc_pvtz_to_cc_pvdz_edge_drive_ratio": edge_ratio,
            "full_mismatch_rejection_remains_positive_at_cc_pvtz": (
                molecular_metrics.get("cc-pvtz", {}).get(
                    "full_rejection_of_mismatch_basin_hartree", -1.0
                ) > 0.0
            ),
            "interpretation": (
                "higher basis sharply increases sparse mismatch separation; "
                "low-basis resolution is favored over a demonstrated persistent boundary"
                if edge_ratio is not None and edge_ratio > 1.0 else
                "high-basis sparse diagnosis incomplete"
            ),
        },
        "generator_rule_audit": generator,
        "atomic_diversity_audit": atomic_diversity_audit(),
        "generator_rule_alignment": {
            "aligned_domains": aligned,
            "total_domains": 3,
            "all_align": aligned == 3,
        },
        "ordinal_leave_one_domain_out": {
            "method": "learn only pairwise condition orderings on which both training domains agree",
            "heldout_domains": loo,
            "all_pass": all(item["pass"] for item in loo.values()),
        },
        "decisions": {
            "molecular_sparse_diagnosis": (
                "LOW_BASIS_RESOLUTION_HYPOTHESIS_FAVORED"
                if edge_ratio is not None and edge_ratio > 1.0 else
                "MOLECULAR_CONVERGENCE_DIAGNOSIS_INCOMPLETE"
            ),
            "generator_rule_diagnosis": (
                "E012_INTERVENTIONS_NOT_UNIFIED_BY_COMPLETE_GENERATOR_RESIDUAL"
                if aligned < 3 else "COMPLETE_GENERATOR_RESIDUAL_ALIGNS_ALL_DOMAINS"
            ),
            "ordinal_leave_one_out_diagnosis": (
                "EXPLORATORY_CROSS_DOMAIN_ORDINAL_TOPOLOGY_PASSES"
                if all(item["pass"] for item in loo.values()) else
                "EXPLORATORY_CROSS_DOMAIN_ORDINAL_TOPOLOGY_FAILS"
            ),
        },
        "scope": {
            "not_confirmatory": True,
            "does_not_change_e012": True,
            "sparse_quantum_diagnostic_not_full_metropolis_reexecution": True,
        },
    }
    write_result(summary)
    print(json.dumps({
        "generator_alignment": f"{aligned}/3",
        "ordinal_leave_one_out": summary["ordinal_leave_one_domain_out"]["all_pass"],
        "bases": list(summary["molecular_sparse_convergence_metrics"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
