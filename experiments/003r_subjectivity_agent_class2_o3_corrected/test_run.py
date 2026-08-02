#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent static and mathematical tests for Experiment 003R."""

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_003", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


@dataclass
class MockState:
    numeric: list[float]
    fes_source: str = "source"
    fes_attribute: str = "attribute"
    fes_energy: str = "energy"
    fes_target: str = "target"
    fes_relation_mode: str = "relation"
    fes_relation_reason: str = "reason"
    remembered_other_signal: str = "other"
    self_change_vector: str = "change"
    other_model_summary: str = "other-model"
    self_update_summary: str = "self-update"
    learned_pattern: str = "pattern"
    raw_voice: str = "voice"


class MockRuntime:
    def __init__(self):
        self.turn = 0
        self.history = []
        self.memory = {}
        self.baseline = {"mock": True}

    def normalize_memory(self, memory):
        return memory

    def update(self, prompt):
        self.turn += 1
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        numeric = [((digest[index % len(digest)] / 127.5) - 1.0) for index in range(24)]
        state = MockState(numeric=numeric, raw_voice=prompt[:80])
        self.history.append(state)
        self.memory = {"events": [item.raw_voice for item in self.history]}
        return state


def mock_natural_lineage(state):
    return state.numeric


class Experiment003RTests(unittest.TestCase):
    def test_registration_manifest(self):
        manifest = MODULE.verify_registration()
        self.assertEqual(manifest["experiment"], "Experiment 003R")

    def test_pair_allocation(self):
        identifiers = [f"P{MODULE.PAIR_START + index}" for index in range(MODULE.PAIR_COUNT)]
        self.assertEqual(len(identifiers), 128)
        self.assertEqual(len(set(identifiers)), 128)
        self.assertEqual(identifiers[0], "P2000")
        self.assertEqual(identifiers[-1], "P2127")

    def test_distance_is_rms_euclidean(self):
        left = np.zeros(24, dtype=np.float64)
        right = np.ones(24, dtype=np.float64)
        self.assertAlmostEqual(MODULE.distance(left, right), 1.0)

    def test_embedding_is_unit_norm(self):
        vector = MODULE.embed_text("registered packet")
        self.assertEqual(vector.shape, (24,))
        self.assertAlmostEqual(float(np.linalg.norm(vector)), 1.0)

    def test_candidate_parameter_count(self):
        matrices = MODULE.orthogonal_matrices(MODULE.PRIMARY_SEED)
        self.assertEqual(len(matrices), 7)
        self.assertTrue(all(matrix.shape == (24, 24) for matrix in matrices))
        self.assertEqual(sum(matrix.size for matrix in matrices), 4032)

    def test_history_families(self):
        self.assertEqual(MODULE.histories(0), ("AABB", "ABAB"))
        self.assertEqual(MODULE.histories(1), ("BBAA", "BABA"))

    def test_wilson_registered_counts(self):
        lower_112, _ = MODULE.wilson_interval(112, 128)
        lower_111, _ = MODULE.wilson_interval(111, 128)
        _, upper_6 = MODULE.wilson_interval(6, 128)
        _, upper_7 = MODULE.wilson_interval(7, 128)
        self.assertGreater(lower_112, 0.80)
        self.assertLessEqual(lower_111, 0.80)
        self.assertLess(upper_6, 0.10)
        self.assertGreaterEqual(upper_7, 0.10)

    def test_gauge_is_isometric(self):
        left = np.arange(24, dtype=np.float64)
        right = np.arange(24, dtype=np.float64)[::-1]
        raw = MODULE.distance(left, right)
        transformed = MODULE.distance(
            MODULE.signed_permutation(left, "same-key"),
            MODULE.signed_permutation(right, "same-key"),
        )
        self.assertAlmostEqual(raw, transformed)

    def test_thresholds_are_frozen(self):
        self.assertEqual(MODULE.CLASS2_THRESHOLDS, {
            "joint_generation": 0.0672948624,
            "history_irreducibility": 0.0551607125,
            "intervention_sensitivity": 0.0868509258,
            "pair_specificity": 0.0707154800,
            "bilateral_feedback": 0.0654685289,
        })

    def test_phase_b_control_inventory_is_exact(self):
        self.assertEqual(MODULE.REGISTERED_PHASE_B_CONTROLS, frozenset({
            "self_reentry_erasure",
            "carrier_reset",
            "native_archive_reset",
            "order_erasure",
            "current_input_only",
            "direct_carrier_output",
            "unilateral_return_A",
            "unilateral_return_B",
            "bilateral_feedback_removal",
            "completed_C_exchange",
            "selective_C_reset",
        }))

    def test_native_pair_exchange_inserts_completed_donor_c(self):
        base = MODULE.build_base(MODULE.PAIR_START, MockRuntime)
        donor = MODULE.build_base(MODULE.PAIR_START + 65, MockRuntime)
        exchanged = MODULE.native_condition(
            "candidate",
            "pair_exchange",
            0,
            1,
            base,
            donor,
            MockRuntime,
            mock_natural_lineage,
        )
        completed_donor = MODULE.build_native_c(
            "candidate",
            "holonomy",
            1,
            donor,
            MockRuntime,
            mock_natural_lineage,
        )
        self.assertEqual(exchanged["carrier_source"], "completed_donor_C")
        np.testing.assert_allclose(exchanged["C"], completed_donor["K_AB"])

    def test_o3_control_runner_executes_registered_inventory(self):
        base = MODULE.build_base(MODULE.PAIR_START, MockRuntime)
        donor = MODULE.build_base(MODULE.PAIR_START + 65, MockRuntime)
        controls = MODULE.phase_b_control_outputs(
            0,
            1,
            base,
            donor,
            MockRuntime,
            mock_natural_lineage,
            seed=MODULE.PRIMARY_SEED,
        )
        self.assertEqual(frozenset(controls), MODULE.REGISTERED_PHASE_B_CONTROLS)
        self.assertEqual(
            controls["completed_C_exchange"]["carrier_source"],
            "completed_donor_C",
        )


if __name__ == "__main__":
    unittest.main()
