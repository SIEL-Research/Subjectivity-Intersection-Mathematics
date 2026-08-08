#!/usr/bin/env python3
"""Frozen preregistration validator and post-release evaluator for E008D."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"
PREDICTION = ROOT / "prediction_before_benchmark.json"
BENCHMARK_LOCK = ROOT / "benchmark_sources.json"
MEASUREMENT_SCHEMA = "siel-e008d-k-second-order-corrections-v1"
SOURCE_ID = "doi:10.1103/PhysRevA.78.032519"
EXPECTED_RECORDS = {
    "potassium39_4p1_2_second_order_delta_A": SOURCE_ID,
    "potassium41_4p1_2_second_order_delta_A": SOURCE_ID,
}
ACCEPTANCE_HALF_WIDTH_LOG = 0.05
STRONG_HALF_WIDTH_LOG = 0.01


class ProvenanceError(RuntimeError):
    """Raised when a frozen input or post-registration record is invalid."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_registration() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    if manifest.get("schema") != "siel-experiment-008d-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_values_present") is not False:
        raise ProvenanceError("registration declares target values")
    prediction = load_json(PREDICTION)
    if prediction.get("target_values_loaded") is not False:
        raise ProvenanceError("prediction declares target values")
    benchmark = load_json(BENCHMARK_LOCK)
    if benchmark.get("target_values_present") is not False:
        raise ProvenanceError("benchmark lock contains target values")
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


def registered_predictions() -> dict[str, float]:
    payload = load_json(PREDICTION)
    return {
        "mixed_rank": float(payload["primary_prediction"]),
        "m1_only": float(payload["m1_only_control"]),
    }


