#!/usr/bin/env python3
"""Frozen runner for Experiment 008.

Registration validation is safe before registration. Scientific execution
requires both --execute and an explicit post-registration measurement file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
MANIFEST = ROOT / "registration_manifest.json"
SOURCE_LOCK = ROOT / "benchmark_sources.json"

R_INFINITY_C_HZ = 3.2898419602508e15
ALPHA = 7.2973525643e-3
RELATIVE_ERROR_LIMIT = 2.0 * ALPHA * ALPHA
CONTROL_IMPROVEMENT_MIN = 100.0
ME_OVER_PARTNER = {
    "muonium_1s2s": 4.83633170e-3,
    "positronium_1s2s": 1.0,
}
EXPECTED_SOURCE_IDS = {
    "muonium_1s2s": "doi:10.1103/PhysRevLett.84.1136",
    "positronium_1s2s": "arxiv:2407.02443v1",
}

TOTAL_EXPONENTS = (
    -4.0,
    -3.0,
    -2.0,
    -1.5,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
    3.0,
    4.0,
)
RADII = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)
DIMENSIONS = tuple(range(1, 13))
POWER_Q = (1.0 / 3.0, 0.5, 2.0 / 3.0, 1.5, 2.0, 3.0, 4.0)
DEFORMED_K = (0.25, 0.5, 1.0, 2.0, 4.0)


class ProvenanceError(RuntimeError):
    """Raised when a frozen source or post-registration input is invalid."""


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
    if manifest.get("schema") != "siel-experiment-008-registration-v1":
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
        observed = sha256_file(path)
        if observed != frozen_hash:
            raise ProvenanceError("hash mismatch: %s" % relative)

    default_results = ROOT / "results"
    if default_results.exists():
        raise ProvenanceError("default results path already exists before execution")
    return manifest


def boundary_identity_audit() -> Dict[str, Any]:
    survivors = [value for value in TOTAL_EXPONENTS if abs(value) <= 1e-15]
    return {
        "registered_total_exponents": list(TOTAL_EXPONENTS),
        "survivors": survivors,
        "pass": survivors == [0.0],
    }


def power_op(x: float, y: float, q: float) -> float:
    return (x ** q + y ** q) ** (1.0 / q)


def deformed_op(x: float, y: float, k: float) -> float:
    return x + y + k * x * y


def additive_coordinate_audit() -> Dict[str, Any]:
    values = (0.125, 0.5, 1.25, 3.0)
    tolerance = 1e-12
    regular: List[Dict[str, Any]] = []

    for q in POWER_Q:
        max_error = 0.0
        for x in values:
            for y in values:
                combined = power_op(x, y, q)
                max_error = max(max_error, abs(combined ** q - (x ** q + y ** q)))
        regular.append({"family": "power_sum", "parameter": q, "max_error": max_error})

    for k in DEFORMED_K:
        max_error = 0.0
        for x in values:
            for y in values:
                combined = deformed_op(x, y, k)
                lhs = math.log1p(k * combined)
                rhs = math.log1p(k * x) + math.log1p(k * y)
                max_error = max(max_error, abs(lhs - rhs))
        regular.append({"family": "deformed_sum", "parameter": k, "max_error": max_error})

    max_strict_order = max(1.0, 2.0) < max(1.5, 2.0)
    regular_pass = all(item["max_error"] <= tolerance for item in regular)
    return {
        "regular_candidates": regular,
        "max_control_strict_order": max_strict_order,
        "pass": regular_pass and not max_strict_order,
    }


def radial_force(name: str, radius: float) -> float:
    if name.startswith("power_"):
        exponent = float(name.split("_", 1)[1])
        return radius ** (-exponent)
    if name == "yukawa_inverse_square":
        return math.exp(-0.25 * radius) / (radius * radius)
    if name == "log_modified_inverse_square":
        return (1.0 + 0.25 * math.log(radius)) / (radius * radius)
    if name == "short_range_modified_inverse_square":
        return (1.0 + 0.25 / radius) / (radius * radius)
    raise KeyError(name)


def spatial_distribution_audit() -> Dict[str, Any]:
    names = (
        "power_1.0",
        "power_1.5",
        "power_2.0",
        "power_2.5",
        "power_3.0",
        "yukawa_inverse_square",
        "log_modified_inverse_square",
        "short_range_modified_inverse_square",
    )
    diagnostics: Dict[str, float] = {}
    survivors: List[str] = []
    for name in names:
        totals = [radius * radius * radial_force(name, radius) for radius in RADII]
        scale = max(abs(value) for value in totals)
        spread = (max(totals) - min(totals)) / scale
        diagnostics[name] = spread
        if spread <= 1e-12:
            survivors.append(name)
    return {
        "registered_radii": list(RADII),
        "relative_spreads": diagnostics,
        "survivors": survivors,
        "pass": survivors == ["power_2.0"],
    }


def dimension_conditions(dimension: int) -> Dict[str, bool]:
    if dimension <= 2:
        return {
            "asymptotic_separation": False,
            "no_fall_to_center": True,
            "cutoff_free_discrete_scale": True,
        }
    if dimension == 3:
        return {
            "asymptotic_separation": True,
            "no_fall_to_center": True,
            "cutoff_free_discrete_scale": True,
        }
    if dimension == 4:
        return {
            "asymptotic_separation": True,
            "no_fall_to_center": False,
            "cutoff_free_discrete_scale": False,
        }
    return {
        "asymptotic_separation": True,
        "no_fall_to_center": False,
        "cutoff_free_discrete_scale": False,
    }


def dimensional_stability_audit() -> Dict[str, Any]:
    diagnostics: Dict[str, Dict[str, bool]] = {}
    survivors: List[int] = []
    for dimension in DIMENSIONS:
        conditions = dimension_conditions(dimension)
        diagnostics[str(dimension)] = conditions
        if all(conditions.values()):
            survivors.append(dimension)
    return {
        "registered_dimensions": list(DIMENSIONS),
        "conditions": diagnostics,
        "survivors": survivors,
        "pass": survivors == [3],
    }


def reentry_audit() -> Dict[str, Any]:
    candidates = {
        "complex_unitary": {"minimal": True, "composition": True, "linear_norm_group": True},
        "real_orthogonal": {"minimal": True, "composition": True, "linear_norm_group": True},
        "dissipative_linear": {"minimal": False, "composition": True, "linear_norm_group": False},
        "amplifying_linear": {"minimal": False, "composition": True, "linear_norm_group": False},
        "shear_linear": {"minimal": False, "composition": True, "linear_norm_group": False},
        "state_dependent_phase": {"minimal": True, "composition": False, "linear_norm_group": False},
        "projectively_normalized_linear": {"minimal": True, "composition": False, "linear_norm_group": False},
    }
    minimal_survivors = sorted(name for name, item in candidates.items() if item["minimal"])
    final_survivors = sorted(
        name
        for name, item in candidates.items()
        if item["minimal"] and item["composition"] and item["linear_norm_group"]
    )
    expected_final = ["complex_unitary", "real_orthogonal"]
    nonlinear_minimal = {
        "state_dependent_phase",
        "projectively_normalized_linear",
    }.issubset(minimal_survivors)
    return {
        "candidates": candidates,
        "minimal_survivors": minimal_survivors,
        "composition_compatible_survivors": final_survivors,
        "generator_identity": "G^dagger=-G; H=iG; H^dagger=H",
        "pass": nonlinear_minimal and final_survivors == expected_final,
    }


def gross_transition_prediction(record_id: str) -> float:
    ratio = ME_OVER_PARTNER[record_id]
    return 0.75 * R_INFINITY_C_HZ / (1.0 + ratio)


def infinite_mass_prediction() -> float:
    return 0.75 * R_INFINITY_C_HZ


def validate_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if payload.get("schema") != "siel-e008-measurements-v1":
        raise ProvenanceError("measurement schema mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 2:
        raise ProvenanceError("exactly two measurement records are required")

    by_id: Dict[str, Dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, dict):
            raise ProvenanceError("measurement record must be an object")
        record_id = raw.get("id")
        if record_id in by_id:
            raise ProvenanceError("duplicate measurement id")
        if record_id not in EXPECTED_SOURCE_IDS:
            raise ProvenanceError("unexpected measurement id: %r" % record_id)
        if raw.get("source_id") != EXPECTED_SOURCE_IDS[record_id]:
            raise ProvenanceError("source id mismatch for %s" % record_id)
        for field in ("frequency_hz", "uncertainty_hz"):
            value = raw.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ProvenanceError("%s must be numeric" % field)
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ProvenanceError("%s must be positive and finite" % field)
        by_id[record_id] = dict(raw)

    if set(by_id) != set(EXPECTED_SOURCE_IDS):
        raise ProvenanceError("measurement record set mismatch")
    return [by_id[record_id] for record_id in sorted(by_id)]


def empirical_audit(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    outcomes: Dict[str, Dict[str, Any]] = {}
    control_prediction = infinite_mass_prediction()
    for record in records:
        record_id = str(record["id"])
        measured = float(record["frequency_hz"])
        predicted = gross_transition_prediction(record_id)
        relational_error = abs(predicted - measured)
        control_error = abs(control_prediction - measured)
        relative_error = relational_error / measured
        improvement = math.inf if relational_error == 0.0 else control_error / relational_error
        passed = (
            relative_error <= RELATIVE_ERROR_LIMIT
            and improvement >= CONTROL_IMPROVEMENT_MIN
        )
        outcomes[record_id] = {
            "source_id": record["source_id"],
            "measured_hz": measured,
            "uncertainty_hz": float(record["uncertainty_hz"]),
            "predicted_hz": predicted,
            "infinite_mass_control_hz": control_prediction,
            "relative_error": relative_error,
            "control_improvement_factor": improvement,
            "relative_error_limit": RELATIVE_ERROR_LIMIT,
            "control_improvement_min": CONTROL_IMPROVEMENT_MIN,
            "pass": passed,
        }
    return {
        "records": outcomes,
        "pass": all(item["pass"] for item in outcomes.values()),
    }


def classify(structural_pass: bool, empirical_pass: bool) -> str:
    if structural_pass and empirical_pass:
        return "SUPPORTED_ATOMIC_CLOSURE_TRANSFER"
    if structural_pass:
        return "STRUCTURAL_TRANSFER_ONLY"
    if empirical_pass:
        return "EMPIRICAL_GROSS_STRUCTURE_ONLY"
    return "NOT_SUPPORTED"


def evaluate(measurements: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    structural = {
        "boundary_identity": boundary_identity_audit(),
        "additive_coordinate": additive_coordinate_audit(),
        "spatial_distribution": spatial_distribution_audit(),
        "dimensional_stability": dimensional_stability_audit(),
        "continuous_reentry": reentry_audit(),
    }
    structural_pass = all(layer["pass"] for layer in structural.values())
    empirical = empirical_audit(measurements)
    decision = classify(structural_pass, empirical["pass"])
    return {
        "schema": "siel-e008-result-v1",
        "experiment": "008_preregistered_atomic_closure_transfer",
        "decision": decision,
        "structural": structural,
        "structural_pass": structural_pass,
        "empirical": empirical,
        "empirical_pass": empirical["pass"],
        "constants": {
            "R_infinity_c_hz": R_INFINITY_C_HZ,
            "alpha": ALPHA,
            "relative_error_limit_2_alpha_squared": RELATIVE_ERROR_LIMIT,
            "electron_muon_mass_ratio": ME_OVER_PARTNER["muonium_1s2s"],
            "electron_positron_mass_ratio": ME_OVER_PARTNER["positronium_1s2s"],
        },
    }


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Experiment 008 Result",
        "",
        "Decision: **%s**" % summary["decision"],
        "",
        "## Structural gates",
        "",
    ]
    for name, layer in summary["structural"].items():
        lines.append("- `%s`: %s" % (name, "PASS" if layer["pass"] else "FAIL"))
    lines.extend(["", "## Empirical holdouts", ""])
    for name, item in summary["empirical"]["records"].items():
        lines.append(
            "- `%s`: %s; relative error `%.12g`; control improvement `%.12g`"
            % (
                name,
                "PASS" if item["pass"] else "FAIL",
                item["relative_error"],
                item["control_improvement_factor"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The empirical gate concerns leading finite-mass gross structure. It does not test higher-order QED, spin, annihilation, nuclear-size, or radiative corrections.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, summary: Dict[str, Any]) -> None:
    if output_dir.exists():
        raise ProvenanceError("output directory already exists: %s" % output_dir)
    output_dir.mkdir(parents=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-registration", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--measurement-file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = verify_registration()
        if args.validate_registration:
            if args.measurement_file is not None:
                raise ProvenanceError("registration validation cannot load measurements")
            print(
                json.dumps(
                    {
                        "experiment": manifest["experiment"],
                        "status": manifest["status"],
                        "registered_sources_verified": len(manifest["source_sha256"]),
                        "scientific_execution": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.measurement_file is None:
            raise ProvenanceError("--measurement-file is required with --execute")
        measurement_payload = load_json(args.measurement_file)
        records = validate_measurements(measurement_payload)
        summary = evaluate(records)
        summary["measurement_file_sha256"] = sha256_file(args.measurement_file)
        write_outputs(args.output_dir, summary)
        print(json.dumps({"decision": summary["decision"], "output_dir": str(args.output_dir)}, indent=2))
        return 0
    except (OSError, ValueError, ProvenanceError, json.JSONDecodeError) as exc:
        print("PROVENANCE_FAILURE: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
