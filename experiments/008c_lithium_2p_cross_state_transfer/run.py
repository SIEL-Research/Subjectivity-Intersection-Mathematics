#!/usr/bin/env python3
"""Frozen preregistration runner for Experiment 008C."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"

SPIN_LI6 = 1.0
SPIN_LI7 = 1.5
MOMENT_LI6 = 0.82204463
MOMENT_LI7 = 3.25641619
MOMENT_LI6_UNCERTAINTY = 0.00000037
MOMENT_LI7_UNCERTAINTY = 0.00000057
INTERVAL_FACTOR_LI6 = 1.5
INTERVAL_FACTOR_LI7 = 2.0
ATOMIC_MASS_LI6_U = 6.0151228874
ATOMIC_MASS_LI7_U = 7.0160034366
ELECTRON_MASS_U = 0.0005485799090441
LITHIUM_ATOMIC_NUMBER = 3
SECTOR_IMBALANCE_LI6 = 1.0 / 3.0
SECTOR_IMBALANCE_LI7 = 1.0 / 4.0
MEASUREMENT_SCHEMA = "siel-e008c-li-2p-hfs-measurements-v1"
SOURCE_ID = "doi:10.1139/p65-075"
EXPECTED_SOURCE_IDS = {
    "lithium6_2p1_2_hfs_A": SOURCE_ID,
    "lithium7_2p1_2_hfs_A": SOURCE_ID,
}


class ProvenanceError(RuntimeError):
    """Raised when frozen provenance or post-registration input is invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify_registration() -> Dict[str, Any]:
    manifest = load_json(MANIFEST)
    if manifest.get("schema") != "siel-experiment-008c-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status is not preregistered/not executed")
    if manifest.get("target_values_present") is not False:
        raise ProvenanceError("registration unexpectedly declares target values")
    expected = manifest.get("source_sha256")
    if not isinstance(expected, dict) or not expected:
        raise ProvenanceError("source_sha256 is missing")
    for relative, frozen_hash in sorted(expected.items()):
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ProvenanceError("missing registered source: %s" % relative)
        if sha256_file(path) != frozen_hash:
            raise ProvenanceError("hash mismatch: %s" % relative)
    if (ROOT / "results").exists():
        raise ProvenanceError("default results path exists before execution")
    return manifest


def nuclear_mass_in_electron_masses(atomic_mass_u: float) -> float:
    return atomic_mass_u / ELECTRON_MASS_U - LITHIUM_ATOMIC_NUMBER


def bilateral_mass_coordinate(mass: float) -> float:
    return 4.0 * mass / (mass + 1.0) ** 2


def recursive_coordinate(mass: float, sector_imbalance: float) -> float:
    return bilateral_mass_coordinate(mass) * (1.0 + sector_imbalance**2)


def registered_predictions() -> Dict[str, float]:
    g6 = MOMENT_LI6 / SPIN_LI6
    g7 = MOMENT_LI7 / SPIN_LI7
    base = (g6 * INTERVAL_FACTOR_LI6) / (g7 * INTERVAL_FACTOR_LI7)
    mass6 = nuclear_mass_in_electron_masses(ATOMIC_MASS_LI6_U)
    mass7 = nuclear_mass_in_electron_masses(ATOMIC_MASS_LI7_U)
    b6 = bilateral_mass_coordinate(mass6)
    b7 = bilateral_mass_coordinate(mass7)
    z6 = recursive_coordinate(mass6, SECTOR_IMBALANCE_LI6)
    z7 = recursive_coordinate(mass7, SECTOR_IMBALANCE_LI7)
    mass_only = base * math.exp(b6 - b7)
    recursive = base * math.exp(z6 - z7)
    predictions = (base, mass_only, recursive)
    nearest = min(
        abs(math.log(left / right))
        for index, left in enumerate(predictions)
        for right in predictions[index + 1 :]
    )
    half_width = nearest / 4.0
    moment_sigma = math.sqrt(
        (MOMENT_LI6_UNCERTAINTY / MOMENT_LI6) ** 2
        + (MOMENT_LI7_UNCERTAINTY / MOMENT_LI7) ** 2
    )
    maximum_measurement_sigma = math.sqrt(
        max(0.0, (half_width / 3.0) ** 2 - moment_sigma**2)
    )
    return {
        "factorised_base_ratio_li6_over_li7": base,
        "bilateral_mass_only_ratio_li6_over_li7": mass_only,
        "recursive_sector_ratio_li6_over_li7": recursive,
        "mass_li6_in_electron_masses": mass6,
        "mass_li7_in_electron_masses": mass7,
        "bilateral_coordinate_li6": b6,
        "bilateral_coordinate_li7": b7,
        "recursive_coordinate_li6": z6,
        "recursive_coordinate_li7": z7,
        "nearest_model_log_separation": nearest,
        "acceptance_half_width": half_width,
        "moment_model_sigma_log": moment_sigma,
        "maximum_measurement_sigma_log": maximum_measurement_sigma,
    }


