#!/usr/bin/env python3
"""Frozen registration validator and future independent evaluator for E008E."""

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
SEARCH_PROTOCOL = ROOT / "benchmark_search_protocol.json"
BENCHMARK_SCHEMA = "siel-e008e-independent-k40-benchmark-v1"
TARGET_ID = "potassium40_4p1_2_complete_second_order_delta_A"


class ProvenanceError(RuntimeError):
    """Raised when a frozen source or future benchmark violates registration."""


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
    if manifest.get("schema") != "siel-experiment-008e-registration-v1":
        raise ProvenanceError("registration manifest schema mismatch")
    if manifest.get("status") != "PREREGISTERED_NOT_EXECUTED":
        raise ProvenanceError("registration status mismatch")
    if manifest.get("target_values_present") is not False:
        raise ProvenanceError("registration declares target values")
    prediction = load_json(PREDICTION)
    if prediction.get("target_values_loaded") is not False:
        raise ProvenanceError("prediction declares target values")
    if prediction.get("known_K40_second_order_values_loaded") is not False:
        raise ProvenanceError("prediction declares a known K-40 correction")
    if prediction.get("free_fitted_parameters") != 0:
        raise ProvenanceError("prediction contains a fitted parameter")
    protocol = load_json(SEARCH_PROTOCOL)
    if protocol.get("target_values_present") is not False:
        raise ProvenanceError("benchmark protocol contains target values")
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
    if (ROOT / "benchmark_measurements.json").exists():
        raise ProvenanceError("benchmark values exist inside registration package")
    return manifest


def primary_prediction() -> dict[str, float]:
    prediction = load_json(PREDICTION)
    central = prediction["isotope_predictions"]["K-40"][
        "predicted_corrections"
    ]["delta_A_P1_2_khz"]
    envelope = prediction["input_uncertainty_envelopes"]["K-40"][
        "delta_A_P1_2_khz"
    ]
    return {
        "central_khz": float(central),
        "min_khz": float(envelope["min"]),
        "max_khz": float(envelope["max"]),
    }


def validate_benchmark(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != BENCHMARK_SCHEMA:
        raise ProvenanceError("benchmark schema mismatch")
    if set(payload) != {"schema", "source", "record"}:
        raise ProvenanceError("benchmark top-level fields mismatch")
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {
        "id",
        "title",
        "publication_date",
        "benchmark_class",
        "construction_overlap",
    }:
        raise ProvenanceError("benchmark source fields mismatch")
    if source["benchmark_class"] not in {"A", "B"}:
        raise ProvenanceError("benchmark class is not confirmatory")
    if source["construction_overlap"] is not False:
        raise ProvenanceError("benchmark overlaps construction")
    if not all(
        isinstance(source[key], str) and source[key].strip()
        for key in ("id", "title", "publication_date")
    ):
        raise ProvenanceError("benchmark source metadata is incomplete")
    record = payload["record"]
    if not isinstance(record, dict) or set(record) != {
        "target_id",
        "value_khz",
        "half_width_khz",
        "derivation",
    }:
        raise ProvenanceError("benchmark record fields mismatch")
    if record["target_id"] != TARGET_ID:
        raise ProvenanceError("benchmark target mismatch")
    if not isinstance(record["derivation"], str) or not record["derivation"].strip():
        raise ProvenanceError("benchmark derivation is missing")
    value = record["value_khz"]
    half_width = record["half_width_khz"]
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ProvenanceError("benchmark value must be finite")
    if (
        not isinstance(half_width, (int, float))
        or isinstance(half_width, bool)
        or not math.isfinite(half_width)
        or half_width <= 0.0
    ):
        raise ProvenanceError("benchmark half-width must be finite and positive")
    return {"source": dict(source), "record": dict(record)}


def classify(value_khz: float, half_width_khz: float) -> dict[str, Any]:
    prediction = primary_prediction()
    benchmark_min = value_khz - half_width_khz
    benchmark_max = value_khz + half_width_khz
    overlap = bool(
        prediction["max_khz"] >= benchmark_min
        and benchmark_max >= prediction["min_khz"]
    )
    strong_match = bool(
        prediction["min_khz"] <= value_khz <= prediction["max_khz"]
    )
    decision = (
        "K40_PRIMARY_PREDICTION_SUPPORTED"
        if overlap
        else "K40_PRIMARY_PREDICTION_NOT_SUPPORTED"
    )
    return {
        "decision": decision,
        "strong_match": strong_match,
        "prediction": prediction,
        "benchmark": {
            "central_khz": value_khz,
            "min_khz": benchmark_min,
            "max_khz": benchmark_max,
        },
        "intervals_overlap": overlap,
        "signed_relative_error": value_khz / prediction["central_khz"] - 1.0,
    }


def evaluate(benchmark_path: Path) -> dict[str, Any]:
    benchmark = validate_benchmark(load_json(benchmark_path))
    record = benchmark["record"]
    classification = classify(
        float(record["value_khz"]), float(record["half_width_khz"])
    )
    return {
        "schema": "siel-e008e-result-v1",
        "experiment": "008e_potassium40_signed_rank_prediction",
        "source": benchmark["source"],
        "record": record,
        "classification": classification,
        "primary_decision": classification["decision"],
    }


def render_report(summary: Mapping[str, Any]) -> str:
    classification = summary["classification"]
    prediction = classification["prediction"]
    benchmark = classification["benchmark"]
    return "\n".join(
        [
            "# Experiment 008E result",
            "",
            "Decision: **%s**" % summary["primary_decision"],
            "",
            "- Registered K-40 delta A(P_1/2): `%.15g kHz`"
            % prediction["central_khz"],
            "- Registered envelope: `[%.15g, %.15g] kHz`"
            % (prediction["min_khz"], prediction["max_khz"]),
            "- Independent benchmark: `%.15g kHz`" % benchmark["central_khz"],
            "- Benchmark interval: `[%.15g, %.15g] kHz`"
            % (benchmark["min_khz"], benchmark["max_khz"]),
            "- Strong match: `%s`" % classification["strong_match"],
            "- Signed relative error: `%.9g`"
            % classification["signed_relative_error"],
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
    parser.add_argument("--benchmark-file", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.validate_registration:
            if args.benchmark_file is not None or args.output_dir is not None:
                raise ProvenanceError("registration validation refuses benchmark input")
            verify_registration()
            print("E008E REGISTRATION VALID")
            return 0
        if args.benchmark_file is None or args.output_dir is None:
            raise ProvenanceError("execution requires benchmark file and output directory")
        verify_registration()
        summary = evaluate(args.benchmark_file)
        write_atomic_output(args.output_dir, summary)
        print(summary["primary_decision"])
        return 0
    except (OSError, ValueError, ProvenanceError) as error:
        print("PROVENANCE_FAILURE: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
