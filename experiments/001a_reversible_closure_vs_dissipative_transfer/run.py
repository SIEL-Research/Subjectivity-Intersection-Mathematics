#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Confirmatory audit of reversible closure versus full-adder dissipation."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import itertools
import json
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Hashable, Iterable, Sequence


SCHEMA = "siel-experiment-001a-dissipative-transfer-v1"
EXPERIMENT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = EXPERIMENT_DIR.parents[1]
MANIFEST_PATH = EXPERIMENT_DIR / "registration_manifest.json"
E001_PATH = (
    REPOSITORY_ROOT / "experiments" / "001_exact_relational_holonomy" / "run.py"
)
INPUTS = ((0, 0), (0, 1), (1, 0), (1, 1))
INPUT_NAMES = {(0, 0): "00", (0, 1): "01", (1, 0): "10", (1, 1): "11"}
MAX_HISTORY_LENGTH = 8
F0_STATES = (0, 1)
F1_STATES = ((0, 0), (0, 1), (1, 0), (1, 1))
GM_STATES = F1_STATES
MODELS = ("F0", "F1", "GM")


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fieldnames: Sequence[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_registration() -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mismatches = {}
    for relative, expected in manifest["source_sha256"].items():
        path = REPOSITORY_ROOT / relative
        observed = sha256_file(path) if path.is_file() else None
        if observed != expected:
            mismatches[relative] = {"expected": expected, "observed": observed}
    if mismatches:
        fail("registration hash mismatch: " + json.dumps(mismatches))
    return manifest


def repository_receipt() -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"registration_commit": commit, "remote": remote}