def validate_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if payload.get("schema") != MEASUREMENT_SCHEMA:
        raise ProvenanceError("measurement schema mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ProvenanceError("exactly two measurement records are required")
    required = {
        "id",
        "source_id",
        "magnetic_dipole_constant_hz",
        "uncertainty_hz",
    }
    observed: Dict[str, Dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, dict) or set(raw) != required:
            raise ProvenanceError("measurement record fields mismatch")
        record_id = raw["id"]
        if record_id in observed or record_id not in EXPECTED_SOURCE_IDS:
            raise ProvenanceError("measurement record id mismatch")
        if raw["source_id"] != EXPECTED_SOURCE_IDS[record_id]:
            raise ProvenanceError("measurement source id mismatch")
        constant = raw["magnetic_dipole_constant_hz"]
        uncertainty = raw["uncertainty_hz"]
        if (
            not isinstance(constant, (int, float))
            or isinstance(constant, bool)
            or not math.isfinite(constant)
            or constant == 0
        ):
            raise ProvenanceError("magnetic dipole constant must be finite and nonzero")
        if (
            not isinstance(uncertainty, (int, float))
            or isinstance(uncertainty, bool)
            or not math.isfinite(uncertainty)
            or uncertainty <= 0
        ):
            raise ProvenanceError("uncertainty must be finite and positive")
        observed[record_id] = dict(raw)
    if set(observed) != set(EXPECTED_SOURCE_IDS):
        raise ProvenanceError("measurement record set mismatch")
    return [observed[key] for key in sorted(observed)]


def observed_ratio(records: Sequence[Mapping[str, Any]]) -> Dict[str, float]:
    by_id = {record["id"]: record for record in records}
    row6 = by_id["lithium6_2p1_2_hfs_A"]
    row7 = by_id["lithium7_2p1_2_hfs_A"]
    a6 = float(row6["magnetic_dipole_constant_hz"])
    a7 = float(row7["magnetic_dipole_constant_hz"])
    u6 = float(row6["uncertainty_hz"])
    u7 = float(row7["uncertainty_hz"])
    interval6 = abs(a6) * INTERVAL_FACTOR_LI6
    interval7 = abs(a7) * INTERVAL_FACTOR_LI7
    return {
        "magnetic_dipole_constant_li6_hz": a6,
        "magnetic_dipole_constant_li7_hz": a7,
        "interval_li6_hz": interval6,
        "interval_li7_hz": interval7,
        "ratio_li6_over_li7": interval6 / interval7,
        "measurement_sigma_log": math.sqrt((u6 / a6) ** 2 + (u7 / a7) ** 2),
    }


def classify(ratio: float, measurement_sigma_log: float) -> Dict[str, Any]:
    prediction = registered_predictions()
    if measurement_sigma_log > prediction["maximum_measurement_sigma_log"]:
        return {
            "decision": "INSUFFICIENT_PRECISION",
            "precision_gate_pass": False,
            "measurement_sigma_log": measurement_sigma_log,
            "maximum_measurement_sigma_log": prediction[
                "maximum_measurement_sigma_log"
            ],
            "models": {},
            "passing_models": [],
        }
    models = {
        "factorised_base": prediction["factorised_base_ratio_li6_over_li7"],
        "bilateral_mass_only": prediction[
            "bilateral_mass_only_ratio_li6_over_li7"
        ],
        "recursive_sector": prediction["recursive_sector_ratio_li6_over_li7"],
    }
    combined_sigma = math.hypot(
        measurement_sigma_log, prediction["moment_model_sigma_log"]
    )
    diagnostics: Dict[str, Any] = {}
    passing: List[str] = []
    for name, value in models.items():
        error = abs(math.log(ratio / value))
        passes = error + 3.0 * combined_sigma <= prediction["acceptance_half_width"]
        diagnostics[name] = {
            "prediction": value,
            "central_log_error": error,
            "combined_sigma_log": combined_sigma,
            "band_pass": passes,
        }
        if passes:
            passing.append(name)
    if len(passing) > 1:
        raise ProvenanceError("registered model bands unexpectedly overlap")
    decision_map = {
        "factorised_base": "FACTORISED_BASE_TRANSFER_SUPPORTED",
        "bilateral_mass_only": "BILATERAL_MASS_ONLY_TRANSFER_SUPPORTED",
        "recursive_sector": "RECURSIVE_SECTOR_TRANSFER_SUPPORTED",
    }
    decision = (
        decision_map[passing[0]]
        if len(passing) == 1
        else "NO_REGISTERED_TRANSFER_MODEL_SUPPORTED"
    )
    return {
        "decision": decision,
        "precision_gate_pass": True,
        "measurement_sigma_log": measurement_sigma_log,
        "maximum_measurement_sigma_log": prediction[
            "maximum_measurement_sigma_log"
        ],
        "models": diagnostics,
        "passing_models": passing,
    }


def evaluate(measurement_path: Path) -> Dict[str, Any]:
    records = validate_measurements(load_json(measurement_path))
    observation = observed_ratio(records)
    diagnostics = classify(
        observation["ratio_li6_over_li7"], observation["measurement_sigma_log"]
    )
    return {
        "experiment": "008c_lithium_2p_cross_state_transfer",
        "primary_decision": diagnostics["decision"],
        "registered_predictions": registered_predictions(),
        "observation": observation,
        "primary_diagnostics": diagnostics,
        "measurement_records": records,
        "measurement_file_sha256": sha256_file(measurement_path),
        "interpretation": (
            "This is a within-lithium transfer test from 2S1/2 to 2P1/2. "
            "It does not test or restore atomic-universal CP-158 portability."
        ),
    }


def report(summary: Mapping[str, Any]) -> str:
    prediction = summary["registered_predictions"]
    observation = summary["observation"]
    diagnostics = summary["primary_diagnostics"]
    return "\n".join(
        [
            "# Experiment 008C Result",
            "",
            "Primary decision: **%s**" % summary["primary_decision"],
            "",
            "- Observed Li-6/Li-7 interval ratio: `%.15g`"
            % observation["ratio_li6_over_li7"],
            "- Factorised base prediction: `%.15g`"
            % prediction["factorised_base_ratio_li6_over_li7"],
            "- Bilateral-mass-only prediction: `%.15g`"
            % prediction["bilateral_mass_only_ratio_li6_over_li7"],
            "- Recursive-sector prediction: `%.15g`"
            % prediction["recursive_sector_ratio_li6_over_li7"],
            "- Measurement log sigma: `%.15g`"
            % observation["measurement_sigma_log"],
            "- Precision gate pass: `%s`" % diagnostics["precision_gate_pass"],
            "- Measurement SHA-256: `%s`" % summary["measurement_file_sha256"],
            "",
            summary["interpretation"],
            "",
        ]
    )


def write_outputs(summary: Mapping[str, Any], output_dir: Path) -> None:
    if output_dir.exists():
        raise ProvenanceError("output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="e008c-", dir=str(output_dir.parent)))
    try:
        (temporary / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (temporary / "report.md").write_text(report(summary), encoding="utf-8")
        os.replace(str(temporary), str(output_dir))
    except Exception:
        for child in temporary.iterdir():
            child.unlink()
        temporary.rmdir()
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    result.add_argument("--measurement-file", type=Path)
    result.add_argument("--output-dir", type=Path, default=ROOT / "results")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        verify_registration()
        if args.validate_registration:
            if args.measurement_file is not None:
                raise ProvenanceError("registration validation cannot accept measurements")
            print("E008C registration valid; scientific execution not run.")
            return 0
        if args.measurement_file is None:
            raise ProvenanceError("scientific execution requires --measurement-file")
        summary = evaluate(args.measurement_file)
        write_outputs(summary, args.output_dir)
        print(summary["primary_decision"])
        return 0
    except (OSError, ValueError, ProvenanceError, json.JSONDecodeError) as error:
        print("PROVENANCE_FAILURE: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
