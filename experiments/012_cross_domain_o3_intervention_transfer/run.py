#!/usr/bin/env python3
"""Frozen runner for Experiment 012 cross-domain O3 intervention transfer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"
REGISTRY = ROOT / "target_registry.json"
CONDITIONS = ("intact", "removed", "mismatched_return", "correct_return")


class ProvenanceError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_registration() -> tuple[dict, dict]:
    manifest = load_json(MANIFEST)
    registry = load_json(REGISTRY)
    if manifest.get("schema") != "siel-experiment-012-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_execution_performed") is not False:
        raise ProvenanceError("registration declares target execution")
    if registry.get("schema") != "siel-e012-target-registry-v1":
        raise ProvenanceError("target registry schema mismatch")
    if registry.get("target_execution_performed") is not False:
        raise ProvenanceError("target registry declares target execution")
    for relative, expected in sorted(manifest["source_sha256"].items()):
        path = REPO_ROOT / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ProvenanceError(f"registered source hash mismatch: {relative}")
    return manifest, registry


def validate_receipt(path: Path) -> dict:
    receipt = load_json(path)
    if set(receipt) != {"schema", "tag", "commit", "release_url", "doi"}:
        raise ProvenanceError("registration receipt fields mismatch")
    if receipt["schema"] != "siel-e012-registration-receipt-v1":
        raise ProvenanceError("registration receipt schema mismatch")
    if receipt["tag"] != "e012-preregistration-v1.0.0":
        raise ProvenanceError("registration receipt tag mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", receipt["commit"]):
        raise ProvenanceError("registration commit is not a full SHA")
    if not receipt["release_url"].endswith(
        "/releases/tag/e012-preregistration-v1.0.0"
    ):
        raise ProvenanceError("registration release URL mismatch")
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", receipt["doi"]):
        raise ProvenanceError("registration DOI mismatch")
    return receipt


def load_cell_core():
    path = REPO_ROOT / "experiments/009_constitutive_cell_o3_closure/core.py"
    spec = importlib.util.spec_from_file_location("e009_core_for_e012_confirm", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load E009 core")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def atomic_engine(config: dict) -> dict:
    n_grid = int(config["grid_points"])
    half_width = float(config["half_width"])
    dx = 2.0 * half_width / n_grid
    x = np.linspace(-half_width, half_width - dx, n_grid)
    k = 2.0 * np.pi * np.fft.fftfreq(n_grid, d=dx)
    softening = float(config["softening"])
    original = -1.0 / np.sqrt(x * x + softening * softening)
    shifted = -1.0 / np.sqrt(
        (x - float(config["mismatched_shift"])) ** 2 + softening * softening
    )
    zero = np.zeros_like(x)

    def step(psi, potential, reduced_mass, damping):
        dt = 0.02
        complex_time = damping + 1j
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        kinetic = k * k / (2.0 * reduced_mass)
        psi = np.fft.ifft(
            np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi)
        )
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))

    records = {}
    for name, target in config["targets"].items():
        ratio = float(target["nuclear_electron_mass_ratio"])
        reduced_mass = ratio / (ratio + 1.0)
        ground = np.exp(-x * x / 2.0).astype(complex)
        ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
        for _ in range(int(config["ground_steps"])):
            ground = step(ground, original, reduced_mass, 0.50)
        scores = {}
        diagnostics = {}
        for condition in CONDITIONS:
            psi = ground.copy()
            for index in range(int(config["dynamic_steps"])):
                if condition == "intact":
                    potential = original
                elif condition == "removed":
                    potential = zero
                elif index < int(config["removal_steps_before_return"]):
                    potential = zero
                elif condition == "correct_return":
                    potential = original
                else:
                    potential = shifted
                psi = step(psi, potential, reduced_mass, 0.08)
            mask = np.abs(x) < float(config["local_window"])
            score = float(np.sum(np.abs(psi[mask]) ** 2) * dx)
            scores[condition] = score
            diagnostics[condition] = {
                "whole_score": score,
                "ground_fidelity": float(abs(np.vdot(ground, psi) * dx) ** 2),
            }
        records[name] = {
            "reduced_mass_electron_units": reduced_mass,
            "scores": scores,
            "diagnostics": diagnostics,
        }
    return {"engine": "atomic_open_quantum_relaxation", "targets": records}


def load_surfaces() -> dict:
    path = REPO_ROOT / (
        "experiments/010_complete_molecular_carrier_transfer/"
        "results/shape_surfaces.csv"
    )
    surfaces = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["basis"], row["mode"])
            point = (
                round(float(row["a_angstrom"]), 1),
                round(float(row["b_angstrom"]), 1),
            )
            surfaces.setdefault(key, {})[point] = float(row["energy_hartree"])
    return surfaces


def molecular_engine(config: dict) -> dict:
    surfaces = load_surfaces()
    temperature = float(config["temperature_hartree"])

    def metropolis(surface, point, rng):
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

    records = {}
    for basis in config["basis_profiles"]:
        full = surfaces[(basis, "full")]
        deleted = surfaces[(basis, "one_electron_cross_deleted")]
        edge = surfaces[(basis, "without_edge_01")]
        minimum = min(full.values())
        minima = [p for p, energy in full.items() if abs(energy - minimum) <= 1e-10]
        start = max(minima, key=lambda p: p[0])
        basis_records = {}
        for condition in CONDITIONS:
            seed_scores = []
            final_points = []
            for seed in config["trajectory_seeds"]:
                rng = np.random.default_rng(int(seed))
                point = start
                trajectory = []
                for index in range(int(config["total_steps"])):
                    if condition == "intact":
                        surface = full
                    elif condition == "removed":
                        surface = deleted
                    elif index < int(config["removal_steps_before_return"]):
                        surface = deleted
                    elif condition == "correct_return":
                        surface = full
                    else:
                        surface = edge
                    point = metropolis(surface, point, rng)
                    trajectory.append(point)
                late = trajectory[-int(config["late_window_steps"]):]
                radius = float(config["minimum_radius_angstrom"])
                score = float(np.mean([
                    min(math.dist(p, m) for m in minima) <= radius for p in late
                ]))
                seed_scores.append(score)
                final_points.append(point)
            basis_records[condition] = {
                "whole_score": float(np.mean(seed_scores)),
                "seed_scores": seed_scores,
                "final_points": final_points,
            }
        records[basis] = basis_records
    return {"engine": "molecular_seeded_metropolis_on_e010_fci_surfaces", "bases": records}


def cellular_engine(config: dict) -> dict:
    core = load_cell_core()
    dynamics = core.DynamicsConfig()
    mapping = {
        "intact": "native",
        "removed": "joint_erased",
        "mismatched_return": "time_shifted",
        "correct_return": "reinjected",
    }
    cohorts = {}
    count = int(config["lineages_per_cohort"])
    for number, start in enumerate(config["cohort_starts"], 1):
        scores = {}
        details = {}
        for condition, cell_condition in mapping.items():
            lineages = [
                core.simulate(seed, dynamics, cell_condition)
                for seed in range(int(start), int(start) + count)
            ]
            score = float(np.mean([item["alive"] for item in lineages]))
            scores[condition] = score
            details[condition] = {
                "whole_score": score,
                "alive_count": int(sum(item["alive"] for item in lineages)),
                "count": count,
            }
        cohorts[f"cohort_{number}"] = {
            "seed_range": [int(start), int(start) + count - 1],
            "scores": scores,
            "details": details,
        }
    return {"engine": "cellular_e009_new_seed_cohorts", "cohorts": cohorts}


def realization_scores(domains: dict) -> dict:
    return {
        "atomic": {
            name: record["scores"] for name, record in domains["atomic"]["targets"].items()
        },
        "molecular": {
            basis: {c: record[c]["whole_score"] for c in CONDITIONS}
            for basis, record in domains["molecular"]["bases"].items()
        },
        "cellular": {
            name: record["scores"] for name, record in domains["cellular"]["cohorts"].items()
        },
    }


def gates(scores: dict, thresholds: dict) -> dict:
    return {
        "intact_high": scores["intact"] >= thresholds["high_minimum"],
        "removed_low": scores["removed"] <= thresholds["low_maximum"],
        "mismatched_low": scores["mismatched_return"] <= thresholds["low_maximum"],
        "correct_high": scores["correct_return"] >= thresholds["high_minimum"],
        "specific_return": scores["correct_return"] >= max(
            scores["removed"], scores["mismatched_return"]
        ) + thresholds["specific_return_advantage_minimum"],
    }


def evaluate(registry: dict, receipt: dict) -> dict:
    domains = {
        "atomic": atomic_engine(registry["atomic"]),
        "molecular": molecular_engine(registry["molecular"]),
        "cellular": cellular_engine(registry["cellular"]),
    }
    scores = realization_scores(domains)
    gate_records = {
        domain: {name: gates(value, registry["thresholds"]) for name, value in records.items()}
        for domain, records in scores.items()
    }
    passes = {
        domain: {name: all(value.values()) for name, value in records.items()}
        for domain, records in gate_records.items()
    }
    flattened = [value for records in scores.values() for value in records.values()]
    minimum_high = min(min(s["intact"], s["correct_return"]) for s in flattened)
    maximum_low = max(max(s["removed"], s["mismatched_return"]) for s in flattened)
    margin = minimum_high - maximum_low
    domain_pass = {
        domain: all(records.values()) for domain, records in passes.items()
    }
    supported = all(domain_pass.values()) and margin > float(
        registry["thresholds"]["threshold_free_margin_minimum"]
    )
    return {
        "schema": "siel-e012-result-v1",
        "decision": (
            "CROSS_DOMAIN_O3_INTERVENTION_TRANSFER_SUPPORTED"
            if supported else "CROSS_DOMAIN_O3_INTERVENTION_TRANSFER_NOT_SUPPORTED"
        ),
        "registration_receipt": receipt,
        "domains": domains,
        "realization_scores": scores,
        "gates": gate_records,
        "realization_pass": passes,
        "domain_pass": domain_pass,
        "threshold_free_separation": {
            "minimum_intact_or_correct": minimum_high,
            "maximum_removed_or_mismatched": maximum_low,
            "margin": margin,
            "pass": margin > 0.0,
        },
        "no_shared_scalar_entered_domain_dynamics": True,
        "leave_one_domain_out": dict(domain_pass),
        "scope": {
            "supported_if_positive": "shared O3 causal intervention topology across three independently executed reduced domain models",
            "not_established": [
                "common O3 substance",
                "microscopic atom-to-cell law",
                "laboratory confirmation in living cells",
            ],
        },
    }


def write_results(output: Path, summary: dict):
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with (output / "domain_scores.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("domain", "realization", "condition", "whole_score"))
        for domain, records in summary["realization_scores"].items():
            for name, scores in records.items():
                for condition in CONDITIONS:
                    writer.writerow((domain, name, condition, scores[condition]))
    separation = summary["threshold_free_separation"]
    lines = [
        "# Experiment 012 result",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        f"Threshold-free separation margin: `{separation['margin']:.9f}`.",
        "",
        "All supported, mixed, and unsupported outputs are retained in `summary.json`.",
    ]
    (output / "RESULT.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--registration-receipt", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    _, registry = verify_registration()
    if args.validate_registration:
        if args.registration_receipt is not None:
            raise ProvenanceError("validation refuses a receipt")
        print("REGISTRATION_VALID_TARGETS_NOT_EXECUTED")
        return
    if args.registration_receipt is None:
        raise ProvenanceError("execution requires a registration receipt")
    receipt = validate_receipt(args.registration_receipt)
    summary = evaluate(registry, receipt)
    write_results(args.output, summary)
    print(summary["decision"])


if __name__ == "__main__":
    main()
