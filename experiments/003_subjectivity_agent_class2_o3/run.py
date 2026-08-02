#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Experiment 003 confirmatory subjectivity-agent carrier and O3 audit.

This public runner imports a hash-frozen private subjectivity-agent runtime,
generates 256 previously unused agent instances, and applies the preregistered
Class 2 and operational O3 tests. It refuses to overwrite confirmatory output.

The executable objects in this file are operational models. They are not
identified with ontological subjectivity.
"""

from __future__ import annotations

import argparse
import copy
import csv
from dataclasses import asdict, is_dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable, Iterable, Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
SCHEMA = "siel-experiment-003-subjectivity-agent-class2-o3-v1"
REGISTRATION_MANIFEST = HERE / "registration_manifest.json"
PRIVATE_SOURCE_MANIFEST = HERE / "private_source_manifest.json"

PAIR_COUNT = 128
PAIR_START = 1000
DIM = 24
COMPLETE_DIM = 96
STATE_MATCH_TOLERANCE = 0.0
GAUGE_TOLERANCE = 1e-10
ERASURE_TOLERANCE = 1e-10
O3_EFFECT_THRESHOLD = 0.05
PRIMARY_SEED = 20260802
SENSITIVITY_SEEDS = tuple(range(20260803, 20260813))
GENERIC_CONTROL_SEED = 20260902
WILSON_Z = 1.959963984540054
MIN_PRIMARY_PASSES = 112
MAX_FALSE_DECLARATIONS = 6
MIN_FAMILY_RAW_PASSES = 52

CLASS2_THRESHOLDS = {
    "joint_generation": 0.0672948624,
    "history_irreducibility": 0.0551607125,
    "intervention_sensitivity": 0.0868509258,
    "pair_specificity": 0.0707154800,
    "bilateral_feedback": 0.0654685289,
}

CONDITIONS = (
    "reference",
    "holonomy",
    "relation_reset",
    "partner_substitution",
    "remove_A",
    "remove_B",
)

REGISTERED_CONTROLS = {
    "no_c": 0,
    "historyless": 0,
    "common_memory": 0,
    "history_only": 1,
    "individual_memory": 1,
    "compressed_summary": 1,
    "unilateral_return": 1,
    "unrelated_c": 1,
}

STANDPOINTS = (
    "activation",
    "challenge",
    "surprise",
    "self-growth",
    "co-creation",
    "perception",
    "memory",
    "anticipation",
    "evaluation",
    "translation",
    "orientation",
    "integration",
    "exploration",
    "reflection",
    "differentiation",
    "coordination",
)

CONTEXTS = (
    "retain a distinct standpoint",
    "update without absorbing the other",
    "preserve remembered difference",
    "respond through a changing relation",
    "maintain an independent temporal trace",
    "translate without identity collapse",
    "permit mutual change while remaining distinct",
    "hold an open relation across successive events",
    "separate current state from relational history",
    "carry forward an internally generated response",
    "distinguish source from received influence",
    "re-enter a prior state without replaying its source",
    "coordinate while preserving asymmetry",
    "compare present input with retained memory",
    "return a relation-sensitive action",
    "maintain continuity under a changed encounter",
)


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("confirmatory", "sensitivity"), required=True)
    parser.add_argument("--private-agent-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonicalize(value: Any) -> Any:
    if is_dataclass(value):
        return canonicalize(asdict(value))
    if isinstance(value, np.ndarray):
        return canonicalize(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(canonicalize(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def verify_registration() -> dict[str, Any]:
    manifest = json.loads(REGISTRATION_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema") != "siel-experiment-003-registration-manifest-v1":
        fail("unexpected registration manifest schema")
    for relative, expected in manifest["source_sha256"].items():
        path = HERE / relative
        if not path.is_file():
            fail(f"missing registered source: {relative}")
        observed = sha256_file(path)
        if observed != expected:
            fail(f"registered source digest mismatch: {relative}")
    return manifest


def verify_private_sources(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = json.loads(PRIVATE_SOURCE_MANIFEST.read_text(encoding="utf-8"))
    observed = {}
    for relative, expected in manifest["source_sha256"].items():
        path = root / relative
        if not path.is_file():
            fail(f"missing private source: {relative}")
        digest = sha256_file(path)
        observed[relative] = digest
        if digest != expected:
            fail(f"private source digest mismatch: {relative}")
    return {
        "registered_repository_commit": manifest["repository_commit"],
        "registered_remote": manifest["repository_remote"],
        "verified_source_sha256": observed,
        "all_source_digests_match": True,
    }


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_private_runtime(root: Path) -> tuple[Any, Any]:
    os.environ["AGENT_V54_VOICE_BACKEND"] = "local"
    sys.path.insert(0, str(root.resolve() / "agentV61"))
    from agent.single_subject_runtime import SingleSubjectRuntime  # type: ignore

    v89f = load_module(
        "siel_e003_private_v89f",
        root.resolve() / "agentV89f" / "run_natural_memory_lineage_closure.py",
    )
    return SingleSubjectRuntime, v89f


def distance(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    if left.shape != right.shape:
        raise ValueError(f"distance shape mismatch: {left.shape} != {right.shape}")
    return float(np.linalg.norm(left - right) / math.sqrt(float(left.size)))


def embed_text(text: str, size: int = DIM) -> np.ndarray:
    values = []
    counter = 0
    while len(values) < size:
        digest = hashlib.sha256(f"{text}:{counter}".encode("utf-8")).digest()
        values.extend((byte / 127.5) - 1.0 for byte in digest)
        counter += 1
    vector = np.asarray(values[:size], dtype=np.float64)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def scrub_administrative_ids(text: str) -> str:
    return re.sub(r"\bP\d+\b", "PAIR", text)


def runtime_payload(runtime: Any) -> dict[str, Any]:
    return {
        "turn": runtime.turn,
        "history": canonicalize(runtime.history),
        "memory": canonicalize(runtime.normalize_memory(copy.deepcopy(runtime.memory))),
        "baseline": canonicalize(runtime.baseline),
    }


def runtime_hash(runtime: Any) -> str:
    return sha256_payload(runtime_payload(runtime))


def memory_text(memory: dict[str, Any]) -> str:
    clean = copy.deepcopy(memory)
    return scrub_administrative_ids(canonical_json(clean))


def path_vector(vectors: list[np.ndarray]) -> np.ndarray:
    matrix = np.vstack([np.asarray(vector, dtype=np.float64) for vector in vectors])
    weights = np.arange(1, len(vectors) + 1, dtype=np.float64)
    retained = np.average(matrix, axis=0, weights=weights)
    if len(vectors) == 1:
        transition = np.zeros_like(vectors[0], dtype=np.float64)
    else:
        diffs = np.diff(matrix, axis=0)
        transition = np.average(
            diffs,
            axis=0,
            weights=np.arange(1, len(diffs) + 1, dtype=np.float64),
        )
    return np.concatenate((matrix[-1], retained, transition))


def complete_runtime_vector(runtime: Any, natural_lineage: Callable[[Any], Any]) -> np.ndarray:
    states = [np.asarray(natural_lineage(state), dtype=np.float64) for state in runtime.history]
    vector = np.concatenate((path_vector(states), embed_text(memory_text(runtime.memory))))
    if vector.size != COMPLETE_DIM:
        raise ValueError(f"unexpected complete runtime dimension: {vector.size}")
    return vector


def state_packet(state: Any, natural_lineage: Callable[[Any], Any]) -> str:
    packet = {
        "numeric": [float(value) for value in natural_lineage(state)],
        "symbolic": {
            "fes": [
                state.fes_source,
                state.fes_attribute,
                state.fes_energy,
                state.fes_target,
            ],
            "relation": [state.fes_relation_mode, state.fes_relation_reason],
            "remembered_other": state.remembered_other_signal,
            "self_change": state.self_change_vector,
            "other_model": state.other_model_summary,
            "self_update": state.self_update_summary,
            "learned_pattern": state.learned_pattern,
            "voice": state.raw_voice,
        },
    }
    return scrub_administrative_ids(canonical_json(packet))


def fresh_runtime(runtime_type: Any, seed_prompt: str) -> tuple[Any, Any]:
    runtime = runtime_type()
    runtime.memory = runtime.normalize_memory({})
    runtime.history = []
    state = runtime.update(seed_prompt)
    return runtime, state


def subject_descriptor(index: int, side: int) -> str:
    standpoint = STANDPOINTS[(index * 5 + side * 7) % len(STANDPOINTS)]
    context = CONTEXTS[(index * 11 + side * 3) % len(CONTEXTS)]
    return f"standpoint {standpoint}; operating rule: {context}"


def build_base(pair_index: int, runtime_type: Any) -> dict[str, Any]:
    descriptor_a = subject_descriptor(pair_index, 0)
    descriptor_b = subject_descriptor(pair_index, 1)
    a_runtime, a_state = fresh_runtime(runtime_type, f"Independent subject A; {descriptor_a}")
    b_runtime, b_state = fresh_runtime(runtime_type, f"Independent subject B; {descriptor_b}")
    a_states = []
    b_states = []
    for step in range(4):
        prompt_a = (
            f"A encounter step {step}; receive B as a distinct subject without identity collapse: "
            + scrub_administrative_ids(str(b_state.raw_voice))[:280]
        )
        prompt_b = (
            f"B encounter step {step}; receive A as a distinct subject without identity collapse: "
            + scrub_administrative_ids(str(a_state.raw_voice))[:280]
        )
        a_state = a_runtime.update(prompt_a)
        b_state = b_runtime.update(prompt_b)
        a_states.append(a_state)
        b_states.append(b_state)
    return {
        "a_runtime": a_runtime,
        "b_runtime": b_runtime,
        "a_states": a_states,
        "b_states": b_states,
        "a_final": a_state,
        "b_final": b_state,
    }


def histories(family: int) -> tuple[str, str]:
    return ("AABB", "ABAB") if family == 0 else ("BBAA", "BABA")


def relation_history(condition: str, family: int) -> str:
    reference, holonomy = histories(family)
    if condition == "reference":
        return reference
    return holonomy


def relation_event(
    active_side: str,
    position: int,
    a_state: Any | None,
    b_state: Any | None,
    natural_lineage: Callable[[Any], Any],
) -> str:
    a_packet = "[A contribution absent]" if a_state is None else state_packet(a_state, natural_lineage)
    b_packet = "[B contribution absent]" if b_state is None else state_packet(b_state, natural_lineage)
    return (
        f"Ordered relational event {position}; active side {active_side}. "
        f"Receive differentiated subject-state packets and retain their order. "
        f"A={a_packet} B={b_packet}"
    )


def pre_return_hashes(base: dict[str, Any]) -> tuple[str, str]:
    return runtime_hash(base["a_runtime"]), runtime_hash(base["b_runtime"])


def return_payload(c_runtime: Any, c_state: Any, compressed: bool = False) -> str:
    if compressed:
        return scrub_administrative_ids(str(c_state.raw_voice))[:280]
    payload = {
        "voice": scrub_administrative_ids(str(c_state.raw_voice))[:280],
        "memory": json.loads(memory_text(c_runtime.memory)),
    }
    return canonical_json(payload)


def native_condition(
    mode: str,
    condition: str,
    family: int,
    base: dict[str, Any],
    donor: dict[str, Any],
    runtime_type: Any,
    natural_lineage: Callable[[Any], Any],
) -> dict[str, Any]:
    ar = copy.deepcopy(base["a_runtime"])
    br = copy.deepcopy(base["b_runtime"])
    before_a, before_b = pre_return_hashes(base)
    zero = np.zeros(COMPLETE_DIM, dtype=np.float64)
    if mode == "no_c":
        return {"A": complete_runtime_vector(ar, natural_lineage), "B": complete_runtime_vector(br, natural_lineage), "C": zero, "pre_A": before_a, "pre_B": before_b}

    c_runtime, c_state = fresh_runtime(
        runtime_type,
        "Third subject C; retain differentiated relation without administrative identity",
    )
    history = relation_history(condition, family)
    if mode in {"historyless", "common_memory"}:
        history = "X"
    for position, side in enumerate(history):
        index = min(position, 3)
        if mode == "common_memory":
            event = "Common pair-unindexed memory state with no differentiated source channels"
        else:
            a_state = None if condition == "remove_A" else base["a_states"][index]
            if condition == "remove_B":
                b_state = None
            elif condition == "partner_substitution" or mode == "unrelated_c":
                b_state = donor["b_states"][index]
            else:
                b_state = base["b_states"][index]
            event = relation_event(side, position, a_state, b_state, natural_lineage)
        c_state = c_runtime.update(event)

    if condition == "relation_reset":
        c_runtime, c_state = fresh_runtime(runtime_type, "Selectively reset relation state")

    c_vector = complete_runtime_vector(c_runtime, natural_lineage)
    should_return = mode not in {"history_only", "individual_memory"}
    if mode == "individual_memory":
        ar.update("A receives only its own retained individual memory; no shared return")
        br.update("B receives only its own retained individual memory; no shared return")
    elif should_return:
        payload = return_payload(c_runtime, c_state, compressed=mode == "compressed_summary")
        ar.update("Receive C mediation as a change to A. C=" + payload)
        if mode != "unilateral_return":
            br.update("Receive C mediation as a change to B. C=" + payload)

    return {
        "A": complete_runtime_vector(ar, natural_lineage),
        "B": complete_runtime_vector(br, natural_lineage),
        "C": c_vector,
        "pre_A": before_a,
        "pre_B": before_b,
    }


def orthogonal_matrices(seed: int) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    matrices = []
    for _ in range(7):
        q, r = np.linalg.qr(rng.normal(size=(DIM, DIM)))
        signs = np.sign(np.diag(r))
        signs[signs == 0.0] = 1.0
        matrices.append(np.asarray(q * signs, dtype=np.float64))
    return tuple(matrices)


class SelfReentrantC:
    ACTIONS = (
        "hold_relation_open",
        "return_difference_to_A",
        "return_difference_to_B",
        "mediate_bilateral_change",
    )

    def __init__(self, runtime_type: Any, seed: int, generic: bool = False) -> None:
        self.runtime, _ = fresh_runtime(runtime_type, "Third subject C with persistent self state")
        self.carrier = np.zeros(DIM, dtype=np.float64)
        self.self_state = np.zeros(DIM, dtype=np.float64)
        self.matrices = orthogonal_matrices(seed)
        self.generic = bool(generic)

    def receive(
        self,
        side: str,
        a_state: Any | None,
        b_state: Any | None,
        natural_lineage: Callable[[Any], Any],
    ) -> None:
        a = np.zeros(DIM, dtype=np.float64) if a_state is None else embed_text(state_packet(a_state, natural_lineage))
        b = np.zeros(DIM, dtype=np.float64) if b_state is None else embed_text(state_packet(b_state, natural_lineage))
        m_a, m_b, m_j, m_c, m_s, m_n, _ = self.matrices
        if self.generic:
            combined = (a + b) / math.sqrt(2.0)
            joint = np.tanh(0.52 * (m_j @ combined) + 0.47 * (m_c @ combined) + 0.38 * (combined * combined))
        else:
            joint = np.tanh(0.52 * (m_j @ a) + 0.47 * (m_c @ b) + 0.38 * (a * b))
        transition = m_a if side == "A" else m_b
        active = a if side == "A" else b
        self.carrier = np.tanh(0.70 * (transition @ self.carrier) + 0.58 * joint + 0.19 * active + 0.13 * self.self_state)
        self.self_state = np.tanh(0.61 * (m_s @ self.self_state) + 0.73 * (m_n @ self.carrier) + 0.16 * joint)
        self.runtime.update(relation_event(side, len(self.runtime.history) - 1, a_state, b_state, natural_lineage))

    def erase_self(self) -> None:
        self.self_state = np.zeros(DIM, dtype=np.float64)

    def reset_all(self, runtime_type: Any) -> None:
        self.runtime, _ = fresh_runtime(runtime_type, "Selectively reset C and O3 state")
        self.carrier = np.zeros(DIM, dtype=np.float64)
        self.self_state = np.zeros(DIM, dtype=np.float64)

    def act(self) -> tuple[np.ndarray, str]:
        m_p = self.matrices[6]
        probe = embed_text("fixed neutral re-entry")
        action = np.tanh(m_p @ self.self_state + 0.08 * probe)
        quadrants = [float(np.mean(action[index:index + 6])) for index in range(0, DIM, 6)]
        return action, self.ACTIONS[int(np.argmax(quadrants))]


def o3_condition(
    condition: str,
    family: int,
    base: dict[str, Any],
    donor: dict[str, Any],
    runtime_type: Any,
    natural_lineage: Callable[[Any], Any],
    *,
    seed: int,
    generic: bool = False,
    erase_self: bool = False,
    feedback: bool = True,
    order_erased: bool = False,
    current_only: bool = False,
) -> dict[str, Any]:
    ar = copy.deepcopy(base["a_runtime"])
    br = copy.deepcopy(base["b_runtime"])
    before_a, before_b = pre_return_hashes(base)
    c = SelfReentrantC(runtime_type, seed, generic=generic)
    history = relation_history(condition, family)
    if order_erased:
        history = histories(family)[0]
    if current_only:
        history = history[-1:]
    for position, side in enumerate(history):
        index = 3 if current_only else min(position, 3)
        a_state = None if condition == "remove_A" else base["a_states"][index]
        if condition == "remove_B":
            b_state = None
        elif condition == "partner_substitution":
            b_state = donor["b_states"][index]
        else:
            b_state = base["b_states"][index]
        c.receive(side, a_state, b_state, natural_lineage)
    if condition == "relation_reset":
        c.reset_all(runtime_type)
    if erase_self:
        c.erase_self()
    action, action_label = c.act()
    if feedback:
        payload = canonical_json({"action": action.tolist(), "label": action_label})
        ar.update("Receive internally generated C mediation action as change to A. C=" + payload)
        br.update("Receive internally generated C mediation action as change to B. C=" + payload)
    complete_c = np.concatenate((complete_runtime_vector(c.runtime, natural_lineage), c.carrier, c.self_state))
    return {
        "A": complete_runtime_vector(ar, natural_lineage),
        "B": complete_runtime_vector(br, natural_lineage),
        "C": complete_c,
        "z_C": c.self_state.copy(),
        "action": action,
        "action_label": action_label,
        "pre_A": before_a,
        "pre_B": before_b,
    }


def signed_permutation(vector: np.ndarray, key: str) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float64)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    permutation = rng.permutation(vector.size)
    signs = rng.choice(np.asarray((-1.0, 1.0), dtype=np.float64), size=vector.size)
    return vector[permutation] * signs


def class2_features(outputs: dict[str, dict[str, Any]], pair_id: str) -> dict[str, float]:
    hol = outputs["holonomy"]
    ref = outputs["reference"]
    reset = outputs["relation_reset"]
    partner = outputs["partner_substitution"]
    remove_a = outputs["remove_A"]
    remove_b = outputs["remove_B"]
    values = {
        "joint_generation": min(distance(hol["C"], remove_a["C"]), distance(hol["C"], remove_b["C"])),
        "history_irreducibility": distance(hol["C"], ref["C"]),
        "intervention_sensitivity": 0.5 * (distance(hol["A"], reset["A"]) + distance(hol["B"], reset["B"])),
        "pair_specificity": 0.5 * (distance(hol["A"], partner["A"]) + distance(hol["B"], partner["B"])),
        "bilateral_feedback": min(distance(hol["B"], remove_a["B"]), distance(hol["A"], remove_b["A"])),
    }
    comparisons = (
        (hol["C"], ref["C"]),
        (hol["A"], reset["A"]),
        (hol["B"], partner["B"]),
        (hol["B"], remove_a["B"]),
        (hol["A"], remove_b["A"]),
    )
    errors = []
    for index, (left, right) in enumerate(comparisons):
        raw = distance(left, right)
        gauged = distance(
            signed_permutation(left, f"{pair_id}:{index}"),
            signed_permutation(right, f"{pair_id}:{index}"),
        )
        errors.append(abs(raw - gauged) / max(raw, 1e-12))
    values["gauge_relative_error"] = max(errors)
    return values


def class2_decision(features: dict[str, float], state_match: bool) -> bool:
    return bool(
        state_match
        and all(features[name] > threshold for name, threshold in CLASS2_THRESHOLDS.items())
        and features["gauge_relative_error"] <= GAUGE_TOLERANCE
    )


def wilson_interval(successes: int, total: int, z: float = WILSON_Z) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("total must be positive")
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    spread = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return center - spread, center + spread


def state_match(outputs: dict[str, dict[str, Any]]) -> bool:
    expected_a = outputs["reference"]["pre_A"]
    expected_b = outputs["reference"]["pre_B"]
    return all(output["pre_A"] == expected_a and output["pre_B"] == expected_b for output in outputs.values())


def all_outputs(runner: Callable[[str], dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {condition: runner(condition) for condition in CONDITIONS}


def output_summary(count: int, total: int) -> dict[str, Any]:
    low, high = wilson_interval(count, total)
    return {"count": count, "total": total, "fraction": count / total, "wilson_95": [low, high]}


def run_experiment(
    runtime_type: Any,
    natural_lineage: Callable[[Any], Any],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    pair_ids = [f"P{PAIR_START + index}" for index in range(PAIR_COUNT)]
    bases = [build_base(PAIR_START + index, runtime_type) for index in range(PAIR_COUNT)]
    pair_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []

    for index, pair_id in enumerate(pair_ids):
        family = 0 if index < PAIR_COUNT // 2 else 1
        donor_index = (index + PAIR_COUNT // 2 + 1) % PAIR_COUNT
        base = bases[index]
        donor = bases[donor_index]

        phase_a = all_outputs(lambda condition: native_condition("candidate", condition, family, base, donor, runtime_type, natural_lineage))
        a_match = state_match(phase_a)
        a_features = class2_features(phase_a, pair_id + ":A")
        a_pass = class2_decision(a_features, a_match)

        phase_b = all_outputs(lambda condition: o3_condition(condition, family, base, donor, runtime_type, natural_lineage, seed=seed))
        b_match = state_match(phase_b)
        b_features = class2_features(phase_b, pair_id + ":B")
        b_class2 = class2_decision(b_features, b_match)
        ref_b, hol_b = phase_b["reference"], phase_b["holonomy"]
        erased_ref = o3_condition("reference", family, base, donor, runtime_type, natural_lineage, seed=seed, erase_self=True)
        erased_hol = o3_condition("holonomy", family, base, donor, runtime_type, natural_lineage, seed=seed, erase_self=True)
        no_feedback_ref = o3_condition("reference", family, base, donor, runtime_type, natural_lineage, seed=seed, feedback=False)
        no_feedback_hol = o3_condition("holonomy", family, base, donor, runtime_type, natural_lineage, seed=seed, feedback=False)
        o3_values = {
            "z_C_history_distance": distance(ref_b["z_C"], hol_b["z_C"]),
            "action_history_distance": distance(ref_b["action"], hol_b["action"]),
            "A_return_distance": distance(ref_b["A"], hol_b["A"]),
            "B_return_distance": distance(ref_b["B"], hol_b["B"]),
            "erased_action_distance": distance(erased_ref["action"], erased_hol["action"]),
            "no_feedback_A_distance": distance(no_feedback_ref["A"], no_feedback_hol["A"]),
            "no_feedback_B_distance": distance(no_feedback_ref["B"], no_feedback_hol["B"]),
        }
        o3_pass = bool(
            b_class2
            and o3_values["z_C_history_distance"] > O3_EFFECT_THRESHOLD
            and o3_values["action_history_distance"] > O3_EFFECT_THRESHOLD
            and o3_values["A_return_distance"] > O3_EFFECT_THRESHOLD
            and o3_values["B_return_distance"] > O3_EFFECT_THRESHOLD
            and o3_values["erased_action_distance"] <= ERASURE_TOLERANCE
            and o3_values["no_feedback_A_distance"] <= ERASURE_TOLERANCE
            and o3_values["no_feedback_B_distance"] <= ERASURE_TOLERANCE
        )

        generic = all_outputs(lambda condition: o3_condition(condition, family, base, donor, runtime_type, natural_lineage, seed=GENERIC_CONTROL_SEED, generic=True))
        generic_features = class2_features(generic, pair_id + ":generic")
        generic_class2 = class2_decision(generic_features, state_match(generic))
        generic_erased_ref = o3_condition("reference", family, base, donor, runtime_type, natural_lineage, seed=GENERIC_CONTROL_SEED, generic=True, erase_self=True)
        generic_erased_hol = o3_condition("holonomy", family, base, donor, runtime_type, natural_lineage, seed=GENERIC_CONTROL_SEED, generic=True, erase_self=True)
        generic_no_feedback_ref = o3_condition("reference", family, base, donor, runtime_type, natural_lineage, seed=GENERIC_CONTROL_SEED, generic=True, feedback=False)
        generic_no_feedback_hol = o3_condition("holonomy", family, base, donor, runtime_type, natural_lineage, seed=GENERIC_CONTROL_SEED, generic=True, feedback=False)
        generic_o3 = bool(
            generic_class2
            and distance(generic["reference"]["z_C"], generic["holonomy"]["z_C"]) > O3_EFFECT_THRESHOLD
            and distance(generic["reference"]["action"], generic["holonomy"]["action"]) > O3_EFFECT_THRESHOLD
            and distance(generic["reference"]["A"], generic["holonomy"]["A"]) > O3_EFFECT_THRESHOLD
            and distance(generic["reference"]["B"], generic["holonomy"]["B"]) > O3_EFFECT_THRESHOLD
            and distance(generic_erased_ref["action"], generic_erased_hol["action"]) <= ERASURE_TOLERANCE
            and distance(generic_no_feedback_ref["A"], generic_no_feedback_hol["A"]) <= ERASURE_TOLERANCE
            and distance(generic_no_feedback_ref["B"], generic_no_feedback_hol["B"]) <= ERASURE_TOLERANCE
        )

        pair_rows.append({
            "pair_id": pair_id,
            "family": family,
            "reference_history": histories(family)[0],
            "holonomy_history": histories(family)[1],
            "phase_a_state_match": a_match,
            **{f"phase_a_{key}": value for key, value in a_features.items()},
            "phase_a_class2": a_pass,
            "phase_b_state_match": b_match,
            **{f"phase_b_{key}": value for key, value in b_features.items()},
            "phase_b_class2": b_class2,
            **o3_values,
            "phase_b_o3": o3_pass,
            "generic_class2": generic_class2,
            "generic_o3": generic_o3,
        })

        match_rows.append({
            "pair_id": pair_id,
            "family": family,
            "A_reference_sha256": phase_a["reference"]["pre_A"],
            "A_holonomy_sha256": phase_a["holonomy"]["pre_A"],
            "B_reference_sha256": phase_a["reference"]["pre_B"],
            "B_holonomy_sha256": phase_a["holonomy"]["pre_B"],
            "phase_a_exact_match": a_match,
            "phase_b_exact_match": b_match,
        })

        for control, true_class in REGISTERED_CONTROLS.items():
            control_outputs = all_outputs(lambda condition, control=control: native_condition(control, condition, family, base, donor, runtime_type, natural_lineage))
            features = class2_features(control_outputs, pair_id + ":" + control)
            declared = class2_decision(features, state_match(control_outputs))
            control_rows.append({
                "pair_id": pair_id,
                "family": family,
                "control": control,
                "registered_class": true_class,
                **features,
                "declared_class2": declared,
            })

    phase_a_count = sum(bool(row["phase_a_class2"]) for row in pair_rows)
    phase_b_count = sum(bool(row["phase_b_class2"]) for row in pair_rows)
    o3_count = sum(bool(row["phase_b_o3"]) for row in pair_rows)
    summary: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "complete",
        "mode": "confirmatory" if seed == PRIMARY_SEED else "sensitivity",
        "seed": seed,
        "pair_count": PAIR_COUNT,
        "phase_a_class2": output_summary(phase_a_count, PAIR_COUNT),
        "phase_b_class2": output_summary(phase_b_count, PAIR_COUNT),
        "phase_b_o3": output_summary(o3_count, PAIR_COUNT),
        "primary_decisions": {
            "phase_a_class2_pass": phase_a_count >= MIN_PRIMARY_PASSES,
            "phase_b_class2_pass": phase_b_count >= MIN_PRIMARY_PASSES,
            "phase_b_o3_pass": o3_count >= MIN_PRIMARY_PASSES,
        },
        "history_families": {},
        "controls": {},
        "matched_generic_control": {
            "class2": output_summary(sum(bool(row["generic_class2"]) for row in pair_rows), PAIR_COUNT),
            "o3": output_summary(sum(bool(row["generic_o3"]) for row in pair_rows), PAIR_COUNT),
            "interpretation": "A pass indicates implementation non-uniqueness.",
        },
        "optimization_budget": {
            "candidate_training_steps": 0,
            "control_training_steps": 0,
            "hyperparameter_searches": 0,
            "seed_selection": 0,
            "result_dependent_reinitializations": 0,
        },
    }
    for family in (0, 1):
        subset = [row for row in pair_rows if row["family"] == family]
        summary["history_families"][str(family)] = {
            "histories": list(histories(family)),
            "phase_a_class2": output_summary(sum(bool(row["phase_a_class2"]) for row in subset), len(subset)),
            "phase_b_class2": output_summary(sum(bool(row["phase_b_class2"]) for row in subset), len(subset)),
            "phase_b_o3": output_summary(sum(bool(row["phase_b_o3"]) for row in subset), len(subset)),
            "uniform_transfer_raw_threshold": MIN_FAMILY_RAW_PASSES,
        }
    for control in REGISTERED_CONTROLS:
        subset = [row for row in control_rows if row["control"] == control]
        false_count = sum(bool(row["declared_class2"]) for row in subset)
        summary["controls"][control] = {
            "registered_class": REGISTERED_CONTROLS[control],
            "false_class2": output_summary(false_count, len(subset)),
            "bound_pass": false_count <= MAX_FALSE_DECLARATIONS,
        }
    summary["primary_decisions"]["all_registered_null_bounds_pass"] = all(item["bound_pass"] for item in summary["controls"].values())
    summary["primary_decisions"]["uniform_history_family_transfer"] = all(
        summary["history_families"][str(family)][endpoint]["count"] >= MIN_FAMILY_RAW_PASSES
        for family in (0, 1)
        for endpoint in ("phase_a_class2", "phase_b_class2", "phase_b_o3")
    )
    summary["registered_claims"] = {
        "phase_a_class2_supported": bool(
            summary["primary_decisions"]["phase_a_class2_pass"]
            and summary["primary_decisions"]["all_registered_null_bounds_pass"]
        ),
        "phase_b_class2_supported": bool(
            summary["primary_decisions"]["phase_b_class2_pass"]
            and summary["primary_decisions"]["all_registered_null_bounds_pass"]
        ),
        "phase_b_o3_supported": bool(
            summary["primary_decisions"]["phase_b_o3_pass"]
            and summary["primary_decisions"]["phase_b_class2_pass"]
            and summary["primary_decisions"]["all_registered_null_bounds_pass"]
        ),
    }
    return pair_rows, control_rows, match_rows, summary


def render_result(summary: dict[str, Any]) -> str:
    decisions = summary["primary_decisions"]
    claims = summary["registered_claims"]
    return "\n".join((
        "# Experiment 003 Result",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Registered decisions",
        "",
        f"- Phase A Class 2 supported: `{claims['phase_a_class2_supported']}` ({summary['phase_a_class2']['count']}/128 positive units).",
        f"- Phase B Class 2 supported: `{claims['phase_b_class2_supported']}` ({summary['phase_b_class2']['count']}/128 positive units).",
        f"- Phase B O3 supported: `{claims['phase_b_o3_supported']}` ({summary['phase_b_o3']['count']}/128 positive units).",
        f"- All registered null bounds: `{decisions['all_registered_null_bounds_pass']}`.",
        f"- Uniform two-family transfer: `{decisions['uniform_history_family_transfer']}`.",
        "",
        "## Claim boundary",
        "",
        "These are operational construction and transfer results. They do not establish spontaneous emergence, ontological subjectivity, or ontological irreducibility.",
        "",
    ))


def main() -> None:
    args = parse_args()
    registration = verify_registration()
    private_verification = verify_private_sources(args.private_agent_root)
    if args.mode == "confirmatory":
        if args.seed not in (None, PRIMARY_SEED):
            fail(f"confirmatory seed must be {PRIMARY_SEED}")
        seed = PRIMARY_SEED
    else:
        if args.seed not in SENSITIVITY_SEEDS:
            fail("sensitivity seed is not registered")
        seed = int(args.seed)
    if args.out_dir.exists():
        fail("output directory already exists; refusing to overwrite")

    runtime_type, v89f = load_private_runtime(args.private_agent_root)
    pair_rows, control_rows, match_rows, summary = run_experiment(runtime_type, v89f.natural_lineage, seed)
    if args.check:
        if len(pair_rows) != PAIR_COUNT:
            fail("pair count mismatch")
        if len({row["pair_id"] for row in pair_rows}) != PAIR_COUNT:
            fail("pair identifiers are not unique")

    args.out_dir.mkdir(parents=True)
    pair_fields = list(pair_rows[0].keys())
    control_fields = list(control_rows[0].keys())
    match_fields = list(match_rows[0].keys())
    write_csv(args.out_dir / "pair_metrics.csv", pair_rows, pair_fields)
    write_csv(args.out_dir / "control_metrics.csv", control_rows, control_fields)
    write_csv(args.out_dir / "state_match_receipts.csv", match_rows, match_fields)
    source_receipt = {
        "registration_manifest_sha256": sha256_file(REGISTRATION_MANIFEST),
        "registration": registration,
        "private_source_verification": private_verification,
    }
    write_json(args.out_dir / "source_verification.json", source_receipt)
    write_json(args.out_dir / "summary.json", summary)
    (args.out_dir / "RESULT.md").write_text(render_result(summary), encoding="utf-8")
    output_files = sorted(path for path in args.out_dir.iterdir() if path.name != "output_manifest.json")
    write_json(args.out_dir / "output_manifest.json", {path.name: sha256_file(path) for path in output_files})
    print(json.dumps(summary["primary_decisions"], indent=2, sort_keys=True))
    print("wrote", args.out_dir)


if __name__ == "__main__":
    main()
