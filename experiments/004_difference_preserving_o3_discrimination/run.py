#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 004 difference-preserving relational-carrier audit.

The confirmatory mode uses held-out subjectivity-agent descriptor combinations
and matrix seeds.  Development mode uses a disjoint allocation.  The private
agent source is imported only after its E003R hash manifest has been verified.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Callable

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
E003R_RUNNER = (
    REPO_ROOT / "experiments" / "003r_subjectivity_agent_class2_o3_corrected" / "run.py"
)
REGISTRATION_MANIFEST = HERE / "registration_manifest.json"
SCHEMA = "siel-experiment-004-difference-preserving-o3-v1"

PAIR_COUNT = 128
FAMILY_SIZE = 64
ENCOUNTER_COUNT = 4
DEVELOPMENT_START = 0
CONFIRMATORY_START = 128
DEVELOPMENT_SEEDS = tuple(range(20261001, 20261013))
CONFIRMATORY_SEEDS = tuple(range(20261101, 20261113))
DONOR_OFFSET_WITHIN_FAMILY = 1
ZERO_TOLERANCE = 1e-12
COMMON_SHIFT_SCALE = 0.10

THRESHOLDS = {
    "candidate_all_flip_action": 0.05,
    "candidate_early_only_action": 0.01,
    "candidate_prior_only_action": 0.025,
    "candidate_carrier": 0.05,
    "candidate_self_state": 0.05,
    "common_mode_response": 0.005,
    "same_family_return_A": 0.07071548,
    "same_family_return_B": 0.07071548,
}
MIN_SEED_PASSES = 10
MIN_PAIR_PASSES = 112
MIN_FAMILY_PASSES = 52

