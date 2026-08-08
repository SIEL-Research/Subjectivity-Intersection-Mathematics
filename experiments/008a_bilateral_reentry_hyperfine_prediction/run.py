#!/usr/bin/env python3
"""Frozen runner for Experiment 008A."""

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

MASS_H = 1836.152673426
MASS_D = 3670.482967655
SPIN_H = 0.5
SPIN_D = 1.0
MU_H = 2.79284734463
MU_D = 0.8574382335
MU_H_UNCERTAINTY = 0.00000000082
MU_D_UNCERTAINTY = 0.0000000022
LAMBDA = 1.0
FULL_THEORY_NUISANCE_LOG = 500e-6
MEASUREMENT_SCHEMA = "siel-e008a-hfs-measurements-v1"
EXPECTED_SOURCE_IDS = {
    "hydrogen_1s_hfs": "doi:10.1016/j.adt.2010.05.001",
    "deuterium_1s_hfs": "doi:10.1016/j.adt.2010.05.001",
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
    if manifest.get("schema") != "siel-experiment-008a-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status is not preregistered/not executed")
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


def reduced_mass(mass: float) -> float:
    return mass / (mass + 1.0)


def bilateral_factor(mass: float) -> float:
    return 4.0 * mass / (mass + 1.0) ** 2


def registered_predictions() -> Dict[str, float]:
    standard = (reduced_mass(MASS_D) / reduced_mass(MASS_H)) ** 3
    delta_b = bilateral_factor(MASS_D) - bilateral_factor(MASS_H)
    si = standard * math.exp(LAMBDA * delta_b)
    separation = abs(math.log(si / standard))
    return {
        "standard_contact_ratio": standard,
        "si_lambda_one_ratio": si,
        "delta_b": delta_b,
        "log_separation": separation,
        "acceptance_half_width": separation / 4.0,
    }