def validate_measurements(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema") != MEASUREMENT_SCHEMA:
        raise ProvenanceError("measurement schema mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ProvenanceError("exactly two benchmark records are required")
    required = {
        "id",
        "source_id",
        "second_order_delta_A_khz",
        "rounding_half_width_khz",
    }
    observed: dict[str, dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, dict) or set(raw) != required:
            raise ProvenanceError("benchmark record fields mismatch")
        record_id = raw["id"]
        if record_id in observed or record_id not in EXPECTED_RECORDS:
            raise ProvenanceError("benchmark record id mismatch")
        if raw["source_id"] != EXPECTED_RECORDS[record_id]:
            raise ProvenanceError("benchmark source id mismatch")
        value = raw["second_order_delta_A_khz"]
        half_width = raw["rounding_half_width_khz"]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value == 0.0
        ):
            raise ProvenanceError("second-order correction must be finite and nonzero")
        if (
            not isinstance(half_width, (int, float))
            or isinstance(half_width, bool)
            or not math.isfinite(half_width)
            or half_width <= 0.0
            or half_width >= abs(value)
        ):
            raise ProvenanceError("rounding half-width must be positive and smaller than value")
        observed[record_id] = dict(raw)
    if set(observed) != set(EXPECTED_RECORDS):
        raise ProvenanceError("benchmark record set mismatch")
    return [observed[key] for key in sorted(observed)]


def observed_ratio(records: list[Mapping[str, Any]]) -> dict[str, float]:
    by_id = {record["id"]: record for record in records}
    row39 = by_id["potassium39_4p1_2_second_order_delta_A"]
    row41 = by_id["potassium41_4p1_2_second_order_delta_A"]
    value39 = float(row39["second_order_delta_A_khz"])
    value41 = float(row41["second_order_delta_A_khz"])
    if value39 * value41 <= 0.0:
        raise ProvenanceError("the two published corrections have opposite signs")
    half39 = float(row39["rounding_half_width_khz"])
    half41 = float(row41["rounding_half_width_khz"])
    ratio = value39 / value41
    rounding_sigma_log = math.hypot(half39 / value39, half41 / value41)
    return {
        "delta_A_k39_khz": value39,
        "delta_A_k41_khz": value41,
        "ratio_k39_over_k41": ratio,
        "rounding_half_width_log": rounding_sigma_log,
    }


def classify(ratio: float, rounding_half_width_log: float) -> dict[str, Any]:
    predictions = registered_predictions()
    errors = {
        name: abs(math.log(ratio / prediction))
        for name, prediction in predictions.items()
    }
    expanded = {
        name: error + rounding_half_width_log for name, error in errors.items()
    }
    passing = [
        name for name, error in expanded.items() if error <= ACCEPTANCE_HALF_WIDTH_LOG
    ]
    if passing == ["mixed_rank"]:
        decision = "MIXED_RANK_PROSPECTIVE_PREDICTION_SUPPORTED"
    elif passing == ["m1_only"]:
        decision = "M1_ONLY_CONTROL_SUPPORTED"
    elif len(passing) == 2:
        decision = "BOTH_REGISTERED_MODELS_WITHIN_TOLERANCE"
    else:
        decision = "NO_REGISTERED_MODEL_SUPPORTED"
    return {
        "decision": decision,
        "predictions": predictions,
        "absolute_log_errors": errors,
        "rounding_expanded_log_errors": expanded,
        "acceptance_half_width_log": ACCEPTANCE_HALF_WIDTH_LOG,
        "strong_half_width_log": STRONG_HALF_WIDTH_LOG,
        "mixed_rank_is_closer": errors["mixed_rank"] < errors["m1_only"],
        "mixed_rank_strong_match": (
            expanded["mixed_rank"] <= STRONG_HALF_WIDTH_LOG
        ),
        "passing_models": passing,
    }


def evaluate(measurement_path: Path) -> dict[str, Any]:
    records = validate_measurements(load_json(measurement_path))
    observation = observed_ratio(records)
    classification = classify(
        observation["ratio_k39_over_k41"],
        observation["rounding_half_width_log"],
    )
    return {
        "schema": "siel-e008d-result-v1",
        "experiment": "008d_pyscf_potassium_mixed_rank_prediction",
        "source_id": SOURCE_ID,
        "observation": observation,
        "classification": classification,
        "primary_decision": classification["decision"],
    }


def render_report(summary: Mapping[str, Any]) -> str:
    observation = summary["observation"]
    classification = summary["classification"]
    return "\n".join(
        [
            "# Experiment 008D result",
            "",
            "Decision: **%s**" % summary["primary_decision"],
            "",
            "- Observed K-39/K-41 correction ratio: `%.15g`"
            % observation["ratio_k39_over_k41"],
            "- Registered mixed-rank prediction: `%.15g`"
            % classification["predictions"]["mixed_rank"],
            "- Registered M1-only control: `%.15g`"
            % classification["predictions"]["m1_only"],
            "- Mixed-rank absolute log error: `%.9g`"
            % classification["absolute_log_errors"]["mixed_rank"],
            "- M1-only absolute log error: `%.9g`"
            % classification["absolute_log_errors"]["m1_only"],
            "- Mixed-rank strong match: `%s`"
            % classification["mixed_rank_strong_match"],
            "",
        ]
    )


def write_atomic_output(output_dir: Path, summary: Mapping[str, Any]) -> None:
    if output_dir.exists():
        raise ProvenanceError("output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=".%s-" % output_dir.name, dir=str(output_dir.parent))
    )
    try:
        (temporary / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (temporary / "report.md").write_text(render_report(summary), encoding="utf-8")
        os.replace(temporary, output_dir)
    except Exception:
        for path in temporary.iterdir():
            path.unlink()
        temporary.rmdir()
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--measurement-file", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.validate_registration:
            if args.measurement_file is not None or args.output_dir is not None:
                raise ProvenanceError("registration validation refuses benchmark input")
            verify_registration()
            print("E008D REGISTRATION VALID")
            return 0
        if args.measurement_file is None or args.output_dir is None:
            raise ProvenanceError("execution requires measurement file and output directory")
        verify_registration()
        summary = evaluate(args.measurement_file)
        write_atomic_output(args.output_dir, summary)
        print(summary["primary_decision"])
        return 0
    except (OSError, ValueError, ProvenanceError) as error:
        print("PROVENANCE_FAILURE: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
