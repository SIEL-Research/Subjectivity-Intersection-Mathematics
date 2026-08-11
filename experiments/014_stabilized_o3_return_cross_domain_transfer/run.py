#!/usr/bin/env python3
"""Frozen runner for Experiment 014 stabilized O3-return transfer."""

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
    """Raised when the preregistration lock is not satisfied."""


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
    if manifest.get("schema") != "siel-experiment-014-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_execution_performed") is not False:
        raise ProvenanceError("registration declares target execution")
    if registry.get("schema") != "siel-e014-target-registry-v1":
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
    required = {"schema", "tag", "commit", "release_url", "doi"}
    if set(receipt) != required:
        raise ProvenanceError("registration receipt fields mismatch")
    if receipt["schema"] != "siel-e014-registration-receipt-v1":
        raise ProvenanceError("registration receipt schema mismatch")
    if receipt["tag"] != "e014-preregistration-v1.0.0":
        raise ProvenanceError("registration receipt tag mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", receipt["commit"]):
        raise ProvenanceError("registration commit is not a full SHA")
    if not receipt["release_url"].endswith(
        "/releases/tag/e014-preregistration-v1.0.0"
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


def normalize(values: np.ndarray) -> np.ndarray:
    output = np.maximum(np.asarray(values, dtype=float), 0.0)
    total = float(np.sum(output))
    if not math.isfinite(total) or total <= 0.0:
        raise FloatingPointError("distribution cannot be normalized")
    return output / total


def hellinger_similarity(observed: np.ndarray, target: np.ndarray) -> float:
    observed = normalize(observed)
    target = normalize(target)
    distance = float(
        np.sqrt(0.5 * np.sum((np.sqrt(observed) - np.sqrt(target)) ** 2))
    )
    return 1.0 - distance


def js_similarity(observed: np.ndarray, target: np.ndarray) -> float:
    observed = normalize(observed)
    target = normalize(target)
    midpoint = 0.5 * (observed + target)
    divergence = 0.5 * (
        np.sum(np.where(observed > 0.0, observed * np.log(observed / midpoint), 0.0))
        + np.sum(np.where(target > 0.0, target * np.log(target / midpoint), 0.0))
    )
    return 1.0 - float(divergence / math.log(2.0))


def centered_overlap(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float) - float(np.mean(left))
    right = np.asarray(right, dtype=float) - float(np.mean(right))
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator <= 0.0:
        raise ValueError("centered carrier has zero norm")
    return float(np.vdot(left.ravel(), right.ravel()).real / denominator)


def nonperiodic_shift(values: np.ndarray, steps: int) -> np.ndarray:
    output = np.empty_like(values)
    if steps > 0:
        output[:steps] = values[0]
        output[steps:] = values[:-steps]
    elif steps < 0:
        count = -steps
        output[-count:] = values[-1]
        output[:-count] = values[count:]
    else:
        output[:] = values
    return output


def coordinate_warp(coordinates: np.ndarray, values: np.ndarray, scale: float) -> np.ndarray:
    centre = 0.5 * (float(coordinates[0]) + float(coordinates[-1]))
    source = centre + scale * (coordinates - centre)
    return np.interp(
        source, coordinates, values, left=values[0], right=values[-1]
    )


def transition(surface: np.ndarray, temperature: float) -> np.ndarray:
    size = len(surface)
    matrix = np.zeros((size, size), dtype=float)
    for index in range(size):
        neighbours = [item for item in (index - 1, index + 1) if 0 <= item < size]
        for proposed in neighbours:
            log_acceptance = -float(surface[proposed] - surface[index]) / temperature
            acceptance = 1.0 if log_acceptance >= 0.0 else math.exp(max(log_acceptance, -745.0))
            proposal = 1.0 / len(neighbours)
            matrix[index, proposed] += proposal * acceptance
            matrix[index, index] += proposal * (1.0 - acceptance)
    return matrix


def propagate(distribution: np.ndarray, matrix: np.ndarray, steps: int) -> np.ndarray:
    return normalize(distribution @ np.linalg.matrix_power(matrix, steps))


def stationary_distribution(surface: np.ndarray, temperature: float) -> np.ndarray:
    shifted = np.asarray(surface, dtype=float) - float(np.min(surface))
    weights = np.exp(np.maximum(-shifted / temperature, -745.0))
    return normalize(weights)


def refine(values: np.ndarray, factor: int) -> np.ndarray:
    old = np.linspace(0.0, 1.0, len(values))
    new = np.linspace(0.0, 1.0, (len(values) - 1) * factor + 1)
    return np.interp(new, old, values)


def atomic_engine(config: dict) -> dict:
    n = int(config["grid_points"])
    half_width = float(config["half_width"])
    dx = 2.0 * half_width / n
    x = np.linspace(-half_width, half_width - dx, n)
    k = 2.0 * np.pi * np.fft.fftfreq(n, d=dx)
    mass_ratio = float(config["nuclear_electron_mass_ratio"])
    reduced_mass = mass_ratio / (mass_ratio + 1.0)
    charge = float(config["nuclear_charge"])
    softening = float(config["softening"])
    native = -charge / np.sqrt(x * x + softening**2)
    reference = np.zeros_like(x)
    mismatch = -charge / np.sqrt(
        (x - float(config["mismatch_translation_distance"])) ** 2 + softening**2
    )

    def step(psi: np.ndarray, potential: np.ndarray, damping: float) -> np.ndarray:
        dt = float(config["dt"])
        complex_time = damping + 1j
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        kinetic = k * k / (2.0 * reduced_mass)
        psi = np.fft.ifft(np.exp(-complex_time * kinetic * dt) * np.fft.fft(psi))
        psi = np.exp(-complex_time * potential * dt / 2.0) * psi
        norm = math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))
        return psi / norm

    def advance(initial: np.ndarray, potential: np.ndarray, steps: int, damping: float) -> np.ndarray:
        state = initial.copy()
        for _ in range(steps):
            state = step(state, potential, damping)
        return state

    ground = np.exp(-x * x / 2.0).astype(complex)
    ground /= math.sqrt(float(np.sum(np.abs(ground) ** 2) * dx))
    ground = advance(ground, native, int(config["ground_steps"]), 0.50)
    removed_at_return = advance(
        ground, reference, int(config["removal_steps"]), float(config["dynamic_damping"])
    )
    checkpoints = []
    for return_steps in config["return_checkpoints"]:
        return_steps = int(return_steps)
        total = int(config["removal_steps"]) + return_steps
        states = {
            "intact": advance(ground, native, total, float(config["dynamic_damping"])),
            "removed": advance(ground, reference, total, float(config["dynamic_damping"])),
            "correct_return": advance(removed_at_return, native, return_steps, float(config["dynamic_damping"])),
            "mismatched_return": advance(removed_at_return, mismatch, return_steps, float(config["dynamic_damping"])),
        }
        distributions = {
            name: normalize(np.abs(state) ** 2 * dx) for name, state in states.items()
        }
        scores = {
            name: hellinger_similarity(distribution, distributions["intact"])
            for name, distribution in distributions.items()
        }
        margin_removed = scores["correct_return"] - scores["removed"]
        margin_mismatch = scores["correct_return"] - scores["mismatched_return"]
        checkpoints.append(
            {
                "return_steps": return_steps,
                "scores": scores,
                "correct_minus_removed": margin_removed,
                "correct_minus_mismatch": margin_mismatch,
                "pass": margin_removed > 0.0 and margin_mismatch > 0.0,
            }
        )
    candidate = native - reference
    mismatch_candidate = mismatch - reference
    return {
        "engine": "helium4_hydrogenic_soft_coulomb",
        "mass_ratio_source": config["mass_ratio_source"],
        "reduced_mass_electron_units": reduced_mass,
        "closure": {
            "reconstruction_error": float(np.max(np.abs(reference + candidate - native))),
            "mismatch_translation_distance": float(config["mismatch_translation_distance"]),
            "centered_overlap": centered_overlap(candidate, mismatch_candidate),
            "carrier_difference_norm": float(np.linalg.norm(candidate - mismatch_candidate)),
        },
        "checkpoints": checkpoints,
        "all_checkpoints_pass": all(item["pass"] for item in checkpoints),
    }