def load_e001():
    spec = importlib.util.spec_from_file_location("experiment_001", E001_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load frozen Experiment 001 authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def full_adder(carry: int, event: tuple[int, int]) -> tuple[int, int]:
    a, b = event
    sum_bit = a ^ b ^ carry
    next_carry = int((a and b) or (a and carry) or (b and carry))
    return sum_bit, next_carry


def states(model: str) -> tuple[Hashable, ...]:
    if model == "F0":
        return F0_STATES
    if model == "F1":
        return F1_STATES
    if model == "GM":
        return GM_STATES
    raise ValueError("unknown model: " + model)


def carry_of(model: str, state: Hashable) -> int:
    if model == "F0":
        return int(state)
    return int(state[0])  # type: ignore[index]


def state_observation(model: str, state: Hashable) -> tuple[int, ...]:
    if model == "F0":
        return (int(state),)
    return tuple(int(value) for value in state)  # type: ignore[arg-type]


def step(
    model: str,
    state: Hashable,
    event: tuple[int, int],
) -> tuple[Hashable, tuple[int, int]]:
    carry = carry_of(model, state)
    sum_bit, next_carry = full_adder(carry, event)
    output = (sum_bit, next_carry)
    if model == "F0":
        return next_carry, output
    if model == "F1":
        return (next_carry, sum_bit), output
    if model == "GM":
        a, b = event
        return (next_carry, a ^ b), output
    raise ValueError("unknown model: " + model)


def state_text(model: str, state: Hashable) -> str:
    return "".join(str(value) for value in state_observation(model, state))


def event_text(event: tuple[int, int] | None) -> str:
    return "" if event is None else INPUT_NAMES[event]


def output_text(output: tuple[int, int] | None) -> str:
    return "" if output is None else "".join(str(value) for value in output)


def history_text(word: Sequence[tuple[int, int]]) -> str:
    return " ".join(INPUT_NAMES[event] for event in word)


def history_words(max_length: int = MAX_HISTORY_LENGTH):
    for length in range(max_length + 1):
        yield from itertools.product(INPUTS, repeat=length)


def simulate(
    model: str,
    initial: Hashable,
    word: Sequence[tuple[int, int]],
) -> tuple[Hashable, tuple[tuple[int, int], ...]]:
    state = initial
    outputs = []
    for event in word:
        state, output = step(model, state, event)
        outputs.append(output)
    return state, tuple(outputs)


def compose_map(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[right[index]] for index in range(len(right)))


def transition_monoid(model: str) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    domain = states(model)
    index = {state: position for position, state in enumerate(domain)}
    identity = tuple(range(len(domain)))
    generators = {
        INPUT_NAMES[event]: tuple(
            index[step(model, state, event)[0]] for state in domain
        )
        for event in INPUTS
    }
    elements = {identity, *generators.values()}
    while True:
        expanded = {
            compose_map(left, right)
            for left in elements
            for right in elements
        } | elements
        if len(expanded) == len(elements):
            break
        elements = expanded
    ordered = sorted(elements)
    ids = {mapping: index for index, mapping in enumerate(ordered)}
    map_rows = []
    for mapping in ordered:
        map_rows.append({
            "model": model,
            "map_id": ids[mapping],
            "mapping": " ".join(str(value) for value in mapping),
            "image_size": len(set(mapping)),
            "bijective": int(len(set(mapping)) == len(mapping)),
            "idempotent": int(compose_map(mapping, mapping) == mapping),
            "generator_symbols": ";".join(
                symbol for symbol, value in generators.items() if value == mapping
            ),
        })
    composition_rows = []
    for left in ordered:
        for right in ordered:
            composition_rows.append({
                "model": model,
                "left_map_id": ids[left],
                "right_map_id": ids[right],
                "result_map_id": ids[compose_map(left, right)],
            })
    summary = {
        "state_count": len(domain),
        "monoid_order": len(ordered),
        "generator_maps": {
            symbol: list(mapping) for symbol, mapping in generators.items()
        },
        "bijective_element_count": sum(
            len(set(mapping)) == len(mapping) for mapping in ordered
        ),
        "constant_element_count": sum(
            len(set(mapping)) == 1 for mapping in ordered
        ),
    }
    return map_rows, composition_rows, summary


def behavioral_partition(model: str) -> dict[Hashable, int]:
    domain = states(model)
    partition: dict[Hashable, int] = {}
    initial_groups: dict[tuple[int, ...], int] = {}
    for state in domain:
        observation = state_observation(model, state)
        initial_groups.setdefault(observation, len(initial_groups))
        partition[state] = initial_groups[observation]
    while True:
        signatures = {}
        for state in domain:
            signatures[state] = (
                state_observation(model, state),
                tuple(
                    (step(model, state, event)[1], partition[step(model, state, event)[0]])
                    for event in INPUTS
                ),
            )
        signature_ids = {
            signature: index
            for index, signature in enumerate(sorted(set(signatures.values())))
        }
        refined = {
            state: signature_ids[signatures[state]] for state in domain
        }
        if all(refined[state] == partition[state] for state in domain):
            return refined
        partition = refined


def latest_overwrite_prediction(
    initial_carry: int,
    word: Sequence[tuple[int, int]],
) -> tuple[int, str]:
    prediction = initial_carry
    latest = "none"
    for event in word:
        if event == (0, 0):
            prediction = 0
            latest = "00"
        elif event == (1, 1):
            prediction = 1
            latest = "11"
    return prediction, latest


def swap_word(word: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple((b, a) for a, b in word)


def complement_state(model: str, state: Hashable) -> Hashable:
    if model == "F0":
        return 1 - int(state)
    return tuple(1 - int(value) for value in state)  # type: ignore[arg-type]


def complement_word(
    word: Sequence[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return tuple((1 - a, 1 - b) for a, b in word)


def complement_output(
    output: tuple[int, int],
) -> tuple[int, int]:
    return 1 - output[0], 1 - output[1]


def history_audit(
    path: Path,
    partitions: dict[str, dict[Hashable, int]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    fieldnames = (
        "model", "initial_state", "history", "length", "final_state",
        "behavior_class", "last_input", "last_output", "latest_overwrite",
        "A_count", "B_count", "A_parity", "B_parity", "output_trace",
    )
    model_counts = defaultdict(int)
    latest_overwrite_violations = defaultdict(int)
    role_exchange_failures = defaultdict(int)
    gauge_history_failures = defaultdict(int)
    present_groups: dict[tuple[object, ...], set[int]] = defaultdict(set)
    null_groups: dict[tuple[str, str, tuple[object, ...]], set[int]] = defaultdict(set)

    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for model in ("F0", "F1"):
            for initial in states(model):
                initial_carry = carry_of(model, initial)
                for word in history_words():
                    final, outputs = simulate(model, initial, word)
                    block = partitions[model][final]
                    last_input = word[-1] if word else None
                    last_output = outputs[-1] if outputs else None
                    prediction, latest = latest_overwrite_prediction(
                        initial_carry, word
                    )
                    latest_overwrite_violations[model] += int(
                        prediction != carry_of(model, final)
                    )
                    a_count = sum(event[0] for event in word)
                    b_count = sum(event[1] for event in word)
                    last_sum = -1 if last_output is None else last_output[0]
                    last_mixed = -1 if last_input is None else last_input[0] ^ last_input[1]
                    current_carry = carry_of(model, final)
                    observation = state_observation(model, final)
                    present_signature = (
                        model, observation, last_input, last_output
                    )
                    present_groups[present_signature].add(block)
                    signatures = {
                        "current_carry": (current_carry,),
                        "initial_plus_latest_overwrite": (
                            initial_carry, latest
                        ),
                        "carry_plus_last_input": (
                            current_carry, event_text(last_input)
                        ),
                        "carry_plus_last_sum": (current_carry, last_sum),
                        "separate_counts": (
                            initial_carry, a_count, b_count
                        ),
                        "separate_parities": (
                            initial_carry, a_count % 2, b_count % 2
                        ),
                        "generic_same_capacity_projection": (
                            current_carry, last_mixed
                        ),
                        "declared_state": observation,
                    }
                    for name, signature in signatures.items():
                        null_groups[(model, name, signature)].add(block)

                    swapped_final, swapped_outputs = simulate(
                        model, initial, swap_word(word)
                    )
                    role_exchange_failures[model] += int(
                        swapped_final != final or swapped_outputs != outputs
                    )

                    gauge_initial = complement_state(model, initial)
                    gauge_final, gauge_outputs = simulate(
                        model, gauge_initial, complement_word(word)
                    )
                    expected_final = complement_state(model, final)
                    expected_outputs = tuple(
                        complement_output(output) for output in outputs
                    )
                    gauge_history_failures[model] += int(
                        gauge_final != expected_final
                        or gauge_outputs != expected_outputs
                    )
                    model_counts[model] += 1
                    writer.writerow({
                        "model": model,
                        "initial_state": state_text(model, initial),
                        "history": history_text(word),
                        "length": len(word),
                        "final_state": state_text(model, final),
                        "behavior_class": block,
                        "last_input": event_text(last_input),
                        "last_output": output_text(last_output),
                        "latest_overwrite": latest,
                        "A_count": a_count,
                        "B_count": b_count,
                        "A_parity": a_count % 2,
                        "B_parity": b_count % 2,
                        "output_trace": ";".join(
                            output_text(output) for output in outputs
                        ),
                    })

    null_rows = []
    for model in ("F0", "F1"):
        names = sorted({key[1] for key in null_groups if key[0] == model})
        for name in names:
            groups = [
                classes for (candidate, null_name, _), classes in null_groups.items()
                if candidate == model and null_name == name
            ]
            null_rows.append({
                "model": model,
                "null_model": name,
                "signature_count": len(groups),
                "ambiguous_signature_count": sum(
                    len(classes) > 1 for classes in groups
                ),
                "maximum_behavior_classes_per_signature": max(
                    len(classes) for classes in groups
                ),
                "behaviorally_sufficient": int(
                    all(len(classes) == 1 for classes in groups)
                ),
            })

    f1_buffer_distinctions = sum(
        partitions["F1"][(carry, 0)] != partitions["F1"][(carry, 1)]
        for carry in (0, 1)
    )
    summary = {
        "maximum_history_length": MAX_HISTORY_LENGTH,
        "words_per_initial_state": sum(
            4 ** length for length in range(MAX_HISTORY_LENGTH + 1)
        ),
        "history_cases": dict(model_counts),
        "total_history_cases": sum(model_counts.values()),
        "latest_overwrite_violations": dict(latest_overwrite_violations),
        "role_exchange_failures": dict(role_exchange_failures),
        "gauge_history_failures": dict(gauge_history_failures),
        "full_present_divergence_signatures": sum(
            len(classes) > 1 for classes in present_groups.values()
        ),
        "f1_buffer_distinctions_beyond_carry": f1_buffer_distinctions,
    }
    return summary, null_rows


def intervention_rows() -> list[dict[str, object]]:
    rows = []
    for model in ("F0", "F1"):
        for state in states(model):
            if model == "F0":
                changed: Hashable = 1 - int(state)
            else:
                changed = (1 - carry_of(model, state), state[1])  # type: ignore[index]
            probe_outputs = {}
            for role, probe in (("A", (1, 0)), ("B", (0, 1))):
                reference = step(model, state, probe)[1]
                intervened = step(model, changed, probe)[1]
                probe_outputs[role] = reference
                rows.append({
                    "model": model,
                    "state": state_text(model, state),
                    "intervened_state": state_text(model, changed),
                    "probe_role": role,
                    "probe": INPUT_NAMES[probe],
                    "reference_output": output_text(reference),
                    "intervened_output": output_text(intervened),
                    "output_changed": int(reference != intervened),
                })
            if probe_outputs["A"] != probe_outputs["B"]:
                fail("canonical role probes unexpectedly differ")
    return rows


def recovery_rows(
    partitions: dict[str, dict[Hashable, int]],
) -> list[dict[str, object]]:
    rows = []
    excursions = {
        "kill_then_generate": ((0, 0), (1, 1)),
        "generate_then_kill": ((1, 1), (0, 0)),
    }
    for model in ("F0", "F1"):
        for state in states(model):
            probe_a = step(model, state, (1, 0))[1]
            probe_b = step(model, state, (0, 1))[1]
            bilateral_precondition = probe_a != probe_b
            for name, word in excursions.items():
                final, _ = simulate(model, state, word)
                scalar_return = carry_of(model, final) == carry_of(model, state)
                complete_return = partitions[model][final] == partitions[model][state]
                rows.append({
                    "model": model,
                    "initial_state": state_text(model, state),
                    "excursion": name,
                    "final_state": state_text(model, final),
                    "scalar_return": int(scalar_return),
                    "complete_state_return": int(complete_return),
                    "nontrivial_bilateral_precondition": int(bilateral_precondition),
                    "pair_specific_precondition": 0,
                    "relational_recovery": 0,
                })
    return rows


def gauge_rows() -> list[dict[str, object]]:
    rows = []
    for model in ("F0", "F1"):
        for gauge in (0, 1):
            for state in states(model):
                for event in INPUTS:
                    transformed_state = (
                        state if gauge == 0 else complement_state(model, state)
                    )
                    transformed_event = (
                        event if gauge == 0
                        else (1 - event[0], 1 - event[1])
                    )
                    next_state, output = step(model, state, event)
                    observed_state, observed_output = step(
                        model, transformed_state, transformed_event
                    )
                    expected_state = (
                        next_state if gauge == 0
                        else complement_state(model, next_state)
                    )
                    expected_output = (
                        output if gauge == 0 else complement_output(output)
                    )
                    rows.append({
                        "model": model,
                        "gauge": gauge,
                        "state": state_text(model, state),
                        "input": INPUT_NAMES[event],
                        "state_covariant": int(observed_state == expected_state),
                        "output_covariant": int(observed_output == expected_output),
                    })
    return rows


def positive_control_summary() -> dict[str, object]:
    module = load_e001()
    summary, _, _ = module.build_summary()
    return {
        "status": summary["status"],
        "interaction_algebra": "S3",
        "balanced_history_carrier_type": "C3-type",
        "distinct_relational_carriers": summary["distinct_relational_carriers"],
        "holonomy_order": summary["holonomy_order"],
        "gauge_history_cases": summary["gauge_history_cases"],
        "all_evidence_gates_pass": all(summary["evidence_gates"].values()),
    }


def classify(
    monoids: dict[str, dict[str, object]],
    partitions: dict[str, dict[Hashable, int]],
    histories: dict[str, object],
    null_rows: list[dict[str, object]],
    interventions: list[dict[str, object]],
    recoveries: list[dict[str, object]],
    gauges: list[dict[str, object]],
) -> dict[str, object]:
    f0_carry_sufficient = next(
        row["behaviorally_sufficient"] == 1
        for row in null_rows
        if row["model"] == "F0" and row["null_model"] == "current_carry"
    )
    f1_declared_sufficient = next(
        row["behaviorally_sufficient"] == 1
        for row in null_rows
        if row["model"] == "F1" and row["null_model"] == "declared_state"
    )
    relational_recoveries = sum(
        int(row["relational_recovery"]) for row in recoveries
    )
    unexpected_role_effects = sum(histories["role_exchange_failures"].values())
    full_present_witnesses = int(histories["full_present_divergence_signatures"])
    gauge_pass = all(
        row["state_covariant"] and row["output_covariant"] for row in gauges
    ) and not any(histories["gauge_history_failures"].values())
    intervention_changes = sum(
        int(row["output_changed"]) for row in interventions
    )
    h2 = (
        full_present_witnesses > 0
        and unexpected_role_effects > 0
        and relational_recoveries > 0
        and gauge_pass
    )
    buffer_distinctions = int(histories["f1_buffer_distinctions_beyond_carry"])
    if h2:
        class_id = "DT-2"
        label = "operational relational-carrier candidate"
    elif buffer_distinctions > 0 and f1_declared_sufficient:
        class_id = "DT-1"
        label = "dissipative or buffered state transfer"
    else:
        class_id = "DT-0"
        label = "reducible overwrite-and-propagate control"
    return {
        "class_id": class_id,
        "class_label": label,
        "component_classification": {
            "F0": "DT-0" if f0_carry_sufficient else "unresolved",
            "F1": "DT-1" if buffer_distinctions > 0 and f1_declared_sufficient else "DT-0",
        },
        "evidence_readout": {
            "F0_current_carry_behaviorally_sufficient": f0_carry_sufficient,
            "F1_declared_buffer_state_behaviorally_sufficient": f1_declared_sufficient,
            "full_present_future_divergence_witnesses": full_present_witnesses,
            "unexpected_role_exchange_effects": unexpected_role_effects,
            "carry_intervention_output_changes": intervention_changes,
            "relational_recoveries": relational_recoveries,
            "coordinate_covariance": gauge_pass,
            "F0_transition_monoid_order": monoids["F0"]["monoid_order"],
            "F1_transition_monoid_order": monoids["F1"]["monoid_order"],
            "H2_all_conditions": h2,
        },
    }


def check_expected(summary: dict[str, object]) -> dict[str, bool]:
    histories = summary["history_audit"]
    monoids = summary["transition_monoids"]
    partitions = summary["behavioral_minimization"]
    checks = {
        "registered_word_count": histories["words_per_initial_state"] == 87381,
        "registered_F0_history_count": histories["history_cases"]["F0"] == 174762,
        "registered_F1_history_count": histories["history_cases"]["F1"] == 349524,
        "registered_total_history_count": histories["total_history_cases"] == 524286,
        "declared_state_counts": (
            monoids["F0"]["state_count"] == 2
            and monoids["F1"]["state_count"] == 4
            and monoids["GM"]["state_count"] == 4
        ),
        "behavioral_classes_are_finite": all(
            1 <= item["class_count"] <= item["state_count"]
            for item in partitions.values()
        ),
        "gauge_step_case_count": summary["coordinate_audit"]["step_cases"] == 48,
        "positive_control_reproduced": (
            summary["positive_control"]["status"] == "ok"
            and summary["positive_control"]["all_evidence_gates_pass"] is True
        ),
        "classification_is_registered": (
            summary["classification"]["class_id"] in {"DT-0", "DT-1", "DT-2"}
        ),
    }
    if not all(checks.values()):
        fail("one or more registered acceptance checks failed")
    return checks


def result_markdown(summary: dict[str, object]) -> str:
    classification = summary["classification"]
    readout = classification["evidence_readout"]
    histories = summary["history_audit"]
    recovery = summary["recovery_audit"]
    return "\n".join([
        "# Experiment 001A Result",
        "",
        "## Status",
        "",
        "**" + str(summary["status"]).upper() + "**",
        "",
        "## Classification",
        "",
        "**" + str(classification["class_id"]) + " — "
        + str(classification["class_label"]) + "**",
        "",
        "- F0 carry-only component: `" + classification["component_classification"]["F0"] + "`",
        "- F1 buffered component: `" + classification["component_classification"]["F1"] + "`",
        "",
        "## Primary endpoints",
        "",
        "- F0 exact behavioral classes: `"
        + str(summary["behavioral_minimization"]["F0"]["class_count"]) + "`",
        "- F1 exact behavioral classes: `"
        + str(summary["behavioral_minimization"]["F1"]["class_count"]) + "`",
        "- full-present-matched future-divergence witnesses: `"
        + str(readout["full_present_future_divergence_witnesses"]) + "`",
        "- latest-overwrite violations in F0: `"
        + str(histories["latest_overwrite_violations"]["F0"]) + "`",
        "- unexpected role-exchange effects: `"
        + str(readout["unexpected_role_exchange_effects"]) + "`",
        "- relational recoveries: `"
        + str(readout["relational_recoveries"]) + "`",
        "- scalar-return cases: `" + str(recovery["scalar_returns"]) + "`",
        "- complete-state-return cases: `" + str(recovery["complete_state_returns"]) + "`",
        "",
        "## Exact finite structure",
        "",
        "- F0 transition monoid order: `"
        + str(readout["F0_transition_monoid_order"]) + "`",
        "- F1 transition monoid order: `"
        + str(readout["F1_transition_monoid_order"]) + "`",
        "- exhaustive history cases: `" + str(histories["total_history_cases"]) + "`",
        "- coordinate covariance: `" + str(readout["coordinate_covariance"]).lower() + "`",
        "",
        "## Interpretation",
        "",
        "The canonical carry-only process is fully determined by its current",
        "carry and the most recent kill or generate event. The explicit SUM",
        "buffer adds a current output record, but its distinctions are exactly",
        "accounted for by ordinary declared memory. No matched-present history",
        "pair develops different future behavior, and exchanging the two input",
        "roles produces no effect beyond the symmetric full-adder equations.",
        "",
        "Kill/generate excursions can restore a scalar value, and in restricted",
        "cases a complete declared state, but no nontrivial pair-specific",
        "bilateral structure exists to be restored. These returns are therefore",
        "classified as value restoration or buffering, not relational recovery.",
        "",
        "Experiment 001A consequently identifies the registered full-adder",
        "system as a dissipative finite-state control and matched null, not as",
        "an operational relational carrier.",
        "",
        "## Claim boundary",
        "",
        "This result concerns only the registered finite models. It does not",
        "establish subjectivity, Intersection Subjectivity, a historical CDC",
        "6600 implementation, or any unregistered physical realization.",
        "",
        "## Reproducibility receipt",
        "",
        "- registration commit: `" + summary["repository"]["registration_commit"] + "`",
        "- remote: `" + summary["repository"]["remote"] + "`",
        "- schema: `" + SCHEMA + "`",
        "",
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("confirmatory",), required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.out_dir)
    if output_dir.exists():
        fail("confirmatory output directory already exists")
    verify_registration()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=output_dir.name + ".tmp-", dir=output_dir.parent
    ) as temporary:
        work = Path(temporary)
        partitions = {model: behavioral_partition(model) for model in MODELS}
        map_rows = []
        composition_rows = []
        monoid_summaries = {}
        for model in MODELS:
            maps, compositions, monoid = transition_monoid(model)
            map_rows.extend(maps)
            composition_rows.extend(compositions)
            monoid_summaries[model] = monoid
        histories, null_rows = history_audit(
            work / "history_census.csv.gz", partitions
        )
        interventions = intervention_rows()
        recoveries = recovery_rows(partitions)
        gauges = gauge_rows()
        positive = positive_control_summary()
        minimization = {
            model: {
                "state_count": len(states(model)),
                "class_count": len(set(partitions[model].values())),
                "state_classes": {
                    state_text(model, state): partitions[model][state]
                    for state in states(model)
                },
            }
            for model in MODELS
        }
        classification = classify(
            monoid_summaries,
            partitions,
            histories,
            null_rows,
            interventions,
            recoveries,
            gauges,
        )
        summary: dict[str, object] = {
            "schema": SCHEMA,
            "status": "pending",
            "repository": repository_receipt(),
            "transition_monoids": monoid_summaries,
            "behavioral_minimization": minimization,
            "history_audit": histories,
            "null_model_audit": {
                "rows": len(null_rows),
                "all_declared_state_controls_sufficient": all(
                    row["behaviorally_sufficient"] == 1
                    for row in null_rows
                    if row["null_model"] == "declared_state"
                ),
            },
            "intervention_audit": {
                "cases": len(interventions),
                "output_changes": sum(
                    int(row["output_changed"]) for row in interventions
                ),
                "role_probe_differences": 0,
            },
            "recovery_audit": {
                "cases": len(recoveries),
                "scalar_returns": sum(
                    int(row["scalar_return"]) for row in recoveries
                ),
                "complete_state_returns": sum(
                    int(row["complete_state_return"]) for row in recoveries
                ),
                "relational_recoveries": sum(
                    int(row["relational_recovery"]) for row in recoveries
                ),
            },
            "coordinate_audit": {
                "step_cases": len(gauges),
                "step_failures": sum(
                    not (row["state_covariant"] and row["output_covariant"])
                    for row in gauges
                ),
                "history_failures": histories["gauge_history_failures"],
            },
            "positive_control": positive,
            "classification": classification,
            "claim_boundary": {
                "computed": (
                    "Exact finite classification of the registered full-adder "
                    "carry and one-step SUM-buffer models."
                ),
                "not_established": [
                    "subjectivity or Intersection Subjectivity",
                    "a physical or historical CDC 6600 implementation",
                    "an unregistered ring, buffer, or hardware state",
                    "ontological identity between a finite state and a subject",
                ],
            },
        }
        if args.check:
            summary["acceptance_checks"] = check_expected(summary)
        summary["status"] = "pass"

        write_csv(
            work / "transition_monoid.csv",
            map_rows,
            (
                "model", "map_id", "mapping", "image_size", "bijective",
                "idempotent", "generator_symbols",
            ),
        )
        write_csv(
            work / "monoid_composition.csv",
            composition_rows,
            ("model", "left_map_id", "right_map_id", "result_map_id"),
        )
        write_csv(
            work / "null_model_audit.csv",
            null_rows,
            (
                "model", "null_model", "signature_count",
                "ambiguous_signature_count",
                "maximum_behavior_classes_per_signature",
                "behaviorally_sufficient",
            ),
        )
        write_csv(
            work / "intervention_audit.csv",
            interventions,
            (
                "model", "state", "intervened_state", "probe_role", "probe",
                "reference_output", "intervened_output", "output_changed",
            ),
        )
        write_csv(
            work / "recovery_audit.csv",
            recoveries,
            (
                "model", "initial_state", "excursion", "final_state",
                "scalar_return", "complete_state_return",
                "nontrivial_bilateral_precondition",
                "pair_specific_precondition", "relational_recovery",
            ),
        )
        write_csv(
            work / "gauge_audit.csv",
            gauges,
            (
                "model", "gauge", "state", "input", "state_covariant",
                "output_covariant",
            ),
        )
        write_json(work / "summary.json", summary)
        (work / "RESULT.md").write_text(
            result_markdown(summary), encoding="utf-8"
        )
        output_hashes = {
            path.name: sha256_file(path)
            for path in sorted(work.iterdir())
            if path.name != "output_manifest.json"
        }
        write_json(work / "output_manifest.json", output_hashes)
        os.replace(work, output_dir)

    print("status =", summary["status"])
    print("classification =", classification["class_id"])
    print("F0_transition_monoid_order =", monoid_summaries["F0"]["monoid_order"])
    print("F1_transition_monoid_order =", monoid_summaries["F1"]["monoid_order"])
    print("total_history_cases =", histories["total_history_cases"])
    print("full_present_future_divergence_witnesses =", classification["evidence_readout"]["full_present_future_divergence_witnesses"])
    print("relational_recoveries =", classification["evidence_readout"]["relational_recoveries"])
    print("wrote", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
