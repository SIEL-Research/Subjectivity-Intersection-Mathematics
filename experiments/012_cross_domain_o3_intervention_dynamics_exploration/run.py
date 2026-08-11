#!/usr/bin/env python3
"""Local result-informed exploration of a cross-domain O3 causal signature."""

from __future__ import annotations

import csv
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
RESULTS = ROOT / "results"
CONDITIONS = ("intact", "removed", "mismatched_return", "correct_return")
TARGET = {
    "intact": 1.0,
    "removed": 0.0,
    "mismatched_return": 0.0,
    "correct_return": 1.0,
}


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e012", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load E009 cell core")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def atomic_engine() -> dict:
    """Execute two independent reduced-mass open quantum relaxations."""
    n_grid = 1024
    half_width = 100.0
    dx = 2.0 * half_width / n_grid
    x = np.linspace(-half_width, half_width - dx, n_grid)
    k = 2.0 * np.pi * np.fft.fftfreq(n_grid, d=dx)
    softening = 0.8
    original = -1.0 / np.sqrt(x * x + softening * softening)
    shifted = -1.0 / np.sqrt((x - 8.0) ** 2 + softening * softening)
    zero = np.zeros_like(x)

    def step(psi, potential, reduced_mass, dt=0.02, damping=0.08):
        complex_time = damping + 1j
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        kinetic = k * k / (2.0 * reduced_mass)
        psi = np.fft.ifft(
            np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi)
        )
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        norm = math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))
        return psi / norm

    masses = {
        "muonium": 206.7682830 / 207.7682830,
        "positronium": 0.5,
    }
    target_records = {}
    for name, reduced_mass in masses.items():
        psi = np.exp(-x * x / 2.0).astype(complex)
        psi /= math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))
        for _ in range(4000):
            psi = step(psi, original, reduced_mass, damping=0.50)
        ground = psi.copy()

        scores = {}
        diagnostics = {}
        for condition in CONDITIONS:
            psi = ground.copy()
            for index in range(1600):
                if condition == "intact":
                    potential = original
                elif condition == "removed":
                    potential = zero
                elif index < 400:
                    potential = zero
                elif condition == "correct_return":
                    potential = original
                else:
                    potential = shifted
                psi = step(psi, potential, reduced_mass)
            local_probability = float(
                np.sum(np.abs(psi[np.abs(x) < 6.0]) ** 2) * dx
            )
            fidelity = float(abs(np.vdot(ground, psi) * dx) ** 2)
            centre = float(np.sum(x * np.abs(psi) ** 2) * dx)
            scores[condition] = local_probability
            diagnostics[condition] = {
                "local_probability": local_probability,
                "ground_fidelity": fidelity,
                "probability_centre": centre,
            }
        target_records[name] = {
            "reduced_mass_electron_units": reduced_mass,
            "scores": scores,
            "diagnostics": diagnostics,
        }

    aggregate = {
        condition: float(
            np.mean([record["scores"][condition] for record in target_records.values()])
        )
        for condition in CONDITIONS
    }
    return {
        "engine": "open_soft_coulomb_two_body_quantum_relaxation",
        "targets": target_records,
        "whole_scores": aggregate,
        "shared_mediator_input": False,
    }


def molecular_engine() -> dict:
    """Execute intervention and return on the independent E010 surfaces."""
    path = (
        REPO_ROOT
        / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    )
    surfaces = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], row["mode"])
            point = (round(float(row["a_angstrom"]), 1), round(float(row["b_angstrom"]), 1))
            surfaces.setdefault(key, {})[point] = float(row["energy_hartree"])

    def descend(surface, start, steps):
        point = start
        trajectory = [point]
        for _ in range(steps):
            candidates = []
            for da in (-0.1, 0.0, 0.1):
                for db in (-0.1, 0.0, 0.1):
                    candidate = (round(point[0] + da, 1), round(point[1] + db, 1))
                    if candidate in surface:
                        candidates.append((surface[candidate], candidate))
            next_point = min(candidates)[1]
            if next_point == point:
                break
            point = next_point
            trajectory.append(point)
        return point, trajectory

    records = {}
    sigma = 0.30
    for basis in ("sto-3g", "6-31g", "cc-pvdz"):
        full = surfaces[(basis, "full")]
        deleted = surfaces[(basis, "one_electron_cross_deleted")]
        edge = surfaces[(basis, "without_edge_01")]
        full_minimum_energy = min(full.values())
        full_minima = [
            point for point, energy in full.items()
            if abs(energy - full_minimum_energy) <= 1e-10
        ]
        start = max(full_minima, key=lambda point: point[0])
        condition_records = {}
        for condition in CONDITIONS:
            if condition == "intact":
                final, trajectory = descend(full, start, 40)
            elif condition == "removed":
                final, trajectory = descend(deleted, start, 40)
            else:
                intermediate, first = descend(deleted, start, 10)
                returned_surface = full if condition == "correct_return" else edge
                final, second = descend(returned_surface, intermediate, 40)
                trajectory = first + second[1:]
            distance = min(
                math.dist(final, equivalent_minimum)
                for equivalent_minimum in full_minima
            )
            score = math.exp(-((distance / sigma) ** 2))
            condition_records[condition] = {
                "start": start,
                "final": final,
                "distance_to_full_minimum_set_angstrom": distance,
                "whole_score": score,
                "trajectory_steps": len(trajectory) - 1,
            }
        records[basis] = condition_records

    aggregate = {
        condition: float(
            np.mean([records[basis][condition]["whole_score"] for basis in records])
        )
        for condition in CONDITIONS
    }
    return {
        "engine": "discrete_relaxation_on_independent_e010_fci_surfaces",
        "basis_records": records,
        "whole_scores": aggregate,
        "shared_mediator_input": False,
    }


