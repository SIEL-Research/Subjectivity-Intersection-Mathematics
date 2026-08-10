from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REGISTRY_PATH = ROOT / "target_registry.json"
MANIFEST_PATH = ROOT / "registration_manifest.json"
CELL_CORE_PATH = ROOT / "cell_core.py"
COUPLINGS = np.round(np.arange(0.400, 0.920 + 0.0001, 0.002), 3)
SEED_COUNT = 96
REGISTRATION_TAG = "e011-preregistration-v1.0.0"
RESULT_TAG = "e011-results-v1.0.0"


def load_module(path: Path):
    specification = importlib.util.spec_from_file_location("e011_cell_core", path)
    if specification is None or specification.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


CELL = load_module(CELL_CORE_PATH)


@dataclass(frozen=True)
class TargetFamily:
    name: str
    bridge_exponent: float
    ensemble_seed: int
    damage_amplitude: float = 0.60
    intervention_end: float = 50.0


TARGET_FAMILIES = (
    TargetFamily("heldout_q_0_75", 0.75, 2026130100),
    TargetFamily("heldout_q_1_25", 1.25, 2026130200),
    TargetFamily("heldout_q_1_50", 1.50, 2026130300),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text())


def validate_registration() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    observed = {
        relative: sha256(ROOT.parents[1] / relative)
        for relative in manifest["source_sha256"]
    }
    if observed != manifest["source_sha256"]:
        raise RuntimeError("registration source hash mismatch")
    registry = load_registry()
    registered = {
        (item["name"], float(item["bridge_exponent"]), int(item["ensemble_seed"]))
        for item in registry["heldout_target_families"]
    }
    implemented = {
        (item.name, item.bridge_exponent, item.ensemble_seed)
        for item in TARGET_FAMILIES
    }
    if registered != implemented:
        raise RuntimeError("implemented targets differ from registry")
    if set(registry["explored_bridge_exponents"]) & {
        item.bridge_exponent for item in TARGET_FAMILIES
    }:
        raise RuntimeError("held-out bridge exponent overlaps exploration")
    return {
        "status": "REGISTRATION_VALID_TARGET_NOT_EXECUTED",
        "files_verified": len(observed),
        "target_family_count": len(TARGET_FAMILIES),
        "lineages_per_coupling": SEED_COUNT,
    }


def validate_receipt(path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text())
    if receipt.get("tag") != REGISTRATION_TAG:
        raise RuntimeError("registration receipt tag mismatch")
    commit = str(receipt.get("commit", ""))
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("registration receipt commit is not a full SHA")
    if not str(receipt.get("doi", "")).startswith("10.5281/zenodo."):
        raise RuntimeError("registration receipt DOI is missing")
    if not str(receipt.get("release_url", "")).endswith(f"/tag/{REGISTRATION_TAG}"):
        raise RuntimeError("registration receipt release URL mismatch")
    return receipt


