#!/usr/bin/env python3
"""Generate the target-free E008D potassium mixed-rank prediction."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import warnings
from pathlib import Path

import numpy as np
from pyscf import gto, scf
from pyscf.data import nist
from pyscf.scf import addons

warnings.filterwarnings("ignore", message="Module .* is under testing")
warnings.filterwarnings("ignore", message="Module infrared is not fully tested")

from pyscf.prop.efg import rhf as rhf_efg  # noqa: E402


ROOT = Path(__file__).resolve().parent
PROPERTIES_SOURCE_COMMIT = "4eee5a430fb47eca5962f36fdcaf75c2b87e7ede"
BASIS_CONFIGURATIONS = (
    ("contracted-def2-TZVPP", "def2-TZVPP", False),
    ("contracted-def2-QZVPP", "def2-QZVPP", False),
    ("uncontracted-def2-TZVPP", "def2-TZVPP", True),
    ("uncontracted-def2-QZVPP", "def2-QZVPP", True),
)
CONSTRUCTION = json.loads(
    (ROOT / "construction_sources.json").read_text(encoding="utf-8")
)
ISOTOPES = CONSTRUCTION["nuclear_inputs"]


def _basis(name: str, decontract: bool) -> object:
    if not decontract:
        return name
    return {"K": gto.uncontract(gto.basis.load(name, "K"))}


def _mulliken_population(
    coefficients: np.ndarray, overlap: np.ndarray, indices: list[int]
) -> float:
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        value = np.einsum(
            "i,i->", coefficients[indices], (overlap @ coefficients)[indices]
        )
    return float(value)


def _lowest_pz_candidate(mean_field: object) -> int:
    """Choose one orientation from the lowest virtual P manifold."""
    molecule = mean_field.mol
    labels = molecule.ao_labels()
    overlap = molecule.intor_symmetric("int1e_ovlp")
    alpha_occupation = np.asarray(mean_field.mo_occ[0])
    virtual = np.flatnonzero(alpha_occupation == 0.0)
    p_indices = [index for index, label in enumerate(labels) if "p" in label.split()[2]]
    pz_indices = [index for index, label in enumerate(labels) if "pz" in label]
    candidates = []
    for orbital_index in virtual:
        coefficients = np.asarray(mean_field.mo_coeff[0][:, orbital_index])
        energy = float(mean_field.mo_energy[0][orbital_index])
        if (
            not np.isfinite(energy)
            or energy > 5.0
            or not np.all(np.isfinite(coefficients))
            or float(np.max(np.abs(coefficients))) > 1e50
        ):
            continue
        p_weight = _mulliken_population(coefficients, overlap, p_indices)
        if p_weight > 0.5:
            pz_weight = _mulliken_population(coefficients, overlap, pz_indices)
            candidates.append(
                (
                    energy,
                    -pz_weight,
                    int(orbital_index),
                )
            )
    if not candidates:
        raise RuntimeError("no virtual P orbital with Mulliken weight above 0.5")
    candidates.sort()
    lowest_energy = candidates[0][0]
    manifold = [row for row in candidates if abs(row[0] - lowest_energy) < 1e-6]
    return min(manifold, key=lambda row: row[1])[2]


def _axial_vector_state_scalar(tensor: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh(tensor)
    trace_error = abs(float(np.trace(tensor)))
    if trace_error > 1e-7:
        raise RuntimeError("rank-two tensor trace error %.6g" % trace_error)
    return 2.5 * float(eigenvalues[0])


def _electronic_xy(coordinates: dict[str, float]) -> dict[str, float]:
    electron_g = float(nist.G_ELECTRON)
    return {
        "x_magnetic_scalar": (
            electron_g / 6.0 * coordinates["contact_scalar"]
            + coordinates["orbital_scalar"] / 4.0
            - electron_g / 16.0 * coordinates["spin_dipole_scalar"]
        ),
        "y_electric_scalar": -3.0 / 5.0 * coordinates["electric_quadrupole_scalar"],
    }


def _isotope_kernel(isotope: dict[str, float], xy: dict[str, float]) -> dict[str, float]:
    spin = isotope["nuclear_spin_I"]
    moment = isotope["magnetic_moment_mu_N"]
    quadrupole = isotope["quadrupole_moment_barn"]
    proton_electron_mass_ratio = float(nist.PROTON_MASS / nist.E_MASS)
    barn_in_compton_squared = float(1e-28 / nist.BOHR_SI**2 / nist.ALPHA**2)
    x_value = moment / (spin * proton_electron_mass_ratio) * xy["x_magnetic_scalar"]
    y_value = quadrupole * barn_in_compton_squared * xy["y_electric_scalar"]
    m1_m1 = -2.0 / 9.0 * x_value**2
    m1_e2 = (2.0 * spin + 3.0) / (9.0 * spin) * x_value * y_value
    return {
        "X_without_common_energy_scale": x_value,
        "Y_without_common_energy_scale": y_value,
        "m1_m1_kernel": m1_m1,
        "m1_e2_kernel": m1_e2,
        "full_kernel": m1_m1 + m1_e2,
    }


def calculate_basis(label: str, basis_name: str, decontract: bool) -> dict[str, object]:
    molecule = gto.M(
        atom="K 0 0 0",
        basis=_basis(basis_name, decontract),
        charge=0,
        spin=1,
        symmetry=False,
        verbose=0,
    )
    ground = scf.UHF(molecule)
    ground.conv_tol = 1e-10
    ground.max_cycle = 150
    ground.kernel()
    if not ground.converged:
        raise RuntimeError("ground-state SCF did not converge for %s" % label)

    p_index = _lowest_pz_candidate(ground)
    alpha_occupation = np.asarray(ground.mo_occ[0]).copy()
    beta_occupation = np.asarray(ground.mo_occ[1]).copy()
    alpha_homo = int(np.flatnonzero(alpha_occupation > 0.0)[-1])
    alpha_occupation[alpha_homo] = 0.0
    alpha_occupation[p_index] = 1.0
    excited_occupation = np.asarray((alpha_occupation, beta_occupation))

    excited = scf.UHF(molecule)
    excited.conv_tol = 1e-10
    excited.max_cycle = 150
    addons.mom_occ_(excited, ground.mo_coeff, excited_occupation)
    initial_density = excited.make_rdm1(ground.mo_coeff, excited_occupation)
    excited.kernel(dm0=initial_density)
    if not excited.converged:
        raise RuntimeError("excited-state SCF did not converge for %s" % label)

    density = np.asarray(excited.make_rdm1(), dtype=float)
    spin_density = density[0] - density[1]
    total_density = density[0] + density[1]
    ao_at_nucleus = np.asarray(
        molecule.eval_gto("GTOval", molecule.atom_coord(0).reshape(1, 3))[0],
        dtype=float,
    )
    contact = float(
        4.0 * math.pi * np.einsum("i,ij,j->", ao_at_nucleus, spin_density, ao_at_nucleus)
    )
    rank_two_ao = -np.asarray(rhf_efg._get_quadrupole_integrals(molecule, 0))
    spin_tensor = np.einsum("abij,ji->ab", rank_two_ao, spin_density)
    electric_tensor = np.einsum("abij,ji->ab", rank_two_ao, total_density)

    occupied_alpha = np.flatnonzero(excited.mo_occ[0] > 0.0)
    valence_index = int(occupied_alpha[np.argmax(excited.mo_energy[0][occupied_alpha])])
    valence_orbital = excited.mo_coeff[0][:, valence_index]
    valence_density = np.outer(valence_orbital, valence_orbital)
    orbital_tensor = np.einsum("abij,ji->ab", rank_two_ao, valence_density)
    coordinates = {
        "contact_scalar": contact,
        "spin_dipole_scalar": _axial_vector_state_scalar(spin_tensor),
        "orbital_scalar": _axial_vector_state_scalar(orbital_tensor),
        "electric_quadrupole_scalar": _axial_vector_state_scalar(electric_tensor),
    }
    xy = _electronic_xy(coordinates)
    kernels = {name: _isotope_kernel(row, xy) for name, row in ISOTOPES.items()}
    full_ratio = kernels["K-39"]["full_kernel"] / kernels["K-41"]["full_kernel"]
    m1_ratio = kernels["K-39"]["m1_m1_kernel"] / kernels["K-41"]["m1_m1_kernel"]
    spin_square, multiplicity = excited.spin_square()
    return {
        "basis_label": label,
        "basis_name": basis_name,
        "decontracted": decontract,
        "number_of_atomic_orbitals": int(molecule.nao),
        "ground_scf_converged": bool(ground.converged),
        "excited_scf_converged": bool(excited.converged),
        "spin_square": float(spin_square),
        "spin_multiplicity": float(multiplicity),
        "promoted_alpha_orbital": alpha_homo,
        "selected_p_orbital": p_index,
        "electronic_coordinates": coordinates,
        "electronic_xy_scalars": xy,
        "isotope_kernels": kernels,
        "m1_only_ratio_k39_over_k41": m1_ratio,
        "mixed_rank_ratio_k39_over_k41": full_ratio,
    }


def generate() -> dict[str, object]:
    rows = [calculate_basis(*configuration) for configuration in BASIS_CONFIGURATIONS]
    by_label = {row["basis_label"]: row for row in rows}
    primary = by_label["uncontracted-def2-QZVPP"]
    secondary = by_label["uncontracted-def2-TZVPP"]
    basis_log_change = abs(
        math.log(
            secondary["mixed_rank_ratio_k39_over_k41"]
            / primary["mixed_rank_ratio_k39_over_k41"]
        )
    )
    return {
        "schema": "siel-e008d-prediction-before-benchmark-v1",
        "experiment": "008d_pyscf_potassium_mixed_rank_prediction",
        "target_values_loaded": False,
        "free_fitted_parameters": 0,
        "primary_target": "full_second_order_delta_A_p1_2_ratio_k39_over_k41",
        "electronic_system": "neutral potassium lowest 4P state",
        "method": "maximum-overlap unrestricted Hartree-Fock",
        "software": {
            "pyscf_version": importlib.metadata.version("pyscf"),
            "pyscf_properties_version": importlib.metadata.version("pyscf-properties"),
            "pyscf_properties_source_commit": PROPERTIES_SOURCE_COMMIT,
        },
        "isotope_inputs": ISOTOPES,
        "basis_calculations": rows,
        "primary_basis": "uncontracted-def2-QZVPP",
        "primary_prediction": primary["mixed_rank_ratio_k39_over_k41"],
        "m1_only_control": primary["m1_only_ratio_k39_over_k41"],
        "uncontracted_tz_qz_log_change": basis_log_change,
        "uncontracted_tz_qz_log_change_ppm": basis_log_change * 1e6,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = generate()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")
        print(json.dumps({
            "output": str(args.output),
            "primary_prediction": result["primary_prediction"],
            "m1_only_control": result["m1_only_control"],
            "basis_log_change_ppm": result["uncontracted_tz_qz_log_change_ppm"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