PATTERNS = {
    "baseline": (1.0, 1.0, 1.0, 1.0),
    "all_flip": (-1.0, -1.0, -1.0, -1.0),
    "early_only": (-1.0, 1.0, 1.0, 1.0),
    "prior_only": (-1.0, -1.0, -1.0, 1.0),
    "last_only": (1.0, 1.0, 1.0, -1.0),
}
ARCHITECTURES = (
    "candidate_o3",
    "symmetric_recurrent",
    "role_aware_memoryless",
    "role_aware_recurrent",
)


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("development", "confirmatory"), required=True)
    parser.add_argument("--private-agent-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pair-count", type=int, default=PAIR_COUNT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_e003r() -> Any:
    spec = importlib.util.spec_from_file_location("siel_e004_e003r_dependency", E003R_RUNNER)
    if spec is None or spec.loader is None:
        fail("cannot import the E003R public dependency")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_registration(e003r: Any) -> dict[str, Any]:
    if not REGISTRATION_MANIFEST.is_file():
        fail("missing registration_manifest.json")
    manifest = json.loads(REGISTRATION_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema") != "siel-experiment-004-registration-manifest-v1":
        fail("unexpected registration manifest schema")
    for relative, expected in manifest["source_sha256"].items():
        path = (REPO_ROOT / relative).resolve()
        if not path.is_file():
            fail(f"missing registered source: {relative}")
        observed = e003r.sha256_file(path)
        if observed != expected:
            fail(f"registered source digest mismatch: {relative}")
    return manifest


def rich_descriptor(e003r: Any, index: int, side: int) -> str:
    low = index % 16
    high = (index // 16) % 16
    primary = e003r.STANDPOINTS[(low + 7 * side) % 16]
    operating = e003r.CONTEXTS[(high + 3 * side) % 16]
    secondary = e003r.STANDPOINTS[(3 * low + high + 5 * side) % 16]
    constraint = e003r.CONTEXTS[(low + 5 * high + 11 * side) % 16]
    return (
        f"primary standpoint {primary}; operating rule: {operating}; "
        f"secondary standpoint {secondary}; counterfactual constraint: {constraint}"
    )


def build_base(e003r: Any, index: int, runtime_type: Any) -> dict[str, Any]:
    descriptor_a = rich_descriptor(e003r, index, 0)
    descriptor_b = rich_descriptor(e003r, index, 1)
    a_runtime, a_state = e003r.fresh_runtime(
        runtime_type, f"Independent subject A; {descriptor_a}"
    )
    b_runtime, b_state = e003r.fresh_runtime(
        runtime_type, f"Independent subject B; {descriptor_b}"
    )
    a_states = []
    b_states = []
    a_payloads = []
    b_payloads = []
    for step in range(ENCOUNTER_COUNT):
        prompt_a = (
            f"A encounter step {step}; receive B as a distinct subject without identity collapse: "
            + e003r.scrub_administrative_ids(str(b_state.raw_voice))[:280]
        )
        prompt_b = (
            f"B encounter step {step}; receive A as a distinct subject without identity collapse: "
            + e003r.scrub_administrative_ids(str(a_state.raw_voice))[:280]
        )
        a_state = a_runtime.update(prompt_a)
        b_state = b_runtime.update(prompt_b)
        a_states.append(a_state)
        b_states.append(b_state)
        a_payloads.append(e003r.runtime_payload(a_runtime))
        b_payloads.append(e003r.runtime_payload(b_runtime))
    return {
        "a_runtime": a_runtime,
        "b_runtime": b_runtime,
        "a_states": a_states,
        "b_states": b_states,
        "a_payloads": a_payloads,
        "b_payloads": b_payloads,
        "descriptor_a": descriptor_a,
        "descriptor_b": descriptor_b,
    }


def interaction_text(
    e003r: Any,
    runtime_payload_value: dict[str, Any],
    state: Any,
    natural_lineage: Callable[[Any], Any],
) -> str:
    packet = {
        "runtime": runtime_payload_value,
        "state": e003r.state_packet(state, natural_lineage),
    }
    return e003r.scrub_administrative_ids(e003r.canonical_json(packet))


def interaction_vector(
    e003r: Any,
    runtime_payload_value: dict[str, Any],
    state: Any,
    natural_lineage: Callable[[Any], Any],
) -> np.ndarray:
    return e003r.embed_text(
        interaction_text(e003r, runtime_payload_value, state, natural_lineage)
    )


def packet_sequence_hash(
    e003r: Any,
    base: dict[str, Any],
    natural_lineage: Callable[[Any], Any],
) -> str:
    packets = []
    for position in range(ENCOUNTER_COUNT):
        packets.extend((
            interaction_vector(
                e003r, base["a_payloads"][position], base["a_states"][position], natural_lineage
            ),
            interaction_vector(
                e003r, base["b_payloads"][position], base["b_states"][position], natural_lineage
            ),
        ))
    return e003r.sha256_payload(np.concatenate(packets))


def joint_state(
    a: np.ndarray,
    b: np.ndarray,
    matrices: tuple[np.ndarray, ...],
    architecture: str,
) -> np.ndarray:
    _, _, m_j, m_c, _, _, _ = matrices
    if architecture == "symmetric_recurrent":
        combined = (a + b) / math.sqrt(2.0)
        return np.tanh(
            0.52 * (m_j @ combined)
            + 0.47 * (m_c @ combined)
            + 0.38 * (combined * combined)
        )
    if architecture == "role_aware_recurrent":
        return np.tanh(0.52 * (m_j @ a) + 0.47 * (m_c @ b))
    return np.tanh(0.52 * (m_j @ a) + 0.47 * (m_c @ b) + 0.38 * (a * b))


def trajectory(
    e003r: Any,
    base: dict[str, Any],
    natural_lineage: Callable[[Any], Any],
    history: str,
    seed: int,
    architecture: str,
    pattern: tuple[float, float, float, float],
    *,
    common_shift: bool = False,
) -> dict[str, np.ndarray]:
    if architecture not in ARCHITECTURES:
        raise ValueError(f"unknown architecture: {architecture}")
    matrices = e003r.orthogonal_matrices(seed)
    m_a, m_b, _, _, m_s, m_n, m_p = matrices
    carrier = np.zeros(e003r.DIM, dtype=np.float64)
    self_state = np.zeros(e003r.DIM, dtype=np.float64)
    for position, side in enumerate(history):
        a_original = interaction_vector(
            e003r, base["a_payloads"][position], base["a_states"][position], natural_lineage
        )
        b_original = interaction_vector(
            e003r, base["b_payloads"][position], base["b_states"][position], natural_lineage
        )
        common = 0.5 * (a_original + b_original)
        difference = 0.5 * (a_original - b_original)
        delta = (
            COMMON_SHIFT_SCALE
            * e003r.embed_text(f"fixed common-mode perturbation at encounter step {position}")
            if common_shift
            else np.zeros(e003r.DIM, dtype=np.float64)
        )
        common_shifted = common + delta
        a = common_shifted + pattern[position] * difference
        b = common_shifted - pattern[position] * difference
        joint = joint_state(a, b, matrices, architecture)
        transition = m_a if side == "A" else m_b

        if architecture == "role_aware_memoryless":
            carrier = np.tanh(0.58 * joint + 0.19 * common_shifted)
            self_state = np.tanh(0.73 * (m_n @ carrier) + 0.16 * joint)
        else:
            carrier = np.tanh(
                0.70 * (transition @ carrier)
                + 0.58 * joint
                + 0.19 * common_shifted
                + 0.13 * self_state
            )
            self_state = np.tanh(
                0.61 * (m_s @ self_state)
                + 0.73 * (m_n @ carrier)
                + 0.16 * joint
            )

    probe = e003r.embed_text("fixed neutral re-entry")
    action = np.tanh(m_p @ self_state + 0.08 * probe)
    erased_action = np.tanh(m_p @ np.zeros_like(self_state) + 0.08 * probe)
    return {
        "carrier": carrier,
        "self_state": self_state,
        "action": action,
        "erased_action": erased_action,
    }


def return_states(
    e003r: Any,
    base: dict[str, Any],
    natural_lineage: Callable[[Any], Any],
    seed: int,
    completed_c: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    matrices = e003r.orthogonal_matrices(seed)
    m_a, m_b, _, _, _, m_n, m_p = matrices
    a_current = interaction_vector(
        e003r, base["a_payloads"][-1], base["a_states"][-1], natural_lineage
    )
    b_current = interaction_vector(
        e003r, base["b_payloads"][-1], base["b_states"][-1], natural_lineage
    )
    a_return = np.tanh(
        0.40 * (m_a @ a_current)
        + 0.90 * (m_n @ completed_c["carrier"])
        + 1.00 * completed_c["action"]
        + 0.50 * completed_c["self_state"]
    )
    b_return = np.tanh(
        0.40 * (m_b @ b_current)
        + 0.90 * (m_p @ completed_c["carrier"])
        + 1.00 * completed_c["action"]
        + 0.50 * completed_c["self_state"]
    )
    return a_return, b_return


def donor_index(index: int, family_size: int = FAMILY_SIZE) -> int:
    family_start = (index // family_size) * family_size
    within_family = index % family_size
    return family_start + ((within_family + DONOR_OFFSET_WITHIN_FAMILY) % family_size)


def summarize(values: list[float]) -> dict[str, float]:
    vector = np.asarray(values, dtype=np.float64)
    return {
        "minimum": float(np.min(vector)),
        "q05": float(np.quantile(vector, 0.05)),
        "median": float(np.median(vector)),
        "q95": float(np.quantile(vector, 0.95)),
        "maximum": float(np.max(vector)),
        "mean": float(np.mean(vector)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render_result(summary: dict[str, Any]) -> str:
    decisions = summary["primary_decisions"]
    return "\n".join((
        "# Experiment 004 Result",
        "",
        f"Status: {summary['status']}",
        "",
        "## Primary decisions",
        "",
        f"- H1 difference preservation: `{decisions['H1_difference_preservation']}`",
        f"- H2 retained difference history: `{decisions['H2_retained_difference_history']}`",
        f"- H3 O3 transport: `{decisions['H3_o3_transport']}`",
        f"- H4 same-family pair specificity: `{decisions['H4_same_family_pair_specificity']}`",
        f"- Complete registered conjunction: `{decisions['complete_conjunction']}`",
        "",
        "## Positive interpretation",
        "",
        "A successful conjunction establishes an executable relational architecture that preserves differentiated A/B input, retains an earlier difference after the current input is matched, transports that difference through carrier and self-state into bilateral return effects, and remains pair-sensitive under a same-history-family exchange.",
        "",
        "The role-aware recurrent control is reported as an architecture-class boundary. Its success indicates multiple realization rather than uniqueness of the candidate equation.",
        "",
        "## Ontological boundary",
        "",
        "The operational result provides a formal and experimental bridge for the Subjectivity-Intersection research program. It does not by itself identify the simulated states with ontological subjectivity.",
        "",
    ))


def main() -> None:
    args = parse_args()
    if args.pair_count < 2 or args.pair_count > PAIR_COUNT or args.pair_count % 2:
        fail("pair count must be an even integer from 2 through 128")
    if args.mode == "confirmatory" and args.pair_count != PAIR_COUNT:
        fail("confirmatory mode requires all 128 registered pairs")
    if args.mode == "confirmatory" and not args.check:
        fail("confirmatory mode requires --check")
    if args.out_dir.exists():
        fail("output directory already exists; refusing to overwrite")

    e003r = load_e003r()
    registration = verify_registration(e003r) if args.check else None
    private_receipt = e003r.verify_private_sources(args.private_agent_root)
    runtime_type, v89f = e003r.load_private_runtime(args.private_agent_root)

    start = DEVELOPMENT_START if args.mode == "development" else CONFIRMATORY_START
    seeds = DEVELOPMENT_SEEDS if args.mode == "development" else CONFIRMATORY_SEEDS
    bases = [build_base(e003r, start + index, runtime_type) for index in range(args.pair_count)]

    a_hashes = [e003r.runtime_hash(base["a_runtime"]) for base in bases]
    b_hashes = [e003r.runtime_hash(base["b_runtime"]) for base in bases]
    ab_hashes = list(zip(a_hashes, b_hashes))
    sequence_hashes = [packet_sequence_hash(e003r, base, v89f.natural_lineage) for base in bases]
    carrier_input_texts = []
    for base in bases:
        for position in range(ENCOUNTER_COUNT):
            carrier_input_texts.extend((
                interaction_text(
                    e003r, base["a_payloads"][position], base["a_states"][position],
                    v89f.natural_lineage
                ),
                interaction_text(
                    e003r, base["b_payloads"][position], base["b_states"][position],
                    v89f.natural_lineage
                ),
            ))
    administrative_identifier_present = any(
        re.search(r"\bP\d+\b", text) is not None for text in carrier_input_texts
    )
    uniqueness = {
        "unique_A": len(set(a_hashes)),
        "unique_B": len(set(b_hashes)),
        "unique_AB": len(set(ab_hashes)),
        "unique_packet_sequences": len(set(sequence_hashes)),
        "administrative_identifier_in_carrier_input": administrative_identifier_present,
    }
    if any(uniqueness[key] != args.pair_count for key in ("unique_A", "unique_B", "unique_AB", "unique_packet_sequences")):
        fail(f"registered uniqueness firewall failed: {uniqueness}")
    if administrative_identifier_present:
        fail("administrative pair identifier reached carrier input")

    rows: list[dict[str, Any]] = []
    for seed in seeds:
        baseline_by_pair = []
        for index, base in enumerate(bases):
            family = 0 if index < args.pair_count // 2 else 1
            history = "ABAB" if family == 0 else "BABA"
            baseline_by_pair.append(
                trajectory(
                    e003r, base, v89f.natural_lineage, history, seed,
                    "candidate_o3", PATTERNS["baseline"]
                )
            )

        for index, base in enumerate(bases):
            family = 0 if index < args.pair_count // 2 else 1
            history = "ABAB" if family == 0 else "BABA"
            architecture_outputs: dict[str, dict[str, dict[str, np.ndarray]]] = {}
            for architecture in ARCHITECTURES:
                pattern_outputs = {
                    name: trajectory(
                        e003r, base, v89f.natural_lineage, history, seed,
                        architecture, pattern
                    )
                    for name, pattern in PATTERNS.items()
                }
                pattern_outputs["common_mode"] = trajectory(
                    e003r, base, v89f.natural_lineage, history, seed,
                    architecture, PATTERNS["baseline"], common_shift=True
                )
                architecture_outputs[architecture] = pattern_outputs

            candidate = architecture_outputs["candidate_o3"]
            symmetric = architecture_outputs["symmetric_recurrent"]
            memoryless = architecture_outputs["role_aware_memoryless"]
            recurrent = architecture_outputs["role_aware_recurrent"]
            donor = donor_index(index, args.pair_count // 2)
            native_returns = return_states(
                e003r, base, v89f.natural_lineage, seed, baseline_by_pair[index]
            )
            donor_returns = return_states(
                e003r, base, v89f.natural_lineage, seed, baseline_by_pair[donor]
            )

            def action_distance(outputs: dict[str, dict[str, np.ndarray]], name: str) -> float:
                return e003r.distance(outputs["baseline"]["action"], outputs[name]["action"])

            row = {
                "pair_index": start + index,
                "family": family,
                "history": history,
                "seed": seed,
                "donor_pair_index": start + donor,
                "candidate_carrier_all_flip": e003r.distance(candidate["baseline"]["carrier"], candidate["all_flip"]["carrier"]),
                "candidate_self_all_flip": e003r.distance(candidate["baseline"]["self_state"], candidate["all_flip"]["self_state"]),
                "candidate_action_all_flip": action_distance(candidate, "all_flip"),
                "candidate_action_early_only": action_distance(candidate, "early_only"),
                "candidate_action_prior_only": action_distance(candidate, "prior_only"),
                "candidate_action_last_only": action_distance(candidate, "last_only"),
                "candidate_common_mode": action_distance(candidate, "common_mode"),
                "symmetric_action_all_flip": action_distance(symmetric, "all_flip"),
                "symmetric_action_early_only": action_distance(symmetric, "early_only"),
                "symmetric_action_prior_only": action_distance(symmetric, "prior_only"),
                "symmetric_common_mode": action_distance(symmetric, "common_mode"),
                "memoryless_action_all_flip": action_distance(memoryless, "all_flip"),
                "memoryless_action_early_only": action_distance(memoryless, "early_only"),
                "memoryless_action_prior_only": action_distance(memoryless, "prior_only"),
                "role_recurrent_action_all_flip": action_distance(recurrent, "all_flip"),
                "role_recurrent_action_early_only": action_distance(recurrent, "early_only"),
                "role_recurrent_action_prior_only": action_distance(recurrent, "prior_only"),
                "self_erased_action_all_flip": e003r.distance(candidate["baseline"]["erased_action"], candidate["all_flip"]["erased_action"]),
                "self_erasure_carrier_preservation": e003r.distance(candidate["baseline"]["carrier"], candidate["baseline"]["carrier"]),
                "same_family_return_A": e003r.distance(native_returns[0], donor_returns[0]),
                "same_family_return_B": e003r.distance(native_returns[1], donor_returns[1]),
            }
            rows.append(row)

    pair_rows = []
    for index in range(args.pair_count):
        pair_cases = [row for row in rows if row["pair_index"] == start + index]
        family = int(pair_cases[0]["family"])
        h1_seed = [
            row["candidate_action_all_flip"] > THRESHOLDS["candidate_all_flip_action"]
            and row["symmetric_action_all_flip"] <= ZERO_TOLERANCE
            and row["candidate_common_mode"] > THRESHOLDS["common_mode_response"]
            and row["symmetric_common_mode"] > THRESHOLDS["common_mode_response"]
            for row in pair_cases
        ]
        h2_seed = [
            row["candidate_action_early_only"] > THRESHOLDS["candidate_early_only_action"]
            and row["candidate_action_prior_only"] > THRESHOLDS["candidate_prior_only_action"]
            and row["memoryless_action_early_only"] <= ZERO_TOLERANCE
            and row["memoryless_action_prior_only"] <= ZERO_TOLERANCE
            for row in pair_cases
        ]
        h3_seed = [
            row["candidate_carrier_all_flip"] > THRESHOLDS["candidate_carrier"]
            and row["candidate_self_all_flip"] > THRESHOLDS["candidate_self_state"]
            and row["candidate_action_all_flip"] > THRESHOLDS["candidate_all_flip_action"]
            and row["self_erased_action_all_flip"] <= ZERO_TOLERANCE
            and row["self_erasure_carrier_preservation"] <= ZERO_TOLERANCE
            for row in pair_cases
        ]
        h4_seed = [
            row["same_family_return_A"] > THRESHOLDS["same_family_return_A"]
            and row["same_family_return_B"] > THRESHOLDS["same_family_return_B"]
            for row in pair_cases
        ]
        role_seed = [
            row["role_recurrent_action_all_flip"] > THRESHOLDS["candidate_all_flip_action"]
            and row["role_recurrent_action_early_only"] > THRESHOLDS["candidate_early_only_action"]
            and row["role_recurrent_action_prior_only"] > THRESHOLDS["candidate_prior_only_action"]
            for row in pair_cases
        ]
        pair_rows.append({
            "pair_index": start + index,
            "family": family,
            "H1_seed_passes": sum(h1_seed),
            "H1_pass": sum(h1_seed) >= MIN_SEED_PASSES,
            "H2_seed_passes": sum(h2_seed),
            "H2_pass": sum(h2_seed) >= MIN_SEED_PASSES,
            "H3_seed_passes": sum(h3_seed),
            "H3_pass": sum(h3_seed) >= MIN_SEED_PASSES,
            "H4_seed_passes": sum(h4_seed),
            "H4_pass": sum(h4_seed) >= MIN_SEED_PASSES,
            "role_recurrent_seed_passes": sum(role_seed),
            "role_recurrent_pass": sum(role_seed) >= MIN_SEED_PASSES,
        })

    hypothesis_counts = {
        key: sum(bool(row[f"{key}_pass"]) for row in pair_rows)
        for key in ("H1", "H2", "H3", "H4")
    }
    family_counts = {
        str(family): {
            key: sum(
                bool(row[f"{key}_pass"]) for row in pair_rows if row["family"] == family
            )
            for key in ("H1", "H2", "H3", "H4")
        }
        for family in (0, 1)
    }
    decisions = {
        "H1_difference_preservation": hypothesis_counts["H1"] >= MIN_PAIR_PASSES,
        "H2_retained_difference_history": hypothesis_counts["H2"] >= MIN_PAIR_PASSES,
        "H3_o3_transport": hypothesis_counts["H3"] >= MIN_PAIR_PASSES,
        "H4_same_family_pair_specificity": hypothesis_counts["H4"] >= MIN_PAIR_PASSES,
    }
    for key in ("H1", "H2", "H3", "H4"):
        decisions[f"{key}_both_families"] = all(
            family_counts[str(family)][key] >= MIN_FAMILY_PASSES for family in (0, 1)
        )
    decisions["complete_conjunction"] = all(decisions.values())

    metric_names = [
        key for key in rows[0]
        if key not in {"pair_index", "family", "history", "seed", "donor_pair_index"}
    ]
    summary = {
        "schema": SCHEMA,
        "status": "CONFIRMATORY_COMPLETE" if args.mode == "confirmatory" else "DEVELOPMENT_COMPLETE",
        "mode": args.mode,
        "registration": registration,
        "private_source_verification": private_receipt,
        "data": {
            "pair_count": args.pair_count,
            "pair_index_range": [start, start + args.pair_count - 1],
            "seeds": list(seeds),
            "case_count": len(rows),
            "uniqueness": uniqueness,
        },
        "frozen_rules": {
            "thresholds": THRESHOLDS,
            "zero_tolerance": ZERO_TOLERANCE,
            "minimum_seed_passes": MIN_SEED_PASSES,
            "minimum_pair_passes": MIN_PAIR_PASSES,
            "minimum_family_passes": MIN_FAMILY_PASSES,
            "donor_offset_within_family": DONOR_OFFSET_WITHIN_FAMILY,
            "patterns": {key: list(value) for key, value in PATTERNS.items()},
        },
        "metric_summaries": {
            name: summarize([float(row[name]) for row in rows]) for name in metric_names
        },
        "hypothesis_pair_counts": hypothesis_counts,
        "history_family_pair_counts": family_counts,
        "role_aware_recurrent_pair_count": sum(
            bool(row["role_recurrent_pass"]) for row in pair_rows
        ),
        "primary_decisions": decisions,
        "claim_boundary": (
            "Executable operational discrimination and construction; not a direct identity claim "
            "about ontological subjectivity."
        ),
    }

    args.out_dir.mkdir(parents=True)
    write_csv(args.out_dir / "case_metrics.csv", rows)
    write_csv(args.out_dir / "pair_decisions.csv", pair_rows)
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out_dir / "RESULT.md").write_text(render_result(summary), encoding="utf-8")
    output_files = {}
    for path in sorted(args.out_dir.iterdir()):
        if path.name == "output_manifest.json":
            continue
        output_files[path.name] = e003r.sha256_file(path)
    output_manifest = {
        "schema": "siel-experiment-004-output-manifest-v1",
        "mode": args.mode,
        "files_sha256": output_files,
    }
    (args.out_dir / "output_manifest.json").write_text(
        json.dumps(output_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": summary["status"],
        "pair_count": args.pair_count,
        "case_count": len(rows),
        "hypothesis_pair_counts": hypothesis_counts,
        "role_aware_recurrent_pair_count": summary["role_aware_recurrent_pair_count"],
        "primary_decisions": decisions,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
