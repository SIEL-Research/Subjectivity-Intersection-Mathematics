#!/usr/bin/env python3
"""Frozen runner for Experiment 013 domain-prior O3 generation transfer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
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
CAUSAL_EDGES = (
    ("intact", "removed"),
    ("intact", "mismatched_return"),
    ("correct_return", "removed"),
    ("correct_return", "mismatched_return"),
)


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
    if manifest.get("schema") != "siel-experiment-013-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_execution_performed") is not False:
        raise ProvenanceError("registration declares target execution")
    if registry.get("schema") != "siel-e013-target-registry-v1":
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
    if receipt["schema"] != "siel-e013-registration-receipt-v1":
        raise ProvenanceError("registration receipt schema mismatch")
    if receipt["tag"] != "e013-preregistration-v1.0.0":
        raise ProvenanceError("registration receipt tag mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", receipt["commit"]):
        raise ProvenanceError("registration commit is not a full SHA")
    if not receipt["release_url"].endswith(
        "/releases/tag/e013-preregistration-v1.0.0"
    ):
        raise ProvenanceError("registration release URL mismatch")
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", receipt["doi"]):
        raise ProvenanceError("registration DOI mismatch")
    return receipt


def load_module(name: str, relative: str):
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def centered_overlap(left, right) -> float:
    left = np.asarray(left, dtype=float) - float(np.mean(left))
    right = np.asarray(right, dtype=float) - float(np.mean(right))
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator <= 0.0:
        raise ValueError("centered candidate has zero norm")
    return float(np.vdot(left.ravel(), right.ravel()).real / denominator)


def first_admissible_roll(candidate, axis: int, maximum_overlap: float) -> tuple[int, np.ndarray, float]:
    array = np.asarray(candidate, dtype=float)
    span = array.shape[axis]
    for shift in range(1, span // 2 + 1):
        shifted = np.roll(array, shift, axis=axis)
        overlap = centered_overlap(array, shifted)
        if overlap <= maximum_overlap:
            return shift, shifted, overlap
    raise RuntimeError("no admissible mismatch isometry")


def atomic_engine(config: dict, maximum_overlap: float) -> dict:
    n = int(config["grid_points"])
    half_width = float(config["half_width"])
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=dx)
    reference = np.zeros_like(x)

    def step(psi, potential, reduced_mass, damping):
        dt = 0.02
        complex_time = damping + 1j
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        kinetic = k * k / (2.0 * reduced_mass)
        psi = np.fft.ifft(np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi))
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))

    records = {}
    closure = {}
    for name, target in config["targets"].items():
        ratio = float(target["nuclear_electron_mass_ratio"])
        charge = float(target["nuclear_charge"])
        reduced_mass = ratio / (ratio + 1.0)
        native = -charge / np.sqrt(x * x + float(config["softening"]) ** 2)
        candidate = native - reference
        shift, mismatch_candidate, overlap = first_admissible_roll(
            candidate, 0, maximum_overlap
        )
        mismatch = reference + mismatch_candidate
        ground = np.exp(-x * x / 2.0).astype(complex)
        ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
        for _ in range(int(config["ground_steps"])):
            ground = step(ground, native, reduced_mass, 0.50)
        scores = {}
        for condition in CONDITIONS:
            psi = ground.copy()
            for index in range(int(config["dynamic_steps"])):
                if condition == "intact":
                    potential = native
                elif condition == "removed":
                    potential = reference
                elif index < int(config["removal_steps_before_return"]):
                    potential = reference
                elif condition == "correct_return":
                    potential = reference + candidate
                else:
                    potential = mismatch
                psi = step(psi, potential, reduced_mass, 0.08)
            mask = np.abs(x) < float(config["local_window"])
            scores[condition] = float(np.sum(np.abs(psi[mask]) ** 2) * dx)
        records[name] = {
            "nuclear_charge": charge,
            "reduced_mass_electron_units": reduced_mass,
            "scores": scores,
        }
        closure[name] = {
            "mismatch_shift_cells": shift,
            "mismatch_shift_distance": shift * dx,
            "centered_overlap": overlap,
            "reconstruction_error": float(np.max(np.abs(reference + candidate - native))),
            "candidate_norm_preservation_error": abs(
                float(np.linalg.norm(candidate)) - float(np.linalg.norm(mismatch_candidate))
            ),
        }
    return {"engine": "atomic_domain_prior_soft_coulomb", "targets": records, "closure": closure}


def molecular_engine(config: dict, maximum_overlap: float, checkpoint: Path) -> dict:
    e010 = load_module(
        "e010_for_e013_confirm",
        "experiments/010_complete_molecular_carrier_transfer/run.py",
    )
    a_values = [
        round(float(config["a_minimum_angstrom"]) + index * float(config["a_step_angstrom"]), 1)
        for index in range(
            int(round((float(config["a_maximum_angstrom"]) - float(config["a_minimum_angstrom"])) / float(config["a_step_angstrom"]))) + 1
        )
    ]
    b = float(config["b_angstrom"])
    energies = load_json(checkpoint) if checkpoint.exists() else {}
    for a in a_values:
        key = f"{a:.1f},{b:.1f}"
        record = energies.setdefault(key, {})
        missing = [mode for mode in ("full", "isolated") if mode not in record]
        if missing:
            built = e010.build_target(config["basis"], a, b)
            record["n_orbitals"] = int(built["h_full"].shape[0])
            for mode in missing:
                record[mode] = float(e010.fci_solution(built, mode)[0])
                checkpoint.write_text(json.dumps(energies, indent=2, sort_keys=True) + "\n")
    native = np.array([energies[f"{a:.1f},{b:.1f}"]["full"] for a in a_values])
    reference = np.array([energies[f"{a:.1f},{b:.1f}"]["isolated"] for a in a_values])
    candidate = native - reference
    shift, mismatch_candidate, overlap = first_admissible_roll(candidate, 0, maximum_overlap)
    mismatch = reference + mismatch_candidate
    reconstructed = reference + candidate
    minimum = float(np.min(native))
    minima = [index for index, value in enumerate(native) if abs(value - minimum) <= float(config["minimum_energy_tolerance_hartree"])]

    def move(surface, index, rng):
        neighbors = [item for item in (index - 1, index + 1) if 0 <= item < len(surface)]
        proposed = neighbors[int(rng.integers(len(neighbors)))]
        delta = float(surface[proposed] - surface[index])
        if delta <= 0.0 or rng.random() < math.exp(-delta / float(config["temperature_hartree"])):
            return proposed
        return index

    scores = {}
    details = {}
    start = max(minima)
    for condition in CONDITIONS:
        seed_scores = []
        for seed in config["trajectory_seeds"]:
            rng = np.random.default_rng(int(seed))
            index = start
            trajectory = []
            for step_index in range(int(config["total_steps"])):
                if condition == "intact":
                    surface = native
                elif condition == "removed":
                    surface = reference
                elif step_index < int(config["removal_steps_before_return"]):
                    surface = reference
                elif condition == "correct_return":
                    surface = reconstructed
                else:
                    surface = mismatch
                index = move(surface, index, rng)
                trajectory.append(index)
            late = trajectory[-int(config["late_window_steps"]):]
            radius = float(config["minimum_radius_angstrom"])
            seed_scores.append(float(np.mean([
                min(abs(a_values[item] - a_values[target]) for target in minima) <= radius
                for item in late
            ])))
        scores[condition] = float(np.mean(seed_scores))
        details[condition] = {"whole_score": scores[condition], "seed_scores": seed_scores}
    return {
        "engine": "molecular_cc_pvtz_fci_generated_residual_line",
        "scores": scores,
        "details": details,
        "native_minima_angstrom": [a_values[index] for index in minima],
        "closure": {
            "mismatch_shift_steps": shift,
            "centered_overlap": overlap,
            "reconstruction_error": float(np.max(np.abs(reconstructed - native))),
            "candidate_norm_preservation_error": abs(float(np.linalg.norm(candidate)) - float(np.linalg.norm(mismatch_candidate))),
            "reference_energy_range_hartree": float(np.max(reference) - np.min(reference)),
        },
    }


def cellular_engine(config: dict, maximum_overlap: float) -> dict:
    core = load_module(
        "e009_core_for_e013_confirm",
        "experiments/009_constitutive_cell_o3_closure/core.py",
    )
    base = core.DynamicsConfig()

    def candidate_series(lineage):
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

    calibration = core.simulate(int(config["calibration_seed"]), base, "native")
    series = candidate_series(calibration)
    selected = None
    for minutes in range(1, int(config["maximum_shift_minutes"]) + 1):
        lag = int(round(minutes / base.dt_minutes))
        overlap = centered_overlap(series[lag:], series[:-lag])
        if overlap <= maximum_overlap:
            selected = (float(minutes), overlap)
            break
    if selected is None:
        raise RuntimeError("no admissible cellular time mismatch")
    shift_minutes, overlap = selected
    dynamics = core.DynamicsConfig(shift_minutes=shift_minutes)
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
        for condition, cell_condition in mapping.items():
            lineages = [
                core.simulate(seed, dynamics, cell_condition)
                for seed in range(int(start), int(start) + count)
            ]
            scores[condition] = float(np.mean([item["alive"] for item in lineages]))
        cohorts[f"cohort_{number}"] = {"seed_range": [int(start), int(start) + count - 1], "scores": scores}
    reconstruction_error = 0.0
    for left in np.linspace(0.0, 2.0, 81):
        for right in np.linspace(0.0, 2.0, 81):
            native = core.joint_gate(float(left), float(right), False)
            reference = core.joint_gate(float(left), float(right), True)
            candidate = native - reference
            reconstruction_error = max(reconstruction_error, abs(reference + candidate - native))
    return {
        "engine": "cellular_generated_joint_residual",
        "calibration": {"seed": int(config["calibration_seed"]), "selected_shift_minutes": shift_minutes, "centered_overlap": overlap, "survival_not_used_for_selection": True},
        "cohorts": cohorts,
        "closure": {"reconstruction_error": reconstruction_error, "candidate_operator_unchanged_under_time_transport": True},
    }


def realization_scores(domains: dict) -> dict:
    return {
        "atomic": {name: item["scores"] for name, item in domains["atomic"]["targets"].items()},
        "molecular": {"cc-pvtz_fresh_line": domains["molecular"]["scores"]},
        "cellular": {name: item["scores"] for name, item in domains["cellular"]["cohorts"].items()},
    }


def gates(scores: dict, thresholds: dict) -> dict:
    return {
        "intact_high": scores["intact"] >= float(thresholds["high_minimum"]),
        "removed_low": scores["removed"] <= float(thresholds["low_maximum"]),
        "mismatched_low": scores["mismatched_return"] <= float(thresholds["low_maximum"]),
        "correct_high": scores["correct_return"] >= float(thresholds["high_minimum"]),
        "specific_return": scores["correct_return"] >= max(scores["removed"], scores["mismatched_return"]) + float(thresholds["specific_return_advantage_minimum"]),
    }


def causal_lodo(scores: dict) -> dict:
    output = {}
    for heldout in scores:
        training = [domain for domain in scores if domain != heldout]
        training_pass = all(
            item[left] > item[right]
            for domain in training
            for item in scores[domain].values()
            for left, right in CAUSAL_EDGES
        )
        checks = {
            name: all(item[left] > item[right] for left, right in CAUSAL_EDGES)
            for name, item in scores[heldout].items()
        }
        output[heldout] = {"training_domains": training, "training_pass": training_pass, "heldout_checks": checks, "pass": training_pass and all(checks.values())}
    return output


def unrestricted_lodo(scores: dict) -> dict:
    pairs = list(itertools.combinations(CONDITIONS, 2))
    direction = lambda item, left, right: 1 if item[left] > item[right] else -1 if item[left] < item[right] else 0
    output = {}
    for heldout in scores:
        training = [domain for domain in scores if domain != heldout]
        learned = []
        for left, right in pairs:
            values = [direction(item, left, right) for domain in training for item in scores[domain].values()]
            if values and values[0] != 0 and all(value == values[0] for value in values):
                learned.append((left, right, values[0]))
        checks = {name: all(direction(item, left, right) == expected for left, right, expected in learned) for name, item in scores[heldout].items()}
        output[heldout] = {"learned_relations": [f"{left} {'>' if expected > 0 else '<'} {right}" for left, right, expected in learned], "heldout_checks": checks, "pass": bool(learned) and all(checks.values())}
    return output


def evaluate(registry: dict, receipt: dict, output: Path) -> dict:
    maximum_overlap = float(registry["maximum_centered_mismatch_overlap"])
    domains = {
        "atomic": atomic_engine(registry["atomic"], maximum_overlap),
        "molecular": molecular_engine(registry["molecular"], maximum_overlap, output / "molecular_energy_checkpoint.json"),
        "cellular": cellular_engine(registry["cellular"], maximum_overlap),
    }
    scores = realization_scores(domains)
    gate_records = {domain: {name: gates(item, registry["thresholds"]) for name, item in records.items()} for domain, records in scores.items()}
    realization_pass = {domain: {name: all(item.values()) for name, item in records.items()} for domain, records in gate_records.items()}
    causal = causal_lodo(scores)
    unrestricted = unrestricted_lodo(scores)
    flattened = [item for records in scores.values() for item in records.values()]
    minimum_high = min(min(item["intact"], item["correct_return"]) for item in flattened)
    maximum_low = max(max(item["removed"], item["mismatched_return"]) for item in flattened)
    margin = minimum_high - maximum_low
    tolerance = float(registry["reconstruction_tolerance"])
    closure_pass = (
        all(item["reconstruction_error"] <= tolerance and item["candidate_norm_preservation_error"] <= tolerance and item["centered_overlap"] <= maximum_overlap for item in domains["atomic"]["closure"].values())
        and domains["molecular"]["closure"]["reconstruction_error"] <= tolerance
        and domains["molecular"]["closure"]["candidate_norm_preservation_error"] <= tolerance
        and domains["molecular"]["closure"]["centered_overlap"] <= maximum_overlap
        and domains["cellular"]["closure"]["reconstruction_error"] <= tolerance
        and domains["cellular"]["calibration"]["centered_overlap"] <= maximum_overlap
    )
    supported = (
        closure_pass
        and all(all(records.values()) for records in realization_pass.values())
        and all(item["pass"] for item in causal.values())
        and margin > float(registry["thresholds"]["threshold_free_margin_minimum"])
    )
    return {
        "schema": "siel-e013-result-v1",
        "decision": "DOMAIN_PRIOR_O3_GENERATION_TRANSFER_SUPPORTED" if supported else "DOMAIN_PRIOR_O3_GENERATION_TRANSFER_NOT_SUPPORTED",
        "registration_receipt": receipt,
        "domains": domains,
        "realization_scores": scores,
        "gates": gate_records,
        "realization_pass": realization_pass,
        "reference_candidate_rule_pass": closure_pass,
        "causal_partial_order_leave_one_domain_out": causal,
        "unrestricted_learned_pairwise_leave_one_domain_out_diagnostic": unrestricted,
        "threshold_free_separation": {"minimum_intact_or_correct": minimum_high, "maximum_removed_or_mismatched": maximum_low, "margin": margin, "pass": margin > 0.0},
        "no_shared_scalar_entered_domain_dynamics": True,
        "scope": {"supported_if_positive": "prospective cross-domain transfer of a domain-prior O3 generation-and-intervention grammar", "not_established": ["common physical O3 substance", "microscopic atom-to-cell law", "laboratory confirmation in natural systems"]},
    }


def write_results(output: Path, summary: dict) -> None:
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with (output / "domain_scores.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("domain", "realization", "condition", "whole_score"))
        for domain, records in summary["realization_scores"].items():
            for name, scores in records.items():
                for condition in CONDITIONS:
                    writer.writerow((domain, name, condition, scores[condition]))
    separation = summary["threshold_free_separation"]
    lines = ["# Experiment 013 result", "", f"Decision: `{summary['decision']}`", "", f"Threshold-free separation margin: `{separation['margin']:.9f}`.", "", "All supported, mixed, and unsupported component outcomes are retained in `summary.json`."]
    (output / "RESULT.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--registration-receipt", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    manifest, registry = verify_registration()
    if args.validate_registration:
        if args.registration_receipt is not None:
            raise ProvenanceError("validation mode refuses a registration receipt")
        print(json.dumps({"status": "VALID", "registration_tag": manifest["registration_tag"], "target_execution_performed": False}, sort_keys=True))
        return
    if args.registration_receipt is None:
        raise ProvenanceError("execution requires --registration-receipt")
    receipt = validate_receipt(args.registration_receipt)
    if args.output.exists():
        raise ProvenanceError("result directory already exists")
    args.output.mkdir(parents=True)
    summary = evaluate(registry, receipt, args.output)
    write_results(args.output, summary)
    print(json.dumps({"decision": summary["decision"], "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