def batch_survival(family: TargetFamily) -> np.ndarray:
    config = CELL.DynamicsConfig()
    rng = np.random.default_rng(family.ensemble_seed)
    count_c = len(COUPLINGS)
    shape = (count_c, SEED_COUNT)
    states = np.zeros(shape + (len(CELL.STATE_NAMES),), dtype=float)
    initial_noise = rng.normal(
        0.0,
        [0.01, 0.02, 0.02, 0.01, 0.01, 0.002, 0.0],
        size=(SEED_COUNT, len(CELL.STATE_NAMES)),
    )
    states[:] = np.array([1.0, 1.0, 1.0, 1.0, 0.45, 0.02, 1.0]) + initial_noise
    dead = np.zeros(shape, dtype=bool)
    pre_samples: list[np.ndarray] = []
    late_module_samples: list[np.ndarray] = []
    late_damage_samples: list[np.ndarray] = []
    dt = config.dt_minutes
    steps = int(round(config.duration_minutes / dt)) + 1

    for index in range(steps - 1):
        time = index * dt
        B, N, A, G, R, D, X = np.moveaxis(
            np.maximum(
                states,
                np.array([0.001, 0.001, 0.001, 0.001, 0.001, 0.0, 0.1]),
            ),
            -1,
            0,
        )
        pulse = (
            family.damage_amplitude
            if config.damage_start_minutes <= time < config.damage_end_minutes
            else 0.0
        )
        active = config.damage_start_minutes <= time < family.intervention_end
        mediator = (
            COUPLINGS[:, None] ** (2.0 * family.bridge_exponent)
            if active
            else np.ones((count_c, 1), dtype=float)
        )

        uptake = 0.90 * B * G * mediator
        catabolism = 0.75 * G * CELL.saturating_array(N) * mediator
        expression = (
            0.32 * B * CELL.saturating_array(A) * CELL.saturating_array(N) * mediator
        )
        lipid = (
            0.28 * G * CELL.saturating_array(A) * CELL.saturating_array(N) * mediator
        )
        repair = (
            0.65
            * R
            * CELL.saturating_array(A)
            * CELL.saturating_array(D, 0.12)
            * mediator
        )
        derivative = np.stack(
            (
                lipid * (1.15 - B) + 0.35 * repair - 0.055 * B - pulse * 0.90 * B,
                uptake - catabolism - 0.12 * expression - 0.12 * lipid - 0.05 * N,
                1.15 * catabolism - 0.55 * expression - 0.55 * lipid - 0.75 * repair - 0.28 * A,
                expression * (1.15 - G) - (0.035 + 0.18 * D + 0.35 * pulse) * G,
                0.70 * expression * CELL.saturating_array(D, 0.15) * (1.20 - R) - 0.08 * R,
                0.008 + pulse * (0.35 + 0.65 * B) - repair - 0.035 * D,
                (0.009 * (expression + lipid) - 0.012 * D) * X,
            ),
            axis=-1,
        )
        base_noise = np.concatenate(
            (
                rng.normal(0.0, 0.0008, (SEED_COUNT, 5)),
                rng.normal(0.0, 0.00025, (SEED_COUNT, 1)),
                np.zeros((SEED_COUNT, 1)),
            ),
            axis=1,
        )
        proposal = states + dt * derivative + math.sqrt(dt) * base_noise[None, :, :]
        proposal[..., :6] = np.maximum(proposal[..., :6], 0.0)
        proposal[..., 6] = np.where(
            proposal[..., 6] >= 2.0,
            proposal[..., 6] / 2.0,
            proposal[..., 6],
        )
        newly_dead = (~dead) & (
            (B < config.death_boundary)
            | (A < config.death_atp)
            | (G < config.death_expression)
        )
        dead |= newly_dead
        states = np.where(dead[..., None], states, proposal)

        if 32.0 <= time < config.damage_start_minutes and index % 10 == 0:
            pre_samples.append(CELL.module_observables(states[0]).copy())
        if time >= 100.0 and index % 50 == 0:
            late_module_samples.append(CELL.module_observables(states).copy())
            late_damage_samples.append(states[..., 5].copy())

    pre_level = np.median(np.stack(pre_samples), axis=0)
    late_level = np.median(np.stack(late_module_samples), axis=0)
    late_damage = np.median(np.stack(late_damage_samples), axis=0)
    recovery = late_level / np.maximum(pre_level[None, :, :], 1e-12)
    return (~dead) & np.all(recovery >= 0.80, axis=-1) & (late_damage < 0.10)


def threshold(outcomes: np.ndarray, target: float) -> float | None:
    indices = np.flatnonzero(outcomes.mean(axis=1) >= target)
    return float(COUPLINGS[indices[0]]) if len(indices) else None


def bootstrap_interval(outcomes: np.ndarray, target: float, seed: int) -> list[float | None]:
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(500):
        selected = rng.integers(0, outcomes.shape[1], outcomes.shape[1])
        estimate = threshold(outcomes[:, selected], target)
        if estimate is not None:
            estimates.append(estimate)
    if not estimates:
        return [None, None]
    return [float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))]


def collapse_metrics(curves: list[np.ndarray]) -> dict[str, float]:
    matrix = np.stack(curves)
    mean_curve = matrix.mean(axis=0)
    family_rmse = np.sqrt(np.mean((matrix - mean_curve) ** 2, axis=1))
    return {
        "pooled_rmse": float(np.sqrt(np.mean((matrix - mean_curve) ** 2))),
        "maximum_family_rmse": float(np.max(family_rmse)),
        "maximum_pairwise_difference": float(
            max(np.max(np.abs(left - right)) for left in matrix for right in matrix)
        ),
    }


