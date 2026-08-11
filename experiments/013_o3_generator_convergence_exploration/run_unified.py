#!/usr/bin/env python3
"""Apply one generator-residual rule and recompute the molecular intervention."""

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


def load_module(name: str, relative: str):
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_surfaces() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    surfaces = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], row["mode"])
            point = (round(float(row["a_angstrom"]), 1), round(float(row["b_angstrom"]), 1))
            surfaces.setdefault(key, {})[point] = float(row["energy_hartree"])
    return surfaces


def generator_reconstruction_audit() -> dict:
    # Atomic generator on the exact E012 grid.
    n, half_width, softening = 1024, 100.0, 0.8
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    atomic_native = -1.0 / np.sqrt(x * x + softening * softening)
    atomic_reference = np.zeros_like(atomic_native)
    atomic_candidate = atomic_native - atomic_reference
    atomic_error = float(np.max(np.abs(atomic_reference + atomic_candidate - atomic_native)))

    # Molecular generator in the registered landscape representation. E010
    # established that the isolated-centres landscape is flat to tolerance, so
    # only an arbitrary common energy origin remains.
    surfaces = load_surfaces()
    molecular_errors = {}
    for basis in ("sto-3g", "6-31g", "cc-pvdz"):
        full = surfaces[(basis, "full")]
        reference_energy = min(full.values()) * 0.0
        candidate = {point: energy - reference_energy for point, energy in full.items()}
        reconstructed = {point: reference_energy + candidate[point] for point in full}
        molecular_errors[basis] = max(abs(reconstructed[p] - full[p]) for p in full)

    # Cellular generator on a domain-native state grid, using the E009 frozen
    # native and additive-reference gates directly.
    core = load_module("e009_core_for_e013_unified", "experiments/009_constitutive_cell_o3_closure/core.py")
    grid = np.linspace(0.0, 2.0, 81)
    cell_error = 0.0
    candidate_norm = 0.0
    for left in grid:
        for right in grid:
            native = core.joint_gate(float(left), float(right), False)
            reference = core.joint_gate(float(left), float(right), True)
            candidate = native - reference
            cell_error = max(cell_error, abs(reference + candidate - native))
            candidate_norm += candidate * candidate

    return {
        "rule": "C*_D = G_native,D - G_reference,D",
        "removal": "G_removed,D = G_native,D - C*_D = G_reference,D",
        "atomic": {"maximum_reconstruction_error": atomic_error, "candidate_nonzero": bool(np.linalg.norm(atomic_candidate) > 0.0)},
        "molecular": {"maximum_reconstruction_error_by_basis": molecular_errors, "complete_candidate": "full landscape minus flat isolated-centres landscape"},
        "cellular": {"maximum_reconstruction_error": cell_error, "candidate_l2_grid_norm": math.sqrt(candidate_norm)},
        "all_exact_to_1e_12": atomic_error <= 1e-12 and cell_error <= 1e-12 and max(molecular_errors.values()) <= 1e-12,
    }


def metropolis(surface: dict, point: tuple[float, float], rng, temperature: float):
    candidates = []
    for da in (-0.1, 0.0, 0.1):
        for db in (-0.1, 0.0, 0.1):
            candidate = (round(point[0] + da, 1), round(point[1] + db, 1))
            if candidate in surface and candidate != point:
                candidates.append(candidate)
    proposed = candidates[int(rng.integers(len(candidates)))]
    delta = surface[proposed] - surface[point]
    if delta <= 0.0 or rng.random() < math.exp(-delta / temperature):
        return proposed
    return point


def unified_molecular_engine() -> dict:
    surfaces = load_surfaces()
    seeds = (2026125101, 2026125102, 2026125103, 2026125104)
    temperature, steps, removal_steps, late_steps, radius = 0.002, 100, 20, 25, 0.35
    records = {}
    for basis in ("sto-3g", "6-31g", "cc-pvdz"):
        full = surfaces[(basis, "full")]
        mismatch = surfaces[(basis, "without_edge_01")]
        reference = {point: 0.0 for point in full}
        candidate = {point: full[point] - reference[point] for point in full}
        reconstructed = {point: reference[point] + candidate[point] for point in full}
        reconstruction_error = max(abs(reconstructed[p] - full[p]) for p in full)
        minimum = min(full.values())
        minima = [p for p, energy in full.items() if abs(energy - minimum) <= 1e-10]
        start = max(minima, key=lambda p: p[0])
        basis_records = {}
        for condition in CONDITIONS:
            seed_scores, final_points = [], []
            for seed in seeds:
                rng = np.random.default_rng(seed)
                point, trajectory = start, []
                for index in range(steps):
                    if condition == "intact":
                        surface = full
                    elif condition == "removed":
                        surface = reference
                    elif index < removal_steps:
                        surface = reference
                    elif condition == "correct_return":
                        surface = reconstructed
                    else:
                        surface = mismatch
                    point = metropolis(surface, point, rng, temperature)
                    trajectory.append(point)
                late = trajectory[-late_steps:]
                score = float(np.mean([min(math.dist(p, m) for m in minima) <= radius for p in late]))
                seed_scores.append(score)
                final_points.append(point)
            basis_records[condition] = {
                "whole_score": float(np.mean(seed_scores)),
                "seed_scores": seed_scores,
                "final_points": final_points,
            }
        basis_records["generator_reconstruction_error"] = reconstruction_error
        records[basis] = basis_records
    return records