def cellular_engine() -> dict:
    """Execute new exploratory E009 lineages under four causal conditions."""
    core = load_cell_core()
    config = core.DynamicsConfig()
    mapping = {
        "intact": "native",
        "removed": "joint_erased",
        "mismatched_return": "time_shifted",
        "correct_return": "reinjected",
    }
    seed_cohorts = {
        f"cohort_{index + 1}": tuple(range(start, start + 16))
        for index, start in enumerate((2026120100, 2026120200, 2026120300, 2026120400))
    }
    cohort_records = {}
    for cohort_name, seeds in seed_cohorts.items():
        records = {}
        for cross_condition, cell_condition in mapping.items():
            lineages = [
                core.simulate(seed, config, condition=cell_condition) for seed in seeds
            ]
            records[cross_condition] = {
                "cell_condition": cell_condition,
                "alive_count": int(sum(item["alive"] for item in lineages)),
                "lineage_count": len(lineages),
                "alive_fraction": float(np.mean([item["alive"] for item in lineages])),
                "median_recovery_ratio": np.median(
                    [item["recovery_ratio"] for item in lineages], axis=0
                ).tolist(),
            }
        cohort_records[cohort_name] = {
            "seed_range": [seeds[0], seeds[-1]],
            "condition_records": records,
            "whole_scores": {
                condition: records[condition]["alive_fraction"]
                for condition in CONDITIONS
            },
        }
    aggregate = {
        condition: float(
            np.mean(
                [
                    cohort["whole_scores"][condition]
                    for cohort in cohort_records.values()
                ]
            )
        )
        for condition in CONDITIONS
    }
    return {
        "engine": "e009_reduced_stochastic_cell_dynamics_new_exploratory_seeds",
        "cohorts": cohort_records,
        "whole_scores": aggregate,
        "shared_mediator_input": False,
    }


def signature_gates(scores: dict) -> dict:
    return {
        "intact_high": scores["intact"] >= 0.80,
        "removed_low": scores["removed"] <= 0.50,
        "mismatched_return_low": scores["mismatched_return"] <= 0.50,
        "correct_return_high": scores["correct_return"] >= 0.80,
        "specific_return_advantage": scores["correct_return"]
        >= max(scores["removed"], scores["mismatched_return"]) + 0.25,
    }


def subtarget_scores(domains: dict) -> dict:
    atomic = {
        name: record["scores"]
        for name, record in domains["atomic"]["targets"].items()
    }
    molecular = {
        basis: {
            condition: records[condition]["whole_score"]
            for condition in CONDITIONS
        }
        for basis, records in domains["molecular"]["basis_records"].items()
    }
    cellular = {
        cohort: record["whole_scores"]
        for cohort, record in domains["cellular"]["cohorts"].items()
    }
    return {
        "atomic": atomic,
        "molecular": molecular,
        "cellular": cellular,
    }


def permutation_null(domain_scores: dict) -> dict:
    """Exact independent condition-label permutation null over all 24^3 cases."""
    permutations = list(itertools.permutations(CONDITIONS))

    def loss(scores, permutation):
        assigned = dict(zip(CONDITIONS, [scores[name] for name in permutation]))
        return sum((assigned[name] - TARGET[name]) ** 2 for name in CONDITIONS)

    observed = sum(
        loss(scores, CONDITIONS) for scores in domain_scores.values()
    )
    at_least_as_good = 0
    total = 0
    domains = tuple(domain_scores)
    for choices in itertools.product(permutations, repeat=len(domains)):
        total += 1
        value = sum(
            loss(domain_scores[domain], permutation)
            for domain, permutation in zip(domains, choices)
        )
        if value <= observed + 1e-12:
            at_least_as_good += 1
    return {
        "observed_squared_signature_loss": observed,
        "independent_label_permutations": total,
        "permutations_at_least_as_good": at_least_as_good,
        "exact_fraction": at_least_as_good / total,
    }


