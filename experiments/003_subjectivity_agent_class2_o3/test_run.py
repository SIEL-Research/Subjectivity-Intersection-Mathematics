#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent static and mathematical tests for Experiment 003."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_003", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Experiment003Tests(unittest.TestCase):
    def test_registration_manifest(self):
        manifest = MODULE.verify_registration()
        self.assertEqual(manifest["experiment"], "Experiment 003")

    def test_pair_allocation(self):
        identifiers = [f"P{MODULE.PAIR_START + index}" for index in range(MODULE.PAIR_COUNT)]
        self.assertEqual(len(identifiers), 128)
        self.assertEqual(len(set(identifiers)), 128)
        self.assertEqual(identifiers[0], "P1000")
        self.assertEqual(identifiers[-1], "P1127")

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


if __name__ == "__main__":
    unittest.main()