def evaluate() -> dict[str, Any]:
    registry = load_registry()
    family_results: dict[str, Any] = {}
    outcomes_by_name: dict[str, np.ndarray] = {}
    for family in TARGET_FAMILIES:
        print(f"running registered target {family.name}", flush=True)
        outcomes = batch_survival(family)
        outcomes_by_name[family.name] = outcomes
        survival = outcomes.mean(axis=1)
        lambda_10 = threshold(outcomes, 0.10)
        lambda_50 = threshold(outcomes, 0.50)
        lambda_90 = threshold(outcomes, 0.90)
        predicted = registry["predictions"][family.name]
        family_results[family.name] = {
            "parameters": asdict(family),
            "predicted_lambda_90": predicted["lambda_90"],
            "predicted_mediator_90": predicted["mediator_90"],
            "lambda_10": lambda_10,
            "lambda_50": lambda_50,
            "lambda_90": lambda_90,
            "lambda_90_bootstrap_95": bootstrap_interval(
                outcomes, 0.90, family.ensemble_seed + 99
            ),
            "mediator_90": (
                lambda_90 ** (2.0 * family.bridge_exponent)
                if lambda_90 is not None
                else None
            ),
            "survival_curve": {
                f"{coupling:.3f}": float(fraction)
                for coupling, fraction in zip(COUPLINGS, survival)
            },
        }

    lambdas = [item["lambda_90"] for item in family_results.values()]
    mediators = [item["mediator_90"] for item in family_results.values()]
    all_thresholds_observed = all(value is not None for value in lambdas + mediators)
    reference = float(registry["frozen_mediator_reference"])
    lambda_tolerance = float(registry["decision_thresholds"]["lambda_absolute_error_max"])
    mediator_tolerance = float(registry["decision_thresholds"]["mediator_absolute_error_max"])

    common_mediator_grid = np.linspace(0.20, 0.85, 326)
    transformed_curves = []
    for family in TARGET_FAMILIES:
        result = family_results[family.name]
        mediator_axis = COUPLINGS ** (2.0 * family.bridge_exponent)
        survival = np.asarray(list(result["survival_curve"].values()))
        transformed_curves.append(
            np.interp(common_mediator_grid, mediator_axis, survival)
        )
    collapse = collapse_metrics(transformed_curves)

    gates = {
        "G1_all_registered_thresholds_observed": all_thresholds_observed,
        "G2_all_raw_lambda_predictions_within_tolerance": all(
            abs(result["lambda_90"] - result["predicted_lambda_90"])
            <= lambda_tolerance
            for result in family_results.values()
        ) if all_thresholds_observed else False,
        "G3_all_mediator_predictions_within_tolerance": all(
            abs(result["mediator_90"] - reference) <= mediator_tolerance
            for result in family_results.values()
        ) if all_thresholds_observed else False,
        "G4_heldout_mediator_range_is_small": (
            max(mediators) - min(mediators)
            <= registry["decision_thresholds"]["mediator_range_max"]
        ) if all_thresholds_observed else False,
        "G5_raw_lambda_range_is_noninvariant": (
            max(lambdas) - min(lambdas)
            >= registry["decision_thresholds"]["raw_lambda_range_min"]
        ) if all_thresholds_observed else False,
        "G6_transformed_survival_curves_collapse": (
            collapse["pooled_rmse"]
            <= registry["decision_thresholds"]["transformed_curve_rmse_max"]
        ),
        "G7_registered_lambda_order_is_preserved": (
            lambdas == sorted(lambdas)
        ) if all_thresholds_observed else False,
    }
    mediator_core = gates["G3_all_mediator_predictions_within_tolerance"] and gates[
        "G4_heldout_mediator_range_is_small"
    ]
    if all(gates.values()):
        decision = "RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_SUPPORTED"
    elif mediator_core:
        decision = "RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_PARTIALLY_SUPPORTED"
    else:
        decision = "RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_NOT_SUPPORTED"

    return {
        "experiment": "011_renormalized_cross_scale_closure_prediction",
        "decision": decision,
        "gates": gates,
        "gates_passed": sum(gates.values()),
        "gates_total": len(gates),
        "frozen_mediator_reference": reference,
        "family_results": family_results,
        "heldout_raw_lambda_90_range": (
            max(lambdas) - min(lambdas) if all_thresholds_observed else None
        ),
        "heldout_mediator_90_range": (
            max(mediators) - min(mediators) if all_thresholds_observed else None
        ),
        "transformed_curve_collapse": collapse,
        "registration_boundary": (
            "This is a prospective held-out transformation test inside a frozen reduced "
            "cross-scale bridge. It is not an ab initio atom-to-cell calculation or an "
            "empirical biological confirmation."
        ),
    }