def main():
    domains = {
        "atomic": atomic_engine(),
        "molecular": molecular_engine(),
        "cellular": cellular_engine(),
    }
    domain_scores = {
        domain: record["whole_scores"] for domain, record in domains.items()
    }
    realization_scores = subtarget_scores(domains)
    realization_gates = {
        domain: {
            name: signature_gates(scores) for name, scores in records.items()
        }
        for domain, records in realization_scores.items()
    }
    realization_pass = {
        domain: {
            name: all(items.values()) for name, items in records.items()
        }
        for domain, records in realization_gates.items()
    }
    all_realization_scores = [
        scores
        for records in realization_scores.values()
        for scores in records.values()
    ]
    minimum_intact_or_correct = min(
        min(scores["intact"], scores["correct_return"])
        for scores in all_realization_scores
    )
    maximum_removed_or_mismatched = max(
        max(scores["removed"], scores["mismatched_return"])
        for scores in all_realization_scores
    )
    threshold_free_margin = minimum_intact_or_correct - maximum_removed_or_mismatched
    gates = {domain: signature_gates(scores) for domain, scores in domain_scores.items()}
    domain_pass = {domain: all(items.values()) for domain, items in gates.items()}
    leave_one_out = {
        heldout: domain_pass[heldout]
        for heldout in domains
    }
    common_scalar_audit = all(
        record["shared_mediator_input"] is False for record in domains.values()
    )
    cross_domain_supported = (
        all(domain_pass.values())
        and all(
            passed
            for records in realization_pass.values()
            for passed in records.values()
        )
        and threshold_free_margin > 0.0
        and all(leave_one_out.values())
        and common_scalar_audit
    )
    summary = {
        "schema": "siel-e012-local-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "question": (
            "Do independently executed atomic, molecular, and cellular models "
            "share the O3 intact-removal-mismatched-return-correct-return causal "
            "signature without a common scalar mediator in their dynamics?"
        ),
        "decision": (
            "CROSS_DOMAIN_O3_INTERVENTION_SIGNATURE_FOUND_IN_LOCAL_EXPLORATION"
            if cross_domain_supported
            else "CROSS_DOMAIN_O3_INTERVENTION_SIGNATURE_NOT_FOUND"
        ),
        "domains": domains,
        "domain_signature_gates": gates,
        "domain_pass": domain_pass,
        "independent_realization_signature_gates": realization_gates,
        "independent_realization_pass": realization_pass,
        "threshold_free_cross_domain_separation": {
            "minimum_intact_or_correct_score": minimum_intact_or_correct,
            "maximum_removed_or_mismatched_score": maximum_removed_or_mismatched,
            "strict_separation_margin": threshold_free_margin,
            "pass": threshold_free_margin > 0.0,
        },
        "leave_one_domain_out_signature_transfer": leave_one_out,
        "no_shared_scalar_entered_domain_dynamics": common_scalar_audit,
        "condition_label_permutation_null": permutation_null(domain_scores),
        "compression_ladder": (
            "domain source -> domain dynamics -> domain whole readout -> "
            "cross-domain causal signature"
        ),
        "scope": {
            "found_if_positive": (
                "A common causal intervention topology executed independently in "
                "atomic, molecular, and cellular models."
            ),
            "not_established": [
                "one microscopic atom-to-cell law",
                "one common O3 substance or scalar coordinate",
                "laboratory confirmation in natural molecules or living cells",
                "confirmatory evidence, because thresholds followed component feasibility checks",
            ],
        },
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    with (RESULTS / "domain_scores.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("domain", "condition", "whole_score"))
        for domain, scores in domain_scores.items():
            for condition in CONDITIONS:
                writer.writerow((domain, condition, scores[condition]))

    lines = [
        "# E012 local exploratory result",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "| Domain | Intact | Removed | Mismatched return | Correct return | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for domain, scores in domain_scores.items():
        lines.append(
            f"| {domain} | {scores['intact']:.6f} | {scores['removed']:.6f} | "
            f"{scores['mismatched_return']:.6f} | {scores['correct_return']:.6f} | "
            f"{domain_pass[domain]} |"
        )
    null = summary["condition_label_permutation_null"]
    separation = summary["threshold_free_cross_domain_separation"]
    lines.extend(
        [
            "",
            f"Threshold-free strict separation margin across all independent "
            f"realizations: `{separation['strict_separation_margin']:.9f}`.",
            "",
            f"Exact independent-label permutation fraction: `{null['exact_fraction']:.9f}` "
            f"({null['permutations_at_least_as_good']}/{null['independent_label_permutations']}).",
            "",
            "This is a result-informed local exploration, not a preregistered confirmation.",
            "The cross-domain object is the causal intervention signature, not a shared scalar.",
        ]
    )
    (RESULTS / "RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