def validate_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if payload.get("schema") != MEASUREMENT_SCHEMA:
        raise ProvenanceError("measurement schema mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ProvenanceError("exactly two measurement records are required")
    observed: Dict[str, Dict[str, Any]] = {}
    required = {"id", "source_id", "frequency_hz", "uncertainty_hz"}
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
        if not isinstance(frequency, (int, float)) or not math.isfinite(frequency) or frequency <= 0:
            raise ProvenanceError("frequency must be finite and positive")
        if not isinstance(uncertainty, (int, float)) or not math.isfinite(uncertainty) or uncertainty <= 0:
            raise ProvenanceError("uncertainty must be finite and positive")
        observed[record_id] = dict(raw)
    if set(observed) != set(EXPECTED_SOURCE_IDS):
        raise ProvenanceError("measurement record set mismatch")
    return [observed[key] for key in sorted(observed)]


def observed_ratio(records: Sequence[Mapping[str, Any]]) -> Dict[str, float]:
    by_id = {record["id"]: record for record in records}
    h = by_id["hydrogen_1s_hfs"]
    d = by_id["deuterium_1s_hfs"]
    g_h = MU_H / SPIN_H
    g_d = MU_D / SPIN_D
    ratio = (
        (float(d["frequency_hz"]) / float(h["frequency_hz"]))
        * ((SPIN_H + 0.5) / (SPIN_D + 0.5))
        * abs(g_h / g_d)
    )
    sigma_log = math.sqrt(
        (float(h["uncertainty_hz"]) / float(h["frequency_hz"])) ** 2
        + (float(d["uncertainty_hz"]) / float(d["frequency_hz"])) ** 2
        + (MU_H_UNCERTAINTY / MU_H) ** 2
        + (MU_D_UNCERTAINTY / MU_D) ** 2
    )
    return {"ratio": ratio, "sigma_log": sigma_log}


def classify(ratio: float, sigma_log: float) -> Dict[str, Any]:
    prediction = registered_predictions()
    si_error = abs(math.log(ratio / prediction["si_lambda_one_ratio"]))
    standard_error = abs(math.log(ratio / prediction["standard_contact_ratio"]))
    margin = 3.0 * sigma_log
    tolerance = prediction["acceptance_half_width"]
    si_pass = si_error + margin <= tolerance
    standard_pass = standard_error + margin <= tolerance
    if si_pass and not standard_pass:
        decision = "SI_LAMBDA_ONE_SUPPORTED"
    elif standard_pass and not si_pass:
        decision = "STANDARD_CONTACT_SUPPORTED"
    else:
        decision = "NEITHER_MINIMAL_MODEL_SUPPORTED"
    delta_b = prediction["delta_b"]
    lambda_hat = math.log(ratio / prediction["standard_contact_ratio"]) / delta_b
    return {
        "decision": decision,
        "si_log_error": si_error,
        "standard_log_error": standard_error,
        "three_sigma_log_margin": margin,
        "acceptance_half_width": tolerance,
        "si_band_pass": si_pass,
        "standard_band_pass": standard_pass,
        "lambda_hat": lambda_hat,
        "si_within_full_theory_nuisance": si_error <= FULL_THEORY_NUISANCE_LOG,
        "standard_within_full_theory_nuisance": standard_error <= FULL_THEORY_NUISANCE_LOG,
        "full_theory_nuisance_log": FULL_THEORY_NUISANCE_LOG,
    }


def evaluate(measurement_path: Path) -> Dict[str, Any]:
    records = validate_measurements(load_json(measurement_path))
    observation = observed_ratio(records)
    diagnostics = classify(observation["ratio"], observation["sigma_log"])
    return {
        "experiment": "008a_bilateral_reentry_hyperfine_prediction",
        "primary_decision": diagnostics["decision"],
        "registered_postulate": "lambda=1",
        "registered_predictions": registered_predictions(),
        "observation": observation,
        "diagnostics": diagnostics,
        "measurement_records": records,
        "measurement_file_sha256": sha256_file(measurement_path),
        "interpretation_boundary": (
            "Primary result compares the registered lambda=1 postulate with the "
            "leading contact control. Full QED and nuclear corrections remain a "
            "mandatory non-overriding interpretive control."
        ),
    }


def report(summary: Mapping[str, Any]) -> str:
    prediction = summary["registered_predictions"]
    observation = summary["observation"]
    diagnostics = summary["diagnostics"]
    return "\n".join(
        [
            "# Experiment 008A Result",
            "",
            "Primary decision: **%s**" % summary["primary_decision"],
            "",
            "- Observed channel-normalized D/H ratio: `%.15g`" % observation["ratio"],
            "- Log-ratio standard uncertainty: `%.15g`" % observation["sigma_log"],
            "- SI lambda=1 prediction: `%.15g`" % prediction["si_lambda_one_ratio"],
            "- Standard contact prediction: `%.15g`" % prediction["standard_contact_ratio"],
            "- SI log error: `%.15g`" % diagnostics["si_log_error"],
            "- Standard log error: `%.15g`" % diagnostics["standard_log_error"],
            "- Implied lambda: `%.15g`" % diagnostics["lambda_hat"],
            "- Measurement SHA-256: `%s`" % summary["measurement_file_sha256"],
            "",
            summary["interpretation_boundary"],
            "",
        ]
    )


def write_outputs(summary: Mapping[str, Any], output_dir: Path) -> None:
    if output_dir.exists():
        raise ProvenanceError("output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="e008a-", dir=str(output_dir.parent)))
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
            print("E008A registration valid; scientific execution not run.")
            return 0
        if args.measurement_file is None:
            raise ProvenanceError("scientific execution requires --measurement-file")
        summary = evaluate(args.measurement_file)
        write_outputs(summary, args.output_dir)
        print(json.dumps({"primary_decision": summary["primary_decision"]}, indent=2))
        return 0
    except ProvenanceError as error:
        print("PROVENANCE_FAILURE: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
