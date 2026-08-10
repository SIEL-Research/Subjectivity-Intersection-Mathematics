#!/usr/bin/env python3
"""Experiment 010 frozen complete-molecular-carrier transfer runner."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from pyscf import ao2mo, fci, gto

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"
TARGET_REGISTRY = ROOT / "target_registry.json"
RESIDUAL_SECTORS = (
    "cross_eri",
    "other_nucleus_local",
    "nuclear_repulsion",
    "local_deformation",
)
ALL_SECTORS = ("one_electron_cross",) + RESIDUAL_SECTORS


class ProvenanceError(RuntimeError):
    """Raised when registration or execution provenance is invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def verify_registration() -> tuple[dict, dict]:
    manifest = load_json(MANIFEST)
    target = load_json(TARGET_REGISTRY)
    if manifest.get("schema") != "siel-experiment-010-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_execution_performed") is not False:
        raise ProvenanceError("registration declares prior target execution")
    if target.get("schema") != "siel-e010-target-registry-v1":
        raise ProvenanceError("target registry schema mismatch")
    if target.get("target_execution_performed") is not False:
        raise ProvenanceError("target registry declares prior execution")
    expected = manifest.get("source_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ProvenanceError("registration source hashes missing")
    for relative, frozen_hash in sorted(expected.items()):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ProvenanceError("missing registered source: %s" % relative)
        if sha256_file(path) != frozen_hash:
            raise ProvenanceError("registered source hash mismatch: %s" % relative)
    return manifest, target


def validate_receipt(path: Path) -> dict:
    receipt = load_json(path)
    required = {"schema", "tag", "commit", "release_url", "doi"}
    if set(receipt) != required:
        raise ProvenanceError("registration receipt fields mismatch")
    if receipt["schema"] != "siel-e010-registration-receipt-v1":
        raise ProvenanceError("registration receipt schema mismatch")
    if receipt["tag"] != "e010-preregistration-v1.0.0":
        raise ProvenanceError("registration receipt tag mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", receipt["commit"]):
        raise ProvenanceError("registration receipt commit is not a full SHA")
    expected_suffix = "/releases/tag/e010-preregistration-v1.0.0"
    if not receipt["release_url"].startswith("https://github.com/") or not receipt[
        "release_url"
    ].endswith(expected_suffix):
        raise ProvenanceError("registration receipt release URL mismatch")
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", receipt["doi"]):
        raise ProvenanceError("registration receipt DOI mismatch")
    return receipt


def matmul_checked(*arrays: np.ndarray) -> np.ndarray:
    result = arrays[0]
    for array in arrays[1:]:
        result = np.matmul(result, array)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("non-finite matrix product")
    return result


def symmetric_orthogonalizer(overlap: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(overlap)
    if float(np.min(values)) <= 1e-9:
        raise ValueError("AO overlap is numerically singular")
    return matmul_checked(vectors * values**-0.5, vectors.T)


def rotate_eri(eri: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    return ao2mo.restore(
        1, ao2mo.incore.full(eri, rotation), rotation.shape[0]
    )


def rectangle_geometry(a: float, b: float) -> str:
    if not (math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0):
        raise ValueError("rectangle dimensions must be finite and positive")
    return (
        f"H {-a / 2} {-b / 2} 0; H {a / 2} {-b / 2} 0; "
        f"H {a / 2} {b / 2} 0; H {-a / 2} {b / 2} 0"
    )


@lru_cache(maxsize=None)
def isolated_atom_terms(basis: str) -> tuple[np.ndarray, np.ndarray]:
    atom = gto.M(
        atom="H 0 0 0", basis=basis, unit="Angstrom", charge=0, spin=1, verbose=0
    )
    transform = symmetric_orthogonalizer(atom.intor("int1e_ovlp"))
    h_ao = atom.intor("int1e_kin") + atom.intor("int1e_nuc")
    h1 = matmul_checked(transform.T, h_ao, transform)
    eri = ao2mo.restore(
        1,
        ao2mo.incore.full(atom.intor("int2e"), transform),
        atom.nao,
    )
    return h1, eri


def build_target(basis: str, a: float, b: float) -> dict:
    molecule = gto.M(
        atom=rectangle_geometry(a, b),
        basis=basis,
        unit="Angstrom",
        charge=1,
        spin=1,
        verbose=0,
    )
    transform = symmetric_orthogonalizer(molecule.intor("int1e_ovlp"))
    kinetic = matmul_checked(transform.T, molecule.intor("int1e_kin"), transform)
    nuclear_parts = []
    for centre in range(4):
        with molecule.with_rinv_origin(molecule.atom_coord(centre)):
            potential_ao = -molecule.atom_charge(centre) * molecule.intor(
                "int1e_rinv"
            )
        nuclear_parts.append(matmul_checked(transform.T, potential_ao, transform))
    h_full = kinetic + sum(nuclear_parts)
    eri_full = ao2mo.restore(
        1,
        ao2mo.incore.full(molecule.intor("int2e"), transform),
        molecule.nao,
    )
    centres = np.array([label[0] for label in molecule.ao_labels(fmt=False)], dtype=int)
    indices = [np.flatnonzero(centres == centre) for centre in range(4)]
    projectors = [np.diag((centres == centre).astype(float)) for centre in range(4)]

    atomic_h, atomic_eri = isolated_atom_terms(basis)
    h_isolated = np.zeros_like(h_full)
    eri_isolated = np.zeros_like(eri_full)
    for centre_indices in indices:
        h_isolated[np.ix_(centre_indices, centre_indices)] = atomic_h
        eri_isolated[
            np.ix_(centre_indices, centre_indices, centre_indices, centre_indices)
        ] = atomic_eri

    edge_carriers = {}
    for left, right in itertools.combinations(range(4), 2):
        edge_carriers[(left, right)] = matmul_checked(
            projectors[left], h_full, projectors[right]
        ) + matmul_checked(projectors[right], h_full, projectors[left])
    h_block_full = h_full - sum(edge_carriers.values())
    h_own = sum(
        (
            matmul_checked(
                projectors[centre],
                kinetic + nuclear_parts[centre],
                projectors[centre],
            )
            for centre in range(4)
        ),
        np.zeros_like(h_full),
    )
    eri_local = np.zeros_like(eri_full)
    for centre_indices in indices:
        block = np.ix_(centre_indices, centre_indices, centre_indices, centre_indices)
        eri_local[block] = eri_full[block]
    zeros_h = np.zeros_like(h_full)
    zeros_eri = np.zeros_like(eri_full)
    components = {
        "one_electron_cross": (sum(edge_carriers.values()), zeros_eri, 0.0),
        "cross_eri": (zeros_h, eri_full - eri_local, 0.0),
        "other_nucleus_local": (h_block_full - h_own, zeros_eri, 0.0),
        "nuclear_repulsion": (
            zeros_h,
            zeros_eri,
            float(molecule.energy_nuc()),
        ),
        "local_deformation": (
            h_own - h_isolated,
            eri_local - eri_isolated,
            0.0,
        ),
    }
    return {
        "basis": basis,
        "a": a,
        "b": b,
        "molecule": molecule,
        "indices": indices,
        "h_full": h_full,
        "eri_full": eri_full,
        "core_full": float(molecule.energy_nuc()),
        "h_isolated": h_isolated,
        "eri_isolated": eri_isolated,
        "components": components,
        "edge_carriers": edge_carriers,
    }


def terms_for_mode(built: dict, mode: str) -> tuple[np.ndarray, np.ndarray, float]:
    if mode == "full":
        return built["h_full"], built["eri_full"], built["core_full"]
    if mode == "isolated":
        return built["h_isolated"], built["eri_isolated"], 0.0
    if mode == "one_electron_cross_deleted":
        delta_h = built["components"]["one_electron_cross"][0]
        return built["h_full"] - delta_h, built["eri_full"], built["core_full"]
    if mode == "without_edge_01":
        return (
            built["h_full"] - built["edge_carriers"][(0, 1)],
            built["eri_full"],
            built["core_full"],
        )
    raise ValueError("unknown mode: %s" % mode)


def fci_solution(
    built: dict, mode: str
) -> tuple[float, np.ndarray, np.ndarray]:
    h1, eri, core = terms_for_mode(built, mode)
    norb = h1.shape[0]
    energy, ci = fci.direct_spin1.kernel(
        h1,
        eri,
        norb,
        built["molecule"].nelec,
        ecore=core,
        tol=1e-12,
        verbose=0,
    )
    rdm1 = fci.direct_spin1.make_rdm1(ci, norb, built["molecule"].nelec)
    return float(energy), ci, rdm1


def centre_populations(built: dict, rdm1: np.ndarray) -> list[float]:
    return [float(np.trace(rdm1[np.ix_(indices, indices)])) for indices in built["indices"]]


def reconstruction_errors(built: dict) -> dict:
    h1 = built["h_isolated"].copy()
    eri = built["eri_isolated"].copy()
    core = 0.0
    for sector in ALL_SECTORS:
        delta_h, delta_eri, delta_core = built["components"][sector]
        h1 += delta_h
        eri += delta_eri
        core += delta_core
    return {
        "h1_max_abs": float(np.max(np.abs(h1 - built["h_full"]))),
        "eri_max_abs": float(np.max(np.abs(eri - built["eri_full"]))),
        "core_abs": abs(core - built["core_full"]),
    }


def transformed_energy(built: dict, mode: str, rotation: np.ndarray) -> float:
    h1, eri, core = terms_for_mode(built, mode)
    rotated_h = matmul_checked(rotation.T, h1, rotation)
    rotated_eri = rotate_eri(eri, rotation)
    value, _ = fci.direct_spin1.kernel(
        rotated_h,
        rotated_eri,
        rotated_h.shape[0],
        built["molecule"].nelec,
        ecore=core,
        tol=1e-12,
        verbose=0,
    )
    return float(value)


def representation_audit(built: dict, rotation_seeds: list[int]) -> list[dict]:
    rotations = [("identity", np.eye(built["h_full"].shape[0]))]
    _, eigenvectors = np.linalg.eigh(built["h_full"])
    rotations.append(("hamiltonian_eigenbasis", eigenvectors))
    for seed in rotation_seeds:
        raw = np.random.default_rng(seed).normal(size=built["h_full"].shape)
        q, _ = np.linalg.qr(raw)
        rotations.append(("random_%d" % seed, q))
    rows = []
    for name, rotation in rotations:
        full_h = matmul_checked(rotation.T, built["h_full"], rotation)
        iso_h = matmul_checked(rotation.T, built["h_isolated"], rotation)
        full_eri = rotate_eri(built["eri_full"], rotation)
        iso_eri = rotate_eri(built["eri_isolated"], rotation)
        offdiag = full_h - np.diag(np.diag(full_h))
        rows.append(
            {
                "representation": name,
                "full_energy_hartree": transformed_energy(built, "full", rotation),
                "isolated_energy_hartree": transformed_energy(built, "isolated", rotation),
                "edge_deleted_energy_hartree": transformed_energy(
                    built, "without_edge_01", rotation
                ),
                "complete_h1_carrier_norm": float(np.linalg.norm(full_h - iso_h)),
                "complete_eri_carrier_norm": float(np.linalg.norm(full_eri - iso_eri)),
                "naive_offdiagonal_h_norm": float(np.linalg.norm(offdiag)),
            }
        )
    return rows


def sector_energy(built: dict, sectors: frozenset[str]) -> float:
    h1 = built["h_isolated"].copy()
    eri = built["eri_isolated"].copy()
    core = 0.0
    for sector in sectors:
        delta_h, delta_eri, delta_core = built["components"][sector]
        h1 += delta_h
        eri += delta_eri
        core += delta_core
    value, _ = fci.direct_spin1.kernel(
        h1,
        eri,
        h1.shape[0],
        built["molecule"].nelec,
        ecore=core,
        tol=1e-12,
        verbose=0,
    )
    return float(value)


def residual_shapley(basis: str, near: tuple[float, float], far: tuple[float, float]):
    near_built = build_target(basis, *near)
    far_built = build_target(basis, *far)
    values = {}
    rows = []
    sectors = tuple(RESIDUAL_SECTORS)
    for count in range(len(sectors) + 1):
        for members in itertools.combinations(sectors, count):
            subset = frozenset(members)
            signal = sector_energy(far_built, subset) - sector_energy(near_built, subset)
            values[subset] = signal
            rows.append(
                {
                    "basis": basis,
                    "subset": "+".join(sorted(subset)) or "isolated",
                    "binding_signal_hartree": signal,
                }
            )
    shapley = {sector: 0.0 for sector in sectors}
    size = len(sectors)
    for sector in sectors:
        for subset, value in values.items():
            if sector in subset:
                continue
            n = len(subset)
            weight = math.factorial(n) * math.factorial(size - n - 1) / math.factorial(size)
            shapley[sector] += weight * (values[subset | {sector}] - value)
    total = values[frozenset(sectors)]
    return rows, {
        "residual_binding_signal_hartree": total,
        "shapley_hartree": shapley,
        "shapley_sum_error_hartree": abs(sum(shapley.values()) - total),
    }


def execute_registered_target(target: dict, receipt: dict) -> tuple[list, list, list, dict]:
    grid = target["shape_grid_angstrom"]
    values = np.arange(grid["minimum"], grid["maximum"] + grid["step"] / 2, grid["step"])
    far = tuple(target["dissociation_reference_angstrom"])
    thresholds = target["thresholds"]
    shape_rows = []
    audit_rows = []
    subset_rows = []
    profiles = {}
    for basis in target["basis_profiles"]:
        profile_rows = []
        for a in values:
            for b in values:
                built = build_target(basis, float(a), float(b))
                for mode in ("full", "one_electron_cross_deleted", "without_edge_01"):
                    energy, _, _ = fci_solution(built, mode)
                    row = {
                        "basis": basis,
                        "mode": mode,
                        "a_angstrom": float(a),
                        "b_angstrom": float(b),
                        "energy_hartree": energy,
                    }
                    shape_rows.append(row)
                    profile_rows.append(row)
        minima = {
            mode: min(
                (row for row in profile_rows if row["mode"] == mode),
                key=lambda row: row["energy_hartree"],
            )
            for mode in ("full", "one_electron_cross_deleted", "without_edge_01")
        }
        far_built = build_target(basis, *far)
        far_energies = {
            mode: fci_solution(far_built, mode)[0]
            for mode in ("full", "one_electron_cross_deleted")
        }
        full_depth = far_energies["full"] - minima["full"]["energy_hartree"]
        residual_depth = (
            far_energies["one_electron_cross_deleted"]
            - minima["one_electron_cross_deleted"]["energy_hartree"]
        )
        removed_fraction = 1.0 - residual_depth / full_depth if full_depth != 0 else float("nan")
        full_xy = (minima["full"]["a_angstrom"], minima["full"]["b_angstrom"])
        edge_xy = (
            minima["without_edge_01"]["a_angstrom"],
            minima["without_edge_01"]["b_angstrom"],
        )
        displacement = float(np.linalg.norm(np.subtract(edge_xy, full_xy)))
        full_built = build_target(basis, *full_xy)
        full_energy, _, full_rdm = fci_solution(full_built, "full")
        edge_energy, _, edge_rdm = fci_solution(full_built, "without_edge_01")
        full_pop = centre_populations(full_built, full_rdm)
        edge_pop = centre_populations(full_built, edge_rdm)
        population_changes = [abs(x - y) for x, y in zip(full_pop, edge_pop)]
        sample_points = ((0.7, 0.7), (1.2, 1.8), (2.5, 2.5), far)
        isolated_energies = [
            fci_solution(build_target(basis, *point), "isolated")[0]
            for point in sample_points
        ]
        isolated_range = max(isolated_energies) - min(isolated_energies)
        reconstruction = reconstruction_errors(full_built)
        audits = representation_audit(full_built, target["random_rotation_seeds"])
        for row in audits:
            audit_rows.append({"basis": basis, **row})
        reference = audits[0]
        representation_maximum = max(
            abs(row[field] - reference[field])
            for row in audits
            for field in (
                "full_energy_hartree",
                "isolated_energy_hartree",
                "edge_deleted_energy_hartree",
                "complete_h1_carrier_norm",
                "complete_eri_carrier_norm",
            )
        )
        eigenbasis = next(row for row in audits if row["representation"] == "hamiltonian_eigenbasis")
        profile_subsets, shapley = residual_shapley(
            basis,
            (
                minima["one_electron_cross_deleted"]["a_angstrom"],
                minima["one_electron_cross_deleted"]["b_angstrom"],
            ),
            far,
        )
        subset_rows.extend(profile_subsets)
        full_minimum_is_interior = not any(
            np.isclose(value, boundary)
            for value in (
                minima["full"]["a_angstrom"],
                minima["full"]["b_angstrom"],
            )
            for boundary in (grid["minimum"], grid["maximum"])
        )
        gates = {
            "exact_five_sector_reconstruction": max(reconstruction.values())
            < thresholds["maximum_reconstruction_error"],
            "finite_interior_full_binding": (
                full_depth > thresholds["minimum_full_binding_depth_hartree"]
                and full_minimum_is_interior
            ),
            "complete_deletion_is_flat": isolated_range
            < thresholds["maximum_complete_deletion_energy_range_hartree"],
            "one_electron_cross_deletion_removes_registered_fraction": removed_fraction
            >= thresholds["minimum_fraction_removed_by_one_electron_cross_deletion"],
            "single_edge_deletion_reorganizes_geometry": displacement
            >= thresholds["minimum_deleted_edge_geometry_displacement_angstrom"],
            "single_edge_deletion_changes_every_centre": min(population_changes)
            >= thresholds["minimum_absolute_population_change_each_centre"],
            "complete_carrier_metrics_are_representation_invariant": representation_maximum
            < thresholds["maximum_representation_metric_error"],
            "complete_carrier_survives_hamiltonian_diagonalization": (
                eigenbasis["naive_offdiagonal_h_norm"]
                < thresholds["maximum_eigenbasis_naive_offdiagonal_norm"]
                and eigenbasis["complete_h1_carrier_norm"]
                > thresholds["minimum_eigenbasis_complete_h1_carrier_norm"]
            ),
            "residual_shapley_sum_is_exact": shapley["shapley_sum_error_hartree"]
            < thresholds["maximum_shapley_sum_error_hartree"],
        }
        profiles[basis] = {
            "minima": minima,
            "full_energy_recomputed_hartree": full_energy,
            "edge_deleted_energy_at_full_minimum_hartree": edge_energy,
            "full_binding_depth_hartree": full_depth,
            "residual_binding_depth_hartree": residual_depth,
            "fraction_binding_removed": removed_fraction,
            "geometry_displacement_angstrom": displacement,
            "full_centre_populations": full_pop,
            "edge_deleted_centre_populations": edge_pop,
            "absolute_population_changes": population_changes,
            "isolated_energy_range_hartree": isolated_range,
            "reconstruction_errors": reconstruction,
            "representation_maximum_error": representation_maximum,
            "eigenbasis_naive_offdiagonal_h_norm": eigenbasis["naive_offdiagonal_h_norm"],
            "eigenbasis_complete_h1_carrier_norm": eigenbasis["complete_h1_carrier_norm"],
            "residual_shapley": shapley,
            "gates": gates,
        }
    algebraic_names = {
        "exact_five_sector_reconstruction",
        "complete_deletion_is_flat",
        "complete_carrier_metrics_are_representation_invariant",
        "complete_carrier_survives_hamiltonian_diagonalization",
    }
    all_gates = [passed for profile in profiles.values() for passed in profile["gates"].values()]
    algebraic_gates = [
        profile["gates"][name] for profile in profiles.values() for name in algebraic_names
    ]
    if all(all_gates):
        decision = "COMPLETE_MOLECULAR_CARRIER_TRANSFER_SUPPORTED"
    elif all(algebraic_gates):
        decision = "ALGEBRAIC_CARRIER_ONLY_CAUSAL_TRANSFER_NOT_SUPPORTED"
    else:
        decision = "COMPLETE_MOLECULAR_CARRIER_TRANSFER_NOT_SUPPORTED"
    summary = {
        "experiment": "010_complete_molecular_carrier_transfer",
        "decision": decision,
        "registration_receipt": receipt,
        "target_registry": target,
        "complete_carrier_definition": "H_H4plus(R)-H_four_isolated_H_centres_in_matched_basis",
        "profiles": profiles,
        "scope": {
            "tested": "Prospective four-centre transfer of the complete molecular-carrier operation.",
            "not_established": [
                "a new physical interaction",
                "numerical predictions unavailable to standard quantum chemistry",
                "ontological O3 by computation alone",
                "laboratory confirmation",
            ],
        },
    }
    return shape_rows, audit_rows, subset_rows, summary


def write_results(output: Path, shape_rows: list, audit_rows: list, subset_rows: list, summary: dict):
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for filename, rows in (
        ("shape_surfaces.csv", shape_rows),
        ("representation_audit.csv", audit_rows),
        ("residual_subsets.csv", subset_rows),
    ):
        with (output / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    report_lines = [
        "# Experiment 010 registered result",
        "",
        "Decision: `%s`" % summary["decision"],
        "",
        "| Basis | Full minimum a/b (A) | Binding depth (Eh) | Removed | Edge displacement (A) | Gates |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for basis, profile in summary["profiles"].items():
        minimum = profile["minima"]["full"]
        report_lines.append(
            "| %s | %.2f/%.2f | %.9f | %.6f%% | %.3f | %d/9 |"
            % (
                basis,
                minimum["a_angstrom"],
                minimum["b_angstrom"],
                profile["full_binding_depth_hartree"],
                100 * profile["fraction_binding_removed"],
                profile["geometry_displacement_angstrom"],
                sum(profile["gates"].values()),
            )
        )
    report_lines.extend(
        [
            "",
            "All profile-specific positive, mixed, and negative gates are retained in `summary.json`.",
            "",
            "This result concerns a constitutive counterfactual inside standard finite-basis quantum chemistry; it does not establish a new force or exclusive predictive capacity.",
            "",
        ]
    )
    (output / "RESULT.md").write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--registration-receipt", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    manifest, target = verify_registration()
    if args.validate_registration:
        if args.registration_receipt is not None:
            raise ProvenanceError("validation mode refuses a registration receipt")
        print(
            json.dumps(
                {
                    "registration_valid": True,
                    "experiment": manifest["experiment"],
                    "target_execution_performed": False,
                    "registered_source_count": len(manifest["source_sha256"]),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.registration_receipt is None:
        raise ProvenanceError("scientific execution requires --registration-receipt")
    if args.output.exists():
        raise ProvenanceError("output path already exists")
    receipt = validate_receipt(args.registration_receipt)
    outputs = execute_registered_target(target, receipt)
    write_results(args.output, *outputs)
    print(json.dumps(outputs[-1], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
