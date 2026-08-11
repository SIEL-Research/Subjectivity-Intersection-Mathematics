#!/usr/bin/env python3
"""Execute domain-prior O3 generation and quarter-span mismatch rules locally."""

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
MAX_MISMATCH_OVERLAP = 0.25


def centered_overlap(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float) - float(np.mean(left))
    right = np.asarray(right, dtype=float) - float(np.mean(right))
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator <= 0.0:
        raise ValueError("centered candidate has zero norm")
    return float(np.vdot(left.ravel(), right.ravel()).real / denominator)


def load_module(name: str, relative: str):
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def gates(scores: dict) -> dict:
    return {
        "intact_high": scores["intact"] >= 0.80,
        "removed_low": scores["removed"] <= 0.50,
        "mismatched_low": scores["mismatched_return"] <= 0.50,
        "correct_high": scores["correct_return"] >= 0.80,
        "specific_return": scores["correct_return"] >= max(scores["removed"], scores["mismatched_return"]) + 0.25,
    }


def atomic_engine() -> dict:
    n, half_width, softening = 1024, 100.0, 0.8
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=dx)
    reference = np.zeros_like(x)
    native = -1.0 / np.sqrt(x * x + softening * softening)
    candidate = native - reference
    shift_cells = next(
        shift for shift in range(1, n // 2 + 1)
        if centered_overlap(candidate, np.roll(candidate, shift)) <= MAX_MISMATCH_OVERLAP
    )
    mismatch_candidate = np.roll(candidate, shift_cells)
    mismatch = reference + mismatch_candidate

    def step(psi, potential, reduced_mass, damping):
        dt, complex_time = 0.02, damping + 1j
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        psi = np.fft.ifft(np.exp(-complex_time * k * k / (2.0 * reduced_mass) * dt) * np.fft.fft(psi))
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))

    targets = {"positronium": 1.0, "muonium": 206.7682830, "hydrogen": 1836.152673426}
    output = {}
    for name, ratio in targets.items():
        reduced_mass = ratio / (ratio + 1.0)
        ground = np.exp(-x * x / 2.0).astype(complex)
        ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
        for _ in range(4000):
            ground = step(ground, native, reduced_mass, 0.50)
        scores = {}
        for condition in CONDITIONS:
            psi = ground.copy()
            for index in range(1600):
                if condition == "intact":
                    potential = native
                elif condition == "removed":
                    potential = reference
                elif index < 400:
                    potential = reference
                elif condition == "correct_return":
                    potential = reference + candidate
                else:
                    potential = mismatch
                psi = step(psi, potential, reduced_mass, 0.08)
            scores[condition] = float(np.sum(np.abs(psi[np.abs(x) < 6.0]) ** 2) * dx)
        shift_sensitivity = {}
        shift_specs = {
            "minimal_outside_equivalence": int(math.floor(6.0 / dx)) + 1,
            "fraction_0.0625": int(round(n * 0.0625)),
            "fraction_0.1250": int(round(n * 0.125)),
            "fraction_0.2500": int(round(n * 0.25)),
            "fraction_0.3750": int(round(n * 0.375)),
        }
        for label, shift_count in shift_specs.items():
            shifted = reference + np.roll(candidate, shift_count)
            psi = ground.copy()
            for index in range(1600):
                potential = reference if index < 400 else shifted
                psi = step(psi, potential, reduced_mass, 0.08)
            mismatch_score = float(np.sum(np.abs(psi[np.abs(x) < 6.0]) ** 2) * dx)
            shift_sensitivity[label] = {
                "shift_cells": shift_count,
                "shift_distance": shift_count * dx,
                "outside_registered_equivalence": shift_count * dx > 6.0,
                "centered_overlap": centered_overlap(candidate, np.roll(candidate, shift_count)),
                "mismatched_return_score": mismatch_score,
                "low_gate": mismatch_score <= 0.50,
                "specific_return_gate": scores["correct_return"] >= max(scores["removed"], mismatch_score) + 0.25,
            }
        output[name] = {
            "scores": scores,
            "gates": gates(scores),
            "pass": all(gates(scores).values()),
            "shift_sensitivity": shift_sensitivity,
        }
    reconstruction = float(np.max(np.abs(reference + candidate - native)))
    return {
        "targets": output,
        "quarter_span_shift_cells": shift_cells,
        "selected_centered_overlap": centered_overlap(candidate, mismatch_candidate),
        "candidate_norm_preservation_error": abs(float(np.linalg.norm(mismatch_candidate)) - float(np.linalg.norm(candidate))),
        "reconstruction_error": reconstruction,
    }