def result_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Experiment 011 registered results",
        "",
        f"Decision: **`{summary['decision']}`**",
        "",
        f"Gates passed: `{summary['gates_passed']}/{summary['gates_total']}`",
        "",
        "## Held-out predictions",
        "",
        "| Family | q | Predicted lambda_90 | Observed lambda_90 | Observed mediator_90 |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in summary["family_results"].items():
        lines.append(
            f"| {name} | {result['parameters']['bridge_exponent']} | "
            f"{result['predicted_lambda_90']:.9f} | {result['lambda_90']} | "
            f"{result['mediator_90']} |"
        )
    lines.extend([
        "",
        "## Registered gates",
        "",
    ])
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in summary["gates"].items())
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        summary["registration_boundary"],
        "",
    ])
    return "\n".join(lines)


def write_results(summary: dict[str, Any], receipt: dict[str, Any]) -> None:
    RESULTS.mkdir()
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (RESULTS / "RESULT.md").write_text(result_report(summary))
    (RESULTS / "registration_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    with (RESULTS / "survival_curves.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family", "bridge_exponent", "coupling", "mediator", "survival_fraction"])
        for name, result in summary["family_results"].items():
            q = result["parameters"]["bridge_exponent"]
            for coupling, fraction in result["survival_curve"].items():
                value = float(coupling)
                writer.writerow([name, q, coupling, value ** (2.0 * q), fraction])
    execution_note = {
        "schema": "siel-e011-execution-note-v1",
        "single_registered_execution_count": 1,
        "registration_commit": receipt["commit"],
        "registration_tag": receipt["tag"],
        "registration_doi": receipt["doi"],
        "python": platform.python_version(),
        "numpy": np.__version__,
        "target_families": [asdict(item) for item in TARGET_FAMILIES],
        "reruns_or_result_informed_repairs": 0,
    }
    (RESULTS / "EXECUTION_NOTE.json").write_text(
        json.dumps(execution_note, indent=2, sort_keys=True) + "\n"
    )
    result_files = [
        "EXECUTION_NOTE.json",
        "RESULT.md",
        "registration_receipt.json",
        "summary.json",
        "survival_curves.csv",
    ]
    result_manifest = {
        "schema": "siel-experiment-011-result-v1",
        "experiment": summary["experiment"],
        "decision": summary["decision"],
        "gates_passed": summary["gates_passed"],
        "gates_total": summary["gates_total"],
        "single_registered_execution_count": 1,
        "registration": receipt,
        "result_release_tag": RESULT_TAG,
        "zenodo_doi": None,
        "result_sha256": {name: sha256(RESULTS / name) for name in result_files},
    }
    (RESULTS / "result_manifest.json").write_text(
        json.dumps(result_manifest, indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-registration", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--registration-receipt", type=Path)
    args = parser.parse_args()
    if args.validate_registration == args.execute:
        parser.error("choose exactly one of --validate-registration or --execute")
    validation = validate_registration()
    if args.validate_registration:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return
    if args.registration_receipt is None:
        parser.error("--execute requires --registration-receipt")
    if RESULTS.exists():
        raise RuntimeError("results directory already exists; registered execution is single-use")
    receipt = validate_receipt(args.registration_receipt)
    summary = evaluate()
    write_results(summary, receipt)
    print(json.dumps({
        "decision": summary["decision"],
        "gates": summary["gates"],
        "heldout_raw_lambda_90_range": summary["heldout_raw_lambda_90_range"],
        "heldout_mediator_90_range": summary["heldout_mediator_90_range"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