def molecular_energies(config: dict, checkpoint: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    e010 = load_module(
        "e010_for_e014_confirm",
        "experiments/010_complete_molecular_carrier_transfer/run.py",
    )
    a_values = np.arange(
        float(config["a_minimum_angstrom"]),
        float(config["a_maximum_angstrom"]) + 0.5 * float(config["a_step_angstrom"]),
        float(config["a_step_angstrom"]),
    )
    a_values = np.round(a_values, 10)
    b = float(config["b_angstrom"])
    energies = load_json(checkpoint) if checkpoint.exists() else {}
    for a in a_values:
        key = f"{a:.1f},{b:.1f}"
        record = energies.setdefault(key, {})
        missing = [mode for mode in ("full", "isolated") if mode not in record]
        if missing:
            built = e010.build_target(config["basis"], float(a), b)
            record["n_orbitals"] = int(built["h_full"].shape[0])
            for mode in missing:
                record[mode] = float(e010.fci_solution(built, mode)[0])
                checkpoint.write_text(json.dumps(energies, indent=2, sort_keys=True) + "\n")
    native = np.asarray([energies[f"{a:.1f},{b:.1f}"]["full"] for a in a_values])
    reference = np.asarray([energies[f"{a:.1f},{b:.1f}"]["isolated"] for a in a_values])
    return a_values, native, reference


def select_molecular_mismatch(
    coordinates: np.ndarray, native: np.ndarray, reference: np.ndarray, config: dict
) -> dict:
    candidate = native - reference
    alternatives = [("coordinate_reflection", candidate[::-1])]
    for shift in config["mismatch_candidate_shifts"]:
        alternatives.append((f"nonperiodic_shift_{int(shift):+d}", nonperiodic_shift(candidate, int(shift))))
    for scale in config["mismatch_candidate_warps"]:
        alternatives.append((f"coordinate_warp_{float(scale):.2f}", coordinate_warp(coordinates, candidate, float(scale))))
    native_stationary = stationary_distribution(native, float(config["temperature_hartree"]))
    eligible = []
    for label, alternative in alternatives:
        overlap = centered_overlap(candidate, alternative)
        if overlap > float(config["maximum_centered_overlap"]):
            continue
        mismatch_surface = reference + alternative
        separation = 1.0 - js_similarity(
            stationary_distribution(mismatch_surface, float(config["temperature_hartree"])),
            native_stationary,
        )
        if separation >= float(config["preoutcome_discriminability_floor"]):
            eligible.append((separation, label, alternative, overlap))
    if not eligible:
        raise RuntimeError("no preregistered molecular mismatch passes structural gates")
    separation, label, alternative, overlap = min(eligible, key=lambda item: (item[0], item[1]))
    return {
        "label": label,
        "candidate": alternative,
        "centered_overlap": overlap,
        "preoutcome_stationary_js_separation": separation,
    }


def molecular_engine(config: dict, checkpoint: Path) -> dict:
    coordinates, original_native, original_reference = molecular_energies(config, checkpoint)
    selection = select_molecular_mismatch(coordinates, original_native, original_reference, config)
    original_candidate = original_native - original_reference
    original_alternative = np.asarray(selection["candidate"], dtype=float)
    rows = []
    for factor in config["grid_factors"]:
        factor = int(factor)
        native = refine(original_native, factor)
        reference = refine(original_reference, factor)
        candidate = native - reference
        if selection["label"] == "coordinate_reflection":
            alternative = candidate[::-1]
        elif selection["label"].startswith("nonperiodic_shift_"):
            shift = int(selection["label"].rsplit("_", 1)[1]) * factor
            alternative = nonperiodic_shift(candidate, shift)
        elif selection["label"].startswith("coordinate_warp_"):
            scale = float(selection["label"].rsplit("_", 1)[1])
            refined_coordinates = np.linspace(coordinates[0], coordinates[-1], len(native))
            alternative = coordinate_warp(refined_coordinates, candidate, scale)
        else:
            raise RuntimeError("unregistered molecular mismatch family")
        mismatch = reference + alternative
        matrices = {
            "native": transition(native, float(config["temperature_hartree"])),
            "reference": transition(reference, float(config["temperature_hartree"])),
            "mismatch": transition(mismatch, float(config["temperature_hartree"])),
        }
        minima = np.flatnonzero(
            np.abs(native - float(np.min(native))) <= float(config["minimum_energy_tolerance_hartree"])
        ).tolist()
        initial = np.zeros(len(native), dtype=float)
        initial[max(minima)] = 1.0
        removal = int(config["base_removal_steps"]) * factor * factor
        removed_at_return = propagate(initial, matrices["reference"], removal)
        for base_return in config["base_return_checkpoints"]:
            returned = int(base_return) * factor * factor
            intact = propagate(initial, matrices["native"], removal + returned)
            distributions = {
                "intact": intact,
                "removed": propagate(initial, matrices["reference"], removal + returned),
                "correct_return": propagate(removed_at_return, matrices["native"], returned),
                "mismatched_return": propagate(removed_at_return, matrices["mismatch"], returned),
            }
            scores = {
                name: hellinger_similarity(distribution, intact)
                for name, distribution in distributions.items()
            }
            margin_removed = scores["correct_return"] - scores["removed"]
            margin_mismatch = scores["correct_return"] - scores["mismatched_return"]
            rows.append(
                {
                    "grid_factor": factor,
                    "grid_points": len(native),
                    "base_return_steps": int(base_return),
                    "scores": scores,
                    "correct_minus_removed": margin_removed,
                    "correct_minus_mismatch": margin_mismatch,
                    "pass": margin_removed > 0.0 and margin_mismatch > 0.0,
                }
            )
    reconstruction_error = float(np.max(np.abs(original_reference + original_candidate - original_native)))
    return {
        "engine": "cc_pvtz_h4plus_exact_transition_distribution",
        "basis": config["basis"],
        "b_angstrom": float(config["b_angstrom"]),
        "a_values_angstrom": coordinates.tolist(),
        "mismatch_selection": {key: value for key, value in selection.items() if key != "candidate"},
        "closure": {
            "reconstruction_error": reconstruction_error,
            "mismatch_carrier_difference_norm": float(np.linalg.norm(original_candidate - original_alternative)),
        },
        "checkpoints": rows,
        "all_checkpoints_pass": all(item["pass"] for item in rows),
        "all_grid_factors_pass": all(
            all(item["pass"] for item in rows if item["grid_factor"] == int(factor))
            for factor in config["grid_factors"]
        ),
    }


def paired_cell_similarity(native: dict, condition: dict, index: int) -> float:
    difference = np.concatenate(
        (
            condition["modules"][index] - native["modules"][index],
            [(condition["states"][index, 5] - native["states"][index, 5]) / 0.10],
            [condition["states"][index, 6] - native["states"][index, 6]],
        )
    )
    return float(np.exp(-np.linalg.norm(difference) / np.sqrt(len(difference))))


def bootstrap_lower_bound(differences: np.ndarray, seed: int, replicates: int, quantile: float) -> float:
    differences = np.asarray(differences, dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(differences), size=(replicates, len(differences)))
    means = np.mean(differences[indices], axis=1)
    return float(np.quantile(means, quantile, method="linear"))


def cellular_engine(config: dict) -> dict:
    core = load_module(
        "e009_core_for_e014_confirm",
        "experiments/009_constitutive_cell_o3_closure/core.py",
    )
    mapping = {
        "intact": "native",
        "removed": "joint_erased",
        "mismatched_return": "time_shifted",
        "correct_return": "reinjected",
    }
    scenarios = []
    boundary_checks = []
    for amplitude_index, amplitude in enumerate(config["damage_amplitudes"]):
        amplitude = float(amplitude)
        for reinjection in config["reinjection_minutes"]:
            reinjection = float(reinjection)
            dynamics = core.DynamicsConfig(
                moderate_damage_amplitude=amplitude,
                reinjection_minutes=reinjection,
            )
            cohort_records = []
            pooled = {condition: [] for condition in CONDITIONS}
            for cohort_number, start in enumerate(config["cohort_starts"], 1):
                seeds = range(int(start), int(start) + int(config["lineages_per_cohort"]))
                lineages = {
                    condition: [core.simulate(seed, dynamics, cell_condition) for seed in seeds]
                    for condition, cell_condition in mapping.items()
                }
                alive = {
                    condition: float(np.mean([item["alive"] for item in items]))
                    for condition, items in lineages.items()
                }
                for condition in CONDITIONS:
                    pooled[condition].extend(lineages[condition])
                predicted_success = reinjection == float(config["predicted_success_reinjection_minutes"])
                correct_rate_pass = (
                    alive["correct_return"] >= float(config["success_alive_fraction_minimum"])
                    if predicted_success
                    else alive["correct_return"] <= float(config["failure_alive_fraction_maximum"])
                )
                nulls_fail = (
                    alive["removed"] <= float(config["failure_alive_fraction_maximum"])
                    and alive["mismatched_return"] <= float(config["failure_alive_fraction_maximum"])
                )
                record = {
                    "cohort": cohort_number,
                    "seed_range": [int(start), int(start) + int(config["lineages_per_cohort"]) - 1],
                    "alive_fraction": alive,
                    "predicted_correct_return_success": predicted_success,
                    "correct_boundary_pass": correct_rate_pass,
                    "null_boundary_pass": nulls_fail,
                    "pass": correct_rate_pass and nulls_fail,
                }
                cohort_records.append(record)
                boundary_checks.append(record["pass"])
            specificity_rows = []
            if reinjection == float(config["predicted_success_reinjection_minutes"]):
                for post_minutes in config["stabilized_post_reinjection_minutes"]:
                    observation = min(float(dynamics.duration_minutes), reinjection + float(post_minutes))
                    index = int(round(observation / dynamics.dt_minutes))
                    similarities = {
                        condition: np.asarray(
                            [
                                paired_cell_similarity(native, candidate, index)
                                for native, candidate in zip(pooled["intact"], pooled[condition])
                            ],
                            dtype=float,
                        )
                        for condition in ("removed", "mismatched_return", "correct_return")
                    }
                    comparisons = {}
                    for comparison_index, null in enumerate(("removed", "mismatched_return")):
                        differences = similarities["correct_return"] - similarities[null]
                        lower = bootstrap_lower_bound(
                            differences,
                            int(config["bootstrap_seed"]) + 1000 * amplitude_index + 100 * int(post_minutes) + comparison_index,
                            int(config["bootstrap_replicates"]),
                            float(config["bootstrap_lower_quantile"]),
                        )
                        comparisons[null] = {
                            "mean_margin": float(np.mean(differences)),
                            "bootstrap_lower_bound": lower,
                            "pass": lower > 0.0,
                        }
                    specificity_rows.append(
                        {
                            "post_reinjection_minutes": float(post_minutes),
                            "observation_minutes": observation,
                            "mean_similarity": {
                                condition: float(np.mean(values))
                                for condition, values in similarities.items()
                            },
                            "comparisons": comparisons,
                            "pass": all(item["pass"] for item in comparisons.values()),
                        }
                    )
            scenarios.append(
                {
                    "damage_amplitude": amplitude,
                    "reinjection_minutes": reinjection,
                    "cohorts": cohort_records,
                    "stabilized_specificity": specificity_rows,
                    "boundary_pass": all(item["pass"] for item in cohort_records),
                    "specificity_pass": all(item["pass"] for item in specificity_rows) if specificity_rows else None,
                }
            )
    specificity = [
        item["pass"]
        for scenario in scenarios
        for item in scenario["stabilized_specificity"]
    ]
    return {
        "engine": "frozen_e009_reduced_stochastic_cell",
        "scenarios": scenarios,
        "all_boundary_predictions_pass": all(boundary_checks),
        "all_stabilized_specificity_checkpoints_pass": all(specificity),
        "stabilized_specificity_check_count": len(specificity),
    }


def leave_one_domain_out(domain_passes: dict) -> dict:
    output = {}
    for heldout in domain_passes:
        training = [domain for domain in domain_passes if domain != heldout]
        training_direction = all(domain_passes[domain] for domain in training)
        output[heldout] = {
            "training_domains": training,
            "training_supports_positive_direction": training_direction,
            "heldout_all_primary_checkpoints_pass": domain_passes[heldout],
            "pass": training_direction and domain_passes[heldout],
        }
    return output


def evaluate(registry: dict, receipt: dict, output: Path) -> dict:
    domains = {
        "atomic": atomic_engine(registry["atomic"]),
        "molecular": molecular_engine(
            registry["molecular"], output / "molecular_energy_checkpoint.json"
        ),
        "cellular": cellular_engine(registry["cellular"]),
    }
    tolerance = float(registry["reconstruction_tolerance"])
    structural_gates = {
        "atomic_reconstruction": domains["atomic"]["closure"]["reconstruction_error"] <= tolerance,
        "atomic_mismatch_distinct": domains["atomic"]["closure"]["carrier_difference_norm"] > 0.0,
        "molecular_reconstruction": domains["molecular"]["closure"]["reconstruction_error"] <= tolerance,
        "molecular_mismatch_overlap": domains["molecular"]["mismatch_selection"]["centered_overlap"] <= float(registry["molecular"]["maximum_centered_overlap"]),
        "molecular_mismatch_discriminable": domains["molecular"]["mismatch_selection"]["preoutcome_stationary_js_separation"] >= float(registry["molecular"]["preoutcome_discriminability_floor"]),
        "no_shared_scalar_in_domain_engines": True,
    }
    domain_passes = {
        "atomic": domains["atomic"]["all_checkpoints_pass"],
        "molecular": domains["molecular"]["all_checkpoints_pass"] and domains["molecular"]["all_grid_factors_pass"],
        "cellular": domains["cellular"]["all_boundary_predictions_pass"] and domains["cellular"]["all_stabilized_specificity_checkpoints_pass"],
    }
    lodo = leave_one_domain_out(domain_passes)
    supported = (
        all(structural_gates.values())
        and all(domain_passes.values())
        and all(item["pass"] for item in lodo.values())
    )
    return {
        "schema": "siel-e014-result-v1",
        "decision": "STABILIZED_O3_RETURN_CROSS_DOMAIN_TRANSFER_SUPPORTED" if supported else "STABILIZED_O3_RETURN_CROSS_DOMAIN_TRANSFER_NOT_SUPPORTED",
        "registration_receipt": receipt,
        "registered_cross_domain_direction": "after domain-native stabilization, correct O3 return is closer to the registered domain state than continued removal or physically distinguishable mismatched return",
        "domains": domains,
        "structural_gates": structural_gates,
        "domain_primary_pass": domain_passes,
        "leave_one_domain_out": lodo,
        "all_primary_gates_pass": supported,
        "compression_boundary": {
            "common_object": "direction of stabilized causal specificity",
            "shared_scalar_entered_domain_engines": False,
            "common_substance_or_source_identity_inferred": False,
        },
        "scope": {
            "supported_if_positive": "prospective transfer of stabilized correct-O3 return specificity across independent atomic, molecular, and cellular reduced realizations",
            "not_established": [
                "common microscopic atom-to-cell law",
                "identical O3 substance across domains",
                "living-cell laboratory confirmation",
                "phenomenal subjectivity",
                "universal instantaneous recovery-speed dominance",
            ],
        },
    }


def write_results(output: Path, summary: dict) -> None:
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with (output / "primary_checkpoints.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("domain", "realization", "checkpoint", "correct_minus_removed", "correct_minus_mismatch", "pass"))
        for item in summary["domains"]["atomic"]["checkpoints"]:
            writer.writerow(("atomic", "helium4_hydrogenic", item["return_steps"], item["correct_minus_removed"], item["correct_minus_mismatch"], item["pass"]))
        for item in summary["domains"]["molecular"]["checkpoints"]:
            writer.writerow(("molecular", f"grid_factor_{item['grid_factor']}", item["base_return_steps"], item["correct_minus_removed"], item["correct_minus_mismatch"], item["pass"]))
        for scenario in summary["domains"]["cellular"]["scenarios"]:
            for item in scenario["stabilized_specificity"]:
                writer.writerow(("cellular", f"damage_{scenario['damage_amplitude']}", item["post_reinjection_minutes"], item["comparisons"]["removed"]["mean_margin"], item["comparisons"]["mismatched_return"]["mean_margin"], item["pass"]))
    lines = [
        "# Experiment 014 result",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "All registered component results, including failures if any, are retained in `summary.json`.",
    ]
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