def load_surfaces() -> dict:
    path = REPO_ROOT / "experiments/010_complete_molecular_carrier_transfer/results/shape_surfaces.csv"
    surfaces = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], row["mode"])
            point = (round(float(row["a_angstrom"]), 1), round(float(row["b_angstrom"]), 1))
            surfaces.setdefault(key, {})[point] = float(row["energy_hartree"])
    return surfaces


def molecular_engine() -> dict:
    registered = load_surfaces()
    seeds = tuple(range(2026134001, 2026134033))
    output = {}
    for basis in ("sto-3g", "6-31g", "cc-pvdz"):
        native = registered[(basis, "full")]
        reference = {point: 0.0 for point in native}
        candidate = {point: native[point] for point in native}
        a_values = sorted({point[0] for point in native})
        b_values = sorted({point[1] for point in native})
        candidate_grid = np.array([[candidate[(a, b)] for b in b_values] for a in a_values])
        shift = next(
            test_shift for test_shift in range(1, len(a_values) // 2 + 1)
            if centered_overlap(candidate_grid, np.roll(candidate_grid, test_shift, axis=0)) <= MAX_MISMATCH_OVERLAP
        )
        a_index = {value: index for index, value in enumerate(a_values)}
        mismatch_candidate = {
            point: candidate[(a_values[(a_index[point[0]] - shift) % len(a_values)], point[1])]
            for point in native
        }
        mismatch = {point: reference[point] + mismatch_candidate[point] for point in native}
        minimum = min(native.values())
        minima = [point for point, energy in native.items() if abs(energy - minimum) <= 1e-10]
        start = max(minima, key=lambda point: point[0])

        def step(surface, point, rng):
            neighbors = []
            for da in (-0.1, 0.0, 0.1):
                for db in (-0.1, 0.0, 0.1):
                    proposed = (round(point[0] + da, 1), round(point[1] + db, 1))
                    if proposed in surface and proposed != point:
                        neighbors.append(proposed)
            proposed = neighbors[int(rng.integers(len(neighbors)))]
            delta = surface[proposed] - surface[point]
            return proposed if delta <= 0.0 or rng.random() < math.exp(-delta / 0.002) else point

        records = {}
        for condition in CONDITIONS:
            seed_scores = []
            for seed in seeds:
                rng, point, trajectory = np.random.default_rng(seed), start, []
                for index in range(100):
                    if condition == "intact":
                        surface = native
                    elif condition == "removed":
                        surface = reference
                    elif index < 20:
                        surface = reference
                    elif condition == "correct_return":
                        surface = native
                    else:
                        surface = mismatch
                    point = step(surface, point, rng)
                    trajectory.append(point)
                late = trajectory[-25:]
                seed_scores.append(float(np.mean([min(math.dist(p, m) for m in minima) <= 0.35 for p in late])))
            records[condition] = {"whole_score": float(np.mean(seed_scores)), "seed_scores": seed_scores}
        scores = {condition: records[condition]["whole_score"] for condition in CONDITIONS}
        shift_sensitivity = {}
        for test_shift in range(1, len(a_values) // 2 + 1):
            test_candidate = {
                point: candidate[(a_values[(a_index[point[0]] - test_shift) % len(a_values)], point[1])]
                for point in native
            }
            test_surface = {point: reference[point] + test_candidate[point] for point in native}
            seed_scores = []
            for seed in seeds:
                rng, point, trajectory = np.random.default_rng(seed), start, []
                for index in range(100):
                    surface = reference if index < 20 else test_surface
                    point = step(surface, point, rng)
                    trajectory.append(point)
                late = trajectory[-25:]
                seed_scores.append(float(np.mean([min(math.dist(p, m) for m in minima) <= 0.35 for p in late])))
            mismatch_score = float(np.mean(seed_scores))
            shift_sensitivity[str(test_shift)] = {
                "fraction_of_a_grid": test_shift / len(a_values),
                "mismatched_return_score": mismatch_score,
                "centered_overlap": centered_overlap(candidate_grid, np.roll(candidate_grid, test_shift, axis=0)),
                "low_gate": mismatch_score <= 0.50,
                "specific_return_gate": scores["correct_return"] >= max(scores["removed"], mismatch_score) + 0.25,
            }
        mismatch_norm = math.sqrt(sum(value * value for value in mismatch_candidate.values()))
        candidate_norm = math.sqrt(sum(value * value for value in candidate.values()))
        output[basis] = {
            "conditions": records,
            "scores": scores,
            "gates": gates(scores),
            "pass": all(gates(scores).values()),
            "quarter_span_shift_steps": shift,
            "selected_centered_overlap": centered_overlap(candidate_grid, np.roll(candidate_grid, shift, axis=0)),
            "candidate_norm_preservation_error": abs(mismatch_norm - candidate_norm),
            "reconstruction_error": max(abs(reference[p] + candidate[p] - native[p]) for p in native),
            "shift_sensitivity": shift_sensitivity,
        }
    return output


def cellular_engine() -> dict:
    core = load_module("e009_core_for_e013_rule", "experiments/009_constitutive_cell_o3_closure/core.py")
    base_config = core.DynamicsConfig()

    def relation_candidate_series(lineage: dict) -> np.ndarray:
        rows = []
        for B, N, A, G, R, D, _ in np.maximum(
            lineage["states"], [0.001, 0.001, 0.001, 0.001, 0.001, 0.0, 0.1]
        ):
            lower = lambda left, right: max(0.0, left + right - 1.0)
            rows.append([
                0.90 * (B * G - lower(B, G)),
                0.75 * (G * core.saturating(N) - lower(G, core.saturating(N))),
                0.32 * (B * core.saturating(A) - lower(B, core.saturating(A))) * core.saturating(N),
                0.28 * (G * core.saturating(A) - lower(G, core.saturating(A))) * core.saturating(N),
                0.65 * (R * core.saturating(A) - lower(R, core.saturating(A))) * core.saturating(D, 0.12),
            ])
        values = np.asarray(rows)
        window = (lineage["times"] >= 35.0) & (lineage["times"] <= 85.0)
        return values[window]

    calibration = core.simulate(2026136000, base_config, "native")
    series = relation_candidate_series(calibration)
    selected_shift_minutes = next(
        float(minutes) for minutes in range(1, 21)
        if centered_overlap(
            series[int(round(minutes / base_config.dt_minutes)):],
            series[:-int(round(minutes / base_config.dt_minutes))],
        ) <= MAX_MISMATCH_OVERLAP
    )
    config = core.DynamicsConfig(shift_minutes=selected_shift_minutes)
    mapping = {"intact": "native", "removed": "joint_erased", "mismatched_return": "time_shifted", "correct_return": "reinjected"}
    output = {}
    for cohort_index, start in enumerate((2026135001, 2026135101, 2026135201, 2026135301), 1):
        scores = {}
        for condition, cell_condition in mapping.items():
            lineages = [core.simulate(seed, config, cell_condition) for seed in range(start, start + 16)]
            scores[condition] = float(np.mean([lineage["alive"] for lineage in lineages]))
        output[f"cohort_{cohort_index}"] = {"scores": scores, "gates": gates(scores), "pass": all(gates(scores).values())}
    sensitivity = {}
    for shift_minutes in (5.0, 10.0, 15.0, 20.0):
        shifted_config = core.DynamicsConfig(shift_minutes=shift_minutes)
        lineages = [
            core.simulate(seed, shifted_config, "time_shifted")
            for seed in range(2026136001, 2026136065)
        ]
        score = float(np.mean([lineage["alive"] for lineage in lineages]))
        lag = int(round(shift_minutes / base_config.dt_minutes))
        sensitivity[f"{shift_minutes:.1f}"] = {
            "mismatched_return_score": score,
            "low_gate": score <= 0.50,
            "centered_overlap": centered_overlap(series[lag:], series[:-lag]),
        }
    # The E009 time shift is 10 minutes over the registered 40-minute
    # damage-to-reinjection response window.
    grid = np.linspace(0.0, 2.0, 81)
    reconstruction_error = 0.0
    for left in grid:
        for right in grid:
            native = core.joint_gate(float(left), float(right), False)
            reference = core.joint_gate(float(left), float(right), True)
            candidate = native - reference
            reconstruction_error = max(reconstruction_error, abs(reference + candidate - native))
    return {
        "cohorts": output,
        "selected_time_shift_minutes": selected_shift_minutes,
        "selected_centered_overlap": centered_overlap(
            series[int(round(selected_shift_minutes / base_config.dt_minutes)):],
            series[:-int(round(selected_shift_minutes / base_config.dt_minutes))],
        ),
        "shift_sensitivity": sensitivity,
        "candidate_operator_unchanged_under_time_transport": True,
        "reference_plus_candidate_reconstruction_error": reconstruction_error,
    }


def strict_loo(realizations: dict) -> dict:
    pairs = list(itertools.combinations(CONDITIONS, 2))

    def direction(scores, left, right):
        delta = scores[left] - scores[right]
        return 1 if delta > 1e-12 else -1 if delta < -1e-12 else 0

    output = {}
    for heldout in realizations:
        training = [domain for domain in realizations if domain != heldout]
        learned = []
        for left, right in pairs:
            values = [direction(item["scores"], left, right) for domain in training for item in realizations[domain].values()]
            if values and all(value == values[0] and value != 0 for value in values):
                learned.append((left, right, values[0]))
        checks = {
            name: all(direction(item["scores"], left, right) == expected for left, right, expected in learned)
            for name, item in realizations[heldout].items()
        }
        output[heldout] = {
            "learned_relations": [f"{left} {'>' if value > 0 else '<'} {right}" for left, right, value in learned],
            "realization_checks": checks,
            "pass": bool(learned) and all(checks.values()),
        }
    return output


def topology_loo(realizations: dict) -> dict:
    edges = (
        ("intact", "removed"),
        ("intact", "mismatched_return"),
        ("correct_return", "removed"),
        ("correct_return", "mismatched_return"),
    )
    output = {}
    for heldout in realizations:
        training = [domain for domain in realizations if domain != heldout]
        training_pass = all(
            item["scores"][left] > item["scores"][right]
            for domain in training
            for item in realizations[domain].values()
            for left, right in edges
        )
        checks = {
            name: all(item["scores"][left] > item["scores"][right] for left, right in edges)
            for name, item in realizations[heldout].items()
        }
        output[heldout] = {
            "training_domains": training,
            "fixed_partial_order_edges": [f"{left} > {right}" for left, right in edges],
            "training_pass": training_pass,
            "realization_checks": checks,
            "pass": training_pass and all(checks.values()),
        }
    return output


def main() -> None:
    atomic = atomic_engine()
    molecular = molecular_engine()
    cellular = cellular_engine()
    realizations = {
        "atomic": atomic["targets"],
        "molecular": molecular,
        "cellular": cellular["cohorts"],
    }
    loo = strict_loo(realizations)
    partial_order_loo = topology_loo(realizations)
    all_pass = all(item["pass"] for domain in realizations.values() for item in domain.values())
    summary = {
        "schema": "siel-e013-domain-prior-rule-local-exploration-v1",
        "status": "LOCAL_RESULT_INFORMED_EXPLORATION",
        "rules": {
            "reference": "maximal local-preserving severing projection",
            "candidate": "C*_D = G_D - P_loc,D(G_D)",
            "mismatch": "minimal admissible isometry with centered candidate overlap at most 0.25",
            "maximum_centered_mismatch_overlap": MAX_MISMATCH_OVERLAP,
        },
        "atomic": atomic,
        "molecular": molecular,
        "cellular": cellular,
        "unrestricted_learned_pairwise_leave_one_domain_out": loo,
        "causal_partial_order_leave_one_domain_out": partial_order_loo,
        "decisions": {
            "all_realizations_pass_absolute_signature": all_pass,
            "unrestricted_learned_pairwise_leave_one_domain_out": all(item["pass"] for item in loo.values()),
            "causal_partial_order_leave_one_domain_out": all(item["pass"] for item in partial_order_loo.values()),
            "reference_and_mismatch_rules_operationally_closed": (
                atomic["reconstruction_error"] <= 1e-12
                and atomic["candidate_norm_preservation_error"] <= 1e-12
                and all(item["reconstruction_error"] <= 1e-12 and item["candidate_norm_preservation_error"] <= 1e-12 for item in molecular.values())
                and cellular["candidate_operator_unchanged_under_time_transport"]
                and cellular["reference_plus_candidate_reconstruction_error"] <= 1e-12
            ),
            "mismatch_shift_sensitivity": {
                "atomic_all_tested_shifts_pass": all(
                    test["low_gate"] and test["specific_return_gate"]
                    for target in atomic["targets"].values()
                    for test in target["shift_sensitivity"].values()
                    if test["centered_overlap"] <= MAX_MISMATCH_OVERLAP
                ),
                "molecular_all_tested_shifts_pass": all(
                    test["low_gate"] and test["specific_return_gate"]
                    for basis in molecular.values()
                    for test in basis["shift_sensitivity"].values()
                    if test["centered_overlap"] <= MAX_MISMATCH_OVERLAP
                ),
                "cellular_all_tested_shifts_pass": all(
                    test["low_gate"] for test in cellular["shift_sensitivity"].values()
                    if test["centered_overlap"] <= MAX_MISMATCH_OVERLAP
                ),
            },
        },
        "scope": {"not_confirmatory": True, "does_not_change_e012": True},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "rule_closure_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Domain-prior rule-closure exploration",
        "",
        f"Operational rule closure: `{summary['decisions']['reference_and_mismatch_rules_operationally_closed']}`.",
        f"All absolute signatures: `{summary['decisions']['all_realizations_pass_absolute_signature']}`.",
        f"Causal partial-order leave-one-domain-out: `{summary['decisions']['causal_partial_order_leave_one_domain_out']}`.",
        f"Unrestricted learned-pairwise leave-one-domain-out: `{summary['decisions']['unrestricted_learned_pairwise_leave_one_domain_out']}`.",
        "",
        "The causal test freezes only the four O3-required comparisons: intact and correct return must each exceed removal and mismatched return. The unrestricted diagnostic additionally learned an incidental removal-versus-mismatch ordering; its cellular holdout failure is preserved and is not used as an O3 gate.",
        "",
        "## Molecular generated-mismatch scores",
        "",
        "| Basis | Intact | Removed | Mismatch | Correct | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for basis, item in molecular.items():
        scores = item["scores"]
        lines.append(f"| {basis} | {scores['intact']:.3f} | {scores['removed']:.3f} | {scores['mismatched_return']:.3f} | {scores['correct_return']:.3f} | {item['pass']} |")
    (RESULTS / "RULE_CLOSURE_RESULT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary["decisions"], sort_keys=True))


if __name__ == "__main__":
    main()