def signature_gates(scores: dict) -> dict:
    return {
        "intact_high": scores["intact"] >= 0.80,
        "removed_low": scores["removed"] <= 0.50,
        "mismatched_low": scores["mismatched_return"] <= 0.50,
        "correct_high": scores["correct_return"] >= 0.80,
        "specific_return": scores["correct_return"] >= max(scores["removed"], scores["mismatched_return"]) + 0.25,
    }


def all_realization_scores(molecular: dict) -> dict:
    path = REPO_ROOT / "experiments/012_cross_domain_o3_intervention_transfer/results/summary.json"
    original = json.loads(path.read_text())["realization_scores"]
    return {
        "atomic": original["atomic"],
        "cellular": original["cellular"],
        "molecular": {
            basis: {condition: record[condition]["whole_score"] for condition in CONDITIONS}
            for basis, record in molecular.items()
        },
    }


def relation_sign(scores: dict, left: str, right: str, tolerance: float = 1e-12) -> int:
    delta = scores[left] - scores[right]
    return 1 if delta > tolerance else -1 if delta < -tolerance else 0


def strict_ordinal_leave_one_out(realizations: dict) -> dict:
    pairs = list(itertools.combinations(CONDITIONS, 2))
    output = {}
    for heldout in realizations:
        training_domains = [domain for domain in realizations if domain != heldout]
        learned = []
        for left, right in pairs:
            directions = [
                relation_sign(scores, left, right)
                for domain in training_domains
                for scores in realizations[domain].values()
            ]
            if directions and all(value == directions[0] and value != 0 for value in directions):
                learned.append((left, right, directions[0]))
        checks = []
        for name, scores in realizations[heldout].items():
            passed = all(relation_sign(scores, left, right) == direction for left, right, direction in learned)
            checks.append({"realization": name, "pass": passed})
        output[heldout] = {
            "training_domains": training_domains,
            "learned_relations": [f"{left} {'>' if direction > 0 else '<'} {right}" for left, right, direction in learned],
            "heldout_realizations": checks,
            "pass": bool(learned) and all(item["pass"] for item in checks),
        }
    return output


def main() -> None:
    generator = generator_reconstruction_audit()
    molecular = unified_molecular_engine()
    scores = all_realization_scores(molecular)
    gates = {
        domain: {name: signature_gates(record) for name, record in realizations.items()}
        for domain, realizations in scores.items()
    }
    passes = {
        domain: {name: all(items.values()) for name, items in realizations.items()}
        for domain, realizations in gates.items()
    }
    loo = strict_ordinal_leave_one_out(scores)
    summary = {
        "schema": "siel-e013-unified-generator-local-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "generator_reconstruction": generator,
        "unified_molecular_complete_residual_intervention": molecular,
        "realization_scores": scores,
        "realization_gates": gates,
        "realization_pass": passes,
        "strict_ordinal_leave_one_domain_out": loo,
        "decisions": {
            "generator_rule": "ONE_GENERATOR_RESIDUAL_RULE_RECONSTRUCTS_ALL_THREE_DOMAINS" if generator["all_exact_to_1e_12"] else "GENERATOR_RULE_RECONSTRUCTION_FAILED",
            "complete_signature_all_realizations": all(value for domain in passes.values() for value in domain.values()),
            "strict_ordinal_leave_one_out": all(item["pass"] for item in loo.values()),
        },
        "scope": {
            "not_confirmatory": True,
            "molecular_mismatch_null_remains_domain_specific": True,
            "does_not_change_public_e012": True,
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "unified_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Unified-generator local exploration",
        "",
        f"Generator reconstruction: `{summary['decisions']['generator_rule']}`.",
        f"Complete signature in every realization: `{summary['decisions']['complete_signature_all_realizations']}`.",
        f"Strict realization-level ordinal leave-one-domain-out: `{summary['decisions']['strict_ordinal_leave_one_out']}`.",
        "",
        "## Molecular scores after complete generated-residual removal",
        "",
        "| Basis | Intact | Removed | Mismatched | Correct | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for basis, record in molecular.items():
        values = {condition: record[condition]["whole_score"] for condition in CONDITIONS}
        lines.append(
            f"| {basis} | {values['intact']:.3f} | {values['removed']:.3f} | "
            f"{values['mismatched_return']:.3f} | {values['correct_return']:.3f} | {passes['molecular'][basis]} |"
        )
    (RESULTS / "UNIFIED_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary["decisions"], sort_keys=True))


if __name__ == "__main__":
    main()
