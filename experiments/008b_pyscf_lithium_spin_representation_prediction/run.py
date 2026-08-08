#!/usr/bin/env python3
"""Frozen preregistration runner for Experiment 008B."""

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

ELECTRONIC_HFC_PER_G_MHZ = 176.04278247339448
ELECTRONIC_RELATIVE_SCALE_PROXY = 0.000717906156476737
SPIN_LI6 = 1.0
SPIN_LI7 = 1.5
MOMENT_LI6 = 0.82204463
MOMENT_LI7 = 3.25641619
MOMENT_LI6_UNCERTAINTY = 0.00000037
MOMENT_LI7_UNCERTAINTY = 0.00000057
INTERVAL_FACTOR_LI6 = 1.5
INTERVAL_FACTOR_LI7 = 2.0
MEASUREMENT_SCHEMA = "siel-e008b-li-hfs-measurements-v1"
EXPECTED_SOURCE_IDS = {
    "lithium6_2s_ground_hfs": "doi:10.1103/PhysRevLett.111.243001",
    "lithium7_2s_ground_hfs": "doi:10.1103/PhysRevLett.111.243001",
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
    if manifest.get("schema") != "siel-experiment-008b-registration-v1":
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


def registered_predictions() -> Dict[str, float]:
    g6 = MOMENT_LI6 / SPIN_LI6
    g7 = MOMENT_LI7 / SPIN_LI7
    full = (g6 * INTERVAL_FACTOR_LI6) / (g7 * INTERVAL_FACTOR_LI7)
    nuclear_g_only = g6 / g7
    representation_only = INTERVAL_FACTOR_LI6 / INTERVAL_FACTOR_LI7
    nearest_separation = min(
        abs(math.log(full / nuclear_g_only)),
        abs(math.log(full / representation_only)),
    )
    moment_sigma_log = math.sqrt(
        (MOMENT_LI6_UNCERTAINTY / MOMENT_LI6) ** 2
        + (MOMENT_LI7_UNCERTAINTY / MOMENT_LI7) ** 2
    )
    return {
        "nuclear_g_li6": g6,
        "nuclear_g_li7": g7,
        "full_factorised_ratio_li6_over_li7": full,
        "nuclear_g_only_ratio_li6_over_li7": nuclear_g_only,
        "representation_only_ratio_li6_over_li7": representation_only,
        "nearest_primary_control_log_separation": nearest_separation,
        "acceptance_half_width": nearest_separation / 4.0,
        "moment_model_sigma_log": moment_sigma_log,
        "clamped_interval_li6_mhz": (
            ELECTRONIC_HFC_PER_G_MHZ * g6 * INTERVAL_FACTOR_LI6
        ),
        "clamped_interval_li7_mhz": (
            ELECTRONIC_HFC_PER_G_MHZ * g7 * INTERVAL_FACTOR_LI7
        ),
    }


def validate_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if payload.get("schema") != MEASUREMENT_SCHEMA:
        raise ProvenanceError("measurement schema mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ProvenanceError("exactly two measurement records are required")
    required = {"id", "source_id", "frequency_hz", "uncertainty_hz"}
    observed: Dict[str, Dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, dict) or set(raw) != required:
            raise ProvenanceError("measurement record fields mismatch")
        record_id = raw["id"]
        if record_id in observed or record_id not in EXPECTED_SOURCE_IDS:
            raise ProvenanceError("measurement record id mismatch")
        if raw["source_id"] != EXPECTED_SOURCE_IDS[record_id]:
            raise ProvenanceError("measurement source id mismatch")
        frequency = raw["frequency_hz"]
        uncertainty = raw["uncertainty_hz"]
        if (
            not isinstance(frequency, (int, float))
            or isinstance(frequency, bool)
            or not math.isfinite(frequency)
            or frequency <= 0
        ):
            raise ProvenanceError("frequency must be finite and positive")
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
    li6 = by_id["lithium6_2s_ground_hfs"]
    li7 = by_id["lithium7_2s_ground_hfs"]
    frequency6 = float(li6["frequency_hz"])
    frequency7 = float(li7["frequency_hz"])
    sigma_measurement_log = math.sqrt(
        (float(li6["uncertainty_hz"]) / frequency6) ** 2
        + (float(li7["uncertainty_hz"]) / frequency7) ** 2
    )
    return {
        "ratio_li6_over_li7": frequency6 / frequency7,
        "measurement_sigma_log": sigma_measurement_log,
    }


def classify(ratio: float, measurement_sigma_log: float) -> Dict[str, Any]:
    predictions = registered_predictions()
    tolerance = predictions["acceptance_half_width"]
    models = {
        "full_factorised": (
            predictions["full_factorised_ratio_li6_over_li7"],
            predictions["moment_model_sigma_log"],
        ),
        "nuclear_g_only": (
            predictions["nuclear_g_only_ratio_li6_over_li7"],
            predictions["moment_model_sigma_log"],
        ),
        "representation_only": (
            predictions["representation_only_ratio_li6_over_li7"],
            0.0,
        ),
    }
    diagnostics: Dict[str, Any] = {}
    passing: List[str] = []
    for name, (prediction, model_sigma_log) in models.items():
        log_error = abs(math.log(ratio / prediction))
        combined_sigma_log = math.hypot(measurement_sigma_log, model_sigma_log)
        band_pass = log_error + 3.0 * combined_sigma_log <= tolerance
        diagnostics[name] = {
            "prediction": prediction,
            "central_log_error": log_error,
            "combined_sigma_log": combined_sigma_log,
            "three_sigma_log_margin": 3.0 * combined_sigma_log,
            "band_pass": band_pass,
        }
        if band_pass:
            passing.append(name)
    decision_map = {
        "full_factorised": "FULL_FACTORISED_GENERATOR_SUPPORTED",
        "nuclear_g_only": "NUCLEAR_G_ONLY_CONTROL_SUPPORTED",
        "representation_only": "REPRESENTATION_ONLY_CONTROL_SUPPORTED",
    }
    decision = (
        decision_map[passing[0]]
        if len(passing) == 1
        else "NEITHER_REGISTERED_MODEL_SUPPORTED"
    )
    return {
        "decision": decision,
        "acceptance_half_width": tolerance,
        "passing_models": passing,
        "models": diagnostics,
    }


def absolute_diagnostics(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_id = {record["id"]: record for record in records}
    predictions = registered_predictions()
    mapping = {
        "lithium6_2s_ground_hfs": "clamped_interval_li6_mhz",
        "lithium7_2s_ground_hfs": "clamped_interval_li7_mhz",
    }
    result: Dict[str, Any] = {}
    for record_id, prediction_key in mapping.items():
        observed_mhz = float(by_id[record_id]["frequency_hz"]) / 1e6
        predicted_mhz = predictions[prediction_key]
        result[record_id] = {
            "observed_mhz": observed_mhz,
            "clamped_uhf_prediction_mhz": predicted_mhz,
            "signed_relative_error": observed_mhz / predicted_mhz - 1.0,
            "absolute_log_error": abs(math.log(observed_mhz / predicted_mhz)),
        }
    result["electronic_scale_relative_basis_proxy"] = ELECTRONIC_RELATIVE_SCALE_PROXY
    result["classification_overriding"] = False
    return result


def evaluate(measurement_path: Path) -> Dict[str, Any]:
    records = validate_measurements(load_json(measurement_path))
    observation = observed_ratio(records)
    diagnostics = classify(
        observation["ratio_li6_over_li7"], observation["measurement_sigma_log"]
    )
    return {
        "experiment": "008b_pyscf_lithium_spin_representation_prediction",
        "primary_decision": diagnostics["decision"],
        "registered_predictions": registered_predictions(),
        "observation": observation,
        "primary_diagnostics": diagnostics,
        "absolute_diagnostics": absolute_diagnostics(records),
        "measurement_records": records,
        "measurement_file_sha256": sha256_file(measurement_path),
        "interpretation": (
            "The primary test asks whether the jointly generated nuclear-g and "
            "representation factors predict the raw lithium isotope interval ratio. "
            "The PySCF absolute intervals are mandatory secondary diagnostics."
        ),
    }


def report(summary: Mapping[str, Any]) -> str:
    prediction = summary["registered_predictions"]
    observation = summary["observation"]
    diagnostics = summary["primary_diagnostics"]
    absolute = summary["absolute_diagnostics"]
    return "\n".join(
        [
            "# Experiment 008B Result",
            "",
            "Primary decision: **%s**" % summary["primary_decision"],
            "",
            "- Observed Li-6/Li-7 interval ratio: `%.15g`"
            % observation["ratio_li6_over_li7"],
            "- Full factorised prediction: `%.15g`"
            % prediction["full_factorised_ratio_li6_over_li7"],
            "- Nuclear-g-only control: `%.15g`"
            % prediction["nuclear_g_only_ratio_li6_over_li7"],
            "- Representation-only control: `%.15g`"
            % prediction["representation_only_ratio_li6_over_li7"],
            "- Full model log error: `%.15g`"
            % diagnostics["models"]["full_factorised"]["central_log_error"],
            "- Clamped PySCF Li-6 prediction: `%.15g MHz`"
            % prediction["clamped_interval_li6_mhz"],
            "- Clamped PySCF Li-7 prediction: `%.15g MHz`"
            % prediction["clamped_interval_li7_mhz"],
            "- Li-6 absolute signed relative error: `%.15g`"
            % absolute["lithium6_2s_ground_hfs"]["signed_relative_error"],
            "- Li-7 absolute signed relative error: `%.15g`"
            % absolute["lithium7_2s_ground_hfs"]["signed_relative_error"],
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
    temporary = Path(tempfile.mkdtemp(prefix="e008b-", dir=str(output_dir.parent)))
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
            print("E008B registration valid; scientific execution not run.")
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
