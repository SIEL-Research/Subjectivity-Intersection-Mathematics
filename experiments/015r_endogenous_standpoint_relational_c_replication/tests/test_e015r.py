#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_e015r", ROOT / "run.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_confirmatory_seeds_are_fresh_and_fixed():
    assert MODULE.CONFIRMATORY_SEEDS == tuple(range(98100, 98148))
    assert not set(MODULE.CONFIRMATORY_SEEDS) & set(MODULE.TEST_SEEDS)
    assert not set(MODULE.CONFIRMATORY_SEEDS) & set(range(73000, 73228))
    assert not set(MODULE.CONFIRMATORY_SEEDS) & set(range(91000, 97132))


def test_base_runner_identity_is_frozen():
    assert MODULE.sha256(MODULE.BASE_PATH) == MODULE.BASE_SHA256


def test_rename_and_channel_permutation_preserve_agent_view():
    episode = MODULE.BASE.generate_episode(96000123, port_swap=True)
    renamed = MODULE.renamed_episode(episode)
    permuted = MODULE.channel_permuted_episode(episode)
    for observer in (0, 1):
        original = MODULE.BASE.build_view(episode, observer, 0)
        renamed_view = MODULE.BASE.build_view(renamed, 1 - observer, 0)
        permuted_view = MODULE.BASE.build_view(permuted, observer, 0)
        assert MODULE.view_difference(original, renamed_view) == 0.0
        assert MODULE.view_difference(
            original,
            permuted_view,
            include_fixed_position_control=False,
        ) == 0.0


def test_renaming_preserves_weights_states_predictions_and_c():
    episodes = [
        MODULE.BASE.generate_episode(96001000 + index, port_swap=(index % 2 == 1))
        for index in range(4)
    ]
    renamed = [MODULE.renamed_episode(episode) for episode in episodes]
    views = [
        MODULE.BASE.build_view(episode, observer, index)
        for index, episode in enumerate(episodes)
        for observer in (0, 1)
    ]
    renamed_views = [
        MODULE.BASE.build_view(episode, 1 - observer, index)
        for index, episode in enumerate(renamed)
        for observer in (0, 1)
    ]
    for left, right in zip(views, renamed_views):
        assert MODULE.view_difference(left, right) == 0.0
    left_model = MODULE.BASE.train_reservoir(96002000, "connected", views)
    right_model = MODULE.BASE.train_reservoir(96002000, "connected", renamed_views)
    assert np.array_equal(left_model.inputs, right_model.inputs)
    assert np.array_equal(left_model.bias, right_model.bias)
    left_states = MODULE.BASE.four_history_states(left_model, views[0].x)
    right_states = MODULE.BASE.four_history_states(right_model, renamed_views[0].x)
    for name in left_states:
        assert np.array_equal(left_states[name], right_states[name])
    assert np.array_equal(
        MODULE.BASE.component(left_states), MODULE.BASE.component(right_states)
    )
    left_beta = MODULE.BASE.fit_readout(left_model, views)
    right_beta = MODULE.BASE.fit_readout(right_model, renamed_views)
    assert np.array_equal(left_beta, right_beta)
    assert np.array_equal(
        MODULE.BASE.predict(left_beta, left_states["ab"]),
        MODULE.BASE.predict(right_beta, right_states["ab"]),
    )


def test_observation_only_lookup_is_at_chance_by_paired_symmetry():
    training = [
        MODULE.BASE.generate_episode(96003000 + index, port_swap=False)
        for index in range(3)
    ]
    testing = [
        MODULE.BASE.generate_episode(96004000 + index, port_swap=True)
        for index in range(3)
    ]
    assert MODULE.observation_only_accuracy(training, testing) == 0.5


def test_additive_c_is_numerical_zero_and_no_c_register_exists():
    episode = MODULE.BASE.generate_episode(96005000, port_swap=False)
    views = [MODULE.BASE.build_view(episode, observer, 0) for observer in (0, 1)]
    connected = MODULE.BASE.train_reservoir(96005001, "connected", views)
    additive = MODULE.BASE.train_reservoir(96005002, "additive", views)
    assert connected.inputs.shape == additive.inputs.shape == (
        MODULE.BASE.STATE_DIM,
        MODULE.BASE.INPUT_DIM,
    )
    additive_c = MODULE.BASE.component(
        MODULE.BASE.four_history_states(additive, views[0].x)
    )
    assert float(np.max(np.abs(additive_c))) < 1e-12


def test_intervention_metrics_execute_on_specification_data():
    episode = MODULE.BASE.generate_episode(96006000, port_swap=False)
    views = [MODULE.BASE.build_view(episode, observer, 0) for observer in (0, 1)]
    connected = MODULE.BASE.train_reservoir(96006001, "connected", views)
    additive = MODULE.BASE.train_reservoir(96006002, "additive", views)
    beta = MODULE.BASE.fit_readout(connected, views)
    rng = np.random.default_rng(96006003)
    records = [
        MODULE.BASE.view_component_record(connected, additive, beta, view, rng)
        for view in views
    ]
    metrics = MODULE.intervention_metrics(connected, beta, views, records)
    assert set(metrics) == {
        "state_only_exchange_effect",
        "coherent_exchange_error",
        "reentry_reconstruction_error",
    }
    assert all(np.isfinite(value) for value in metrics.values())


def test_scientific_baseline_is_passed_but_execution_remains_doi_gated():
    gate = MODULE.verify_baseline_gate()
    assert gate["scientific_baseline_authorized"] is True
    assert gate["confirmatory_execution_authorized"] is False


def test_doi1_gate_is_hard_blocked_before_verified_receipt():
    receipt = ROOT / "registration_receipt.json"
    if receipt.exists():
        verified = MODULE.verify_doi1_gate(ROOT / "FROZEN_MANIFEST.sha256")
        assert verified["status"] == "PASS"
        return
    try:
        MODULE.verify_doi1_gate(ROOT / "FROZEN_MANIFEST.sha256")
    except SystemExit as error:
        assert "registration_receipt.json is absent" in str(error)
    else:
        raise AssertionError("E-DOI-1 did not block execution")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"E015R specification tests passed: {len(tests)}")
