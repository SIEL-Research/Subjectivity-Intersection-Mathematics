"""Frozen reduced JCVI-syn3A-anchored dynamics for Experiment 009."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SOURCE_COMMIT = "db048aca5fe85438e0129819bbf0314b037dd931"
SOURCE_FILES = {
    "CME_ODE/model_data/GlobalParameters_Zane-TB-DB.csv":
        "1745c8590b76489ab9d5f923eacb59151a11fccbaea76f4cfa81066a940ec783",
    "CME_ODE/model_data/Central_AA_Zane_Balanced_direction_fixed_nounqATP.tsv":
        "3b86daa5d789be833e9fb8e9987cc603b03bc74510aaddc2f66db42322fcc413",
    "CME_ODE/model_data/lipid_NoH2O_balanced_model.tsv":
        "b09eee8d8a8fbff4024e138eab2a7c827529abc8bbc8c7f4821bd95c00024fc3",
    "CME_ODE/model_data/membrane_protein_metabolites.csv":
        "325f2e5313a49c3f3f52560f90464dfa057836f5280d911230a4b6a6915fb041",
}

STATE_NAMES = (
    "boundary_integrity",
    "nutrient_pool",
    "atp_pool",
    "expression_capacity",
    "repair_capacity",
    "damage_load",
    "biomass",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_and_read_anchors(root: Path) -> dict:
    for relative, expected in SOURCE_FILES.items():
        actual = file_sha256(root / relative)
        if actual != expected:
            raise ValueError(f"source hash mismatch for {relative}: {actual}")

    globals_path = root / "CME_ODE/model_data/GlobalParameters_Zane-TB-DB.csv"
    with globals_path.open() as handle:
        globals_rows = list(csv.DictReader(handle))
    by_key = {row["FormKey"]: row for row in globals_rows}
    glucose_mm = float(by_key["M_glc__D_e"]["parVal"])
    radius_m = float(by_key["r_cell"]["parVal"])

    def initial_concentration(path: Path, compound: str) -> float:
        in_compounds = False
        for line in path.read_text().splitlines():
            if "TableType='Compound'" in line:
                in_compounds = True
                continue
            if in_compounds and line.startswith("!!SBtab"):
                break
            if in_compounds and line.startswith(compound + "\t"):
                fields = line.split("\t")
                return float(fields[5])
        raise ValueError(f"compound not found: {compound}")

    central_atp = initial_concentration(
        root / "CME_ODE/model_data/Central_AA_Zane_Balanced_direction_fixed_nounqATP.tsv",
        "M_atp_c",
    )
    lipid_atp = initial_concentration(
        root / "CME_ODE/model_data/lipid_NoH2O_balanced_model.tsv", "M_atp_c"
    )
    membrane_path = root / "CME_ODE/model_data/membrane_protein_metabolites.csv"
    with membrane_path.open() as handle:
        membrane_rows = list(csv.DictReader(handle))
    membrane_genes = sorted({row["gene"] for row in membrane_rows})
    return {
        "external_glucose_mm": glucose_mm,
        "cell_radius_m": radius_m,
        "central_atp_initial_mm": central_atp,
        "lipid_atp_initial_mm": lipid_atp,
        "atp_scale_mm": (central_atp + lipid_atp) / 2.0,
        "membrane_gene_count": len(membrane_genes),
    }


@dataclass(frozen=True)
class DynamicsConfig:
    dt_minutes: float = 0.02
    duration_minutes: float = 150.0
    damage_start_minutes: float = 40.0
    damage_end_minutes: float = 43.0
    moderate_damage_amplitude: float = 0.60
    severe_damage_amplitude: float = 1.20
    shift_minutes: float = 10.0
    reinjection_minutes: float = 50.0
    death_boundary: float = 0.05
    death_atp: float = 0.03
    death_expression: float = 0.05


def saturating(value: float, half: float = 0.5) -> float:
    """Dimensionless saturation normalized to one at value=1."""
    value = max(value, 0.0)
    return value / (half + value) * (half + 1.0)


def joint_gate(x: float, y: float, erase_joint: bool) -> float:
    """Bilinear gate or its inclusion-exclusion joint-erased counterpart."""
    if erase_joint:
        return max(0.0, x + y - 1.0)
    return max(0.0, x * y)


def module_observables(states: np.ndarray) -> np.ndarray:
    boundary = np.maximum(states[..., 0], 0.0)
    metabolic = np.sqrt(
        np.maximum(saturating_array(states[..., 1]), 0.0)
        * np.maximum(saturating_array(states[..., 2]), 0.0)
    )
    information_repair = np.sqrt(
        np.maximum(states[..., 3], 0.0)
        * np.maximum(saturating_array(states[..., 4], 0.25), 0.0)
    )
    return np.stack((boundary, metabolic, information_repair), axis=-1)


def saturating_array(values: np.ndarray, half: float = 0.5) -> np.ndarray:
    values = np.maximum(values, 0.0)
    return values / (half + values) * (half + 1.0)


def simulate(
    seed: int,
    config: DynamicsConfig,
    condition: str = "native",
    damage_amplitude: float | None = None,
) -> dict:
    if condition not in {"native", "joint_erased", "time_shifted", "reinjected", "nonliving"}:
        raise ValueError(condition)
    amplitude = (
        config.moderate_damage_amplitude if damage_amplitude is None else damage_amplitude
    )
    rng = np.random.default_rng(seed)
    dt = config.dt_minutes
    steps = int(round(config.duration_minutes / dt)) + 1
    times = np.arange(steps) * dt
    states = np.zeros((steps, len(STATE_NAMES)), dtype=float)
    initial_noise = rng.normal(0.0, [0.01, 0.02, 0.02, 0.01, 0.01, 0.002, 0.0])
    states[0] = np.array([1.0, 1.0, 1.0, 1.0, 0.45, 0.02, 1.0]) + initial_noise
    divisions = 0
    death_time = None

    for index in range(steps - 1):
        time = times[index]
        B, N, A, G, R, D, X = np.maximum(
            states[index], [0.001, 0.001, 0.001, 0.001, 0.001, 0.0, 0.1]
        )
        pulse = amplitude if config.damage_start_minutes <= time < config.damage_end_minutes else 0.0
        erase = condition == "joint_erased" and time >= config.damage_start_minutes
        if condition == "reinjected" and config.damage_start_minutes <= time < config.reinjection_minutes:
            erase = True

        if condition == "time_shifted" and time >= config.damage_start_minutes:
            lag = int(round(config.shift_minutes / dt))
            shifted_index = max(0, index - lag)
            Bs, Ns, As, Gs, Rs, Ds, _ = np.maximum(
                states[shifted_index], [0.001, 0.001, 0.001, 0.001, 0.001, 0.0, 0.1]
            )
            uptake = 0.90 * B * Gs
            catabolism = 0.75 * G * saturating(Ns)
            expression = 0.32 * B * saturating(As) * saturating(N)
            lipid_synthesis = 0.28 * G * saturating(As) * saturating(N)
            repair = 0.65 * R * saturating(As) * saturating(D, 0.12)
        else:
            uptake = 0.90 * joint_gate(B, G, erase)
            catabolism = 0.75 * joint_gate(G, saturating(N), erase)
            expression = 0.32 * joint_gate(B, saturating(A), erase) * saturating(N)
            lipid_synthesis = 0.28 * joint_gate(G, saturating(A), erase) * saturating(N)
            repair = 0.65 * joint_gate(R, saturating(A), erase) * saturating(D, 0.12)

        if condition == "nonliving":
            repair = 0.0
            expression *= 0.55
            lipid_synthesis *= 0.55

        derivative = np.array(
            [
                lipid_synthesis * (1.15 - B) + 0.35 * repair - 0.055 * B - pulse * 0.90 * B,
                uptake - catabolism - 0.12 * expression - 0.12 * lipid_synthesis - 0.05 * N,
                1.15 * catabolism - 0.55 * expression - 0.55 * lipid_synthesis - 0.75 * repair - 0.28 * A,
                expression * (1.15 - G) - (0.035 + 0.18 * D + 0.35 * pulse) * G,
                0.70 * expression * saturating(D, 0.15) * (1.20 - R) - 0.08 * R,
                0.008 + pulse * (0.35 + 0.65 * B) - repair - 0.035 * D,
                (0.009 * (expression + lipid_synthesis) - 0.012 * D) * X,
            ]
        )
        noise = np.concatenate(
            (rng.normal(0.0, 0.0008, 5), [rng.normal(0.0, 0.00025), 0.0])
        )
        states[index + 1] = states[index] + dt * derivative + np.sqrt(dt) * noise
        states[index + 1, :6] = np.maximum(states[index + 1, :6], 0.0)
        if condition != "nonliving" and states[index + 1, 6] >= 2.0:
            states[index + 1, 6] /= 2.0
            divisions += 1
        if B < config.death_boundary or A < config.death_atp or G < config.death_expression:
            death_time = time
            states[index + 1 :] = states[index + 1]
            break

    modules = module_observables(states)
    pre = (times >= 32.0) & (times < config.damage_start_minutes)
    late = times >= 100.0
    pre_level = np.median(modules[pre], axis=0)
    late_level = np.median(modules[late], axis=0)
    recovery_ratio = late_level / np.maximum(pre_level, 1e-12)
    alive = bool(
        death_time is None
        and np.all(recovery_ratio >= 0.80)
        and np.median(states[late, 5]) < 0.10
    )
    return {
        "seed": seed,
        "condition": condition,
        "damage_amplitude": amplitude,
        "times": times,
        "states": states,
        "modules": modules,
        "divisions": divisions,
        "death_time": death_time,
        "alive": alive,
        "pre_level": pre_level,
        "late_level": late_level,
        "recovery_ratio": recovery_ratio,
    }


def fit_cross_mode(lineages: list[dict], config: DynamicsConfig, lag_minutes: float = 1.0) -> dict:
    lag = int(round(lag_minutes / config.dt_minutes))
    x_parts, y_parts = [], []
    for lineage in lineages:
        times = lineage["times"]
        modules = lineage["modules"]
        window = (times >= 35.0) & (times <= 85.0 - lag_minutes)
        indices = np.flatnonzero(window)
        x_parts.append(modules[indices])
        y_parts.append(modules[indices + lag] - modules[indices])
    x = np.vstack(x_parts)
    y = np.vstack(y_parts)
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-8] = 1.0
    xs = (x - mean) / scale
    ys = y / scale
    design = np.column_stack((np.ones(len(xs)), xs))
    coefficients, *_ = np.linalg.lstsq(design, ys, rcond=None)
    transition = coefficients[1:].T
    cross = np.abs(transition.copy())
    np.fill_diagonal(cross, 0.0)
    eigenvalues, eigenvectors = np.linalg.eig(cross)
    selected = int(np.argmax(eigenvalues.real))
    mode = np.abs(eigenvectors[:, selected].real)
    mode /= np.linalg.norm(mode)
    participation = float(1.0 / np.sum(mode**4))
    return {
        "mean": mean,
        "scale": scale,
        "transition": transition,
        "cross_matrix": cross,
        "mode": mode,
        "eigenvalue": float(eigenvalues[selected].real),
        "participation_ratio": participation,
    }


def predictor_scores(training: list[dict], testing: list[dict], config: DynamicsConfig, lag_minutes: float = 1.0) -> dict:
    lag = int(round(lag_minutes / config.dt_minutes))

    def samples(lineages):
        xp, yp = [], []
        for lineage in lineages:
            times = lineage["times"]
            z = lineage["modules"]
            idx = np.flatnonzero((times >= 35.0) & (times <= 85.0 - lag_minutes))
            xp.append(z[idx])
            yp.append(z[idx + lag] - z[idx])
        return np.vstack(xp), np.vstack(yp)

    train_x, train_y = samples(training)
    test_x, test_y = samples(testing)
    mean, scale = train_x.mean(0), train_x.std(0)
    scale[scale < 1e-8] = 1.0
    train_x = (train_x - mean) / scale
    test_x = (test_x - mean) / scale
    train_y, test_y = train_y / scale, test_y / scale
    full_train = np.column_stack((np.ones(len(train_x)), train_x))
    full_test = np.column_stack((np.ones(len(test_x)), test_x))
    full_coef, *_ = np.linalg.lstsq(full_train, train_y, rcond=None)
    full_pred = full_test @ full_coef
    component_scores = []
    for component in range(3):
        self_train = np.column_stack((np.ones(len(train_x)), train_x[:, component]))
        self_test = np.column_stack((np.ones(len(test_x)), test_x[:, component]))
        self_coef, *_ = np.linalg.lstsq(self_train, train_y[:, component], rcond=None)
        self_pred = self_test @ self_coef
        target = test_y[:, component]
        denominator = float(np.sum((target - target.mean()) ** 2))
        full_r2 = 1.0 - float(np.sum((target - full_pred[:, component]) ** 2)) / denominator
        self_r2 = 1.0 - float(np.sum((target - self_pred) ** 2)) / denominator
        component_scores.append(
            {"component": component, "full_r2": full_r2, "self_r2": self_r2, "cross_gain": full_r2 - self_r2}
        )
    return {
        "component_scores": component_scores,
        "minimum_cross_gain": min(item["cross_gain"] for item in component_scores),
        "mean_cross_gain": float(np.mean([item["cross_gain"] for item in component_scores])),
    }
