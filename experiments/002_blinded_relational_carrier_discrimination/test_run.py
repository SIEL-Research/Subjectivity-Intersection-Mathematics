#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for Experiment 002 preregistered mechanics."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment002", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)


class ExactCarrierTests(unittest.TestCase):
    def test_exact_registered_checks(self) -> None:
        self.assertTrue(all(EXPERIMENT.exact_self_test().values()))

    def test_pair_split_checks(self) -> None:
        self.assertTrue(all(EXPERIMENT.validate_pair_splits().values()))

    def test_permutation_boundary(self) -> None:
        pair = "unit-test"
        self.assertEqual(
            EXPERIMENT.permutation_carrier(pair, "reference"),
            EXPERIMENT.PERMUTATION_IDENTITY,
        )
        self.assertNotEqual(
            EXPERIMENT.permutation_carrier(pair, "holonomy"),
            EXPERIMENT.PERMUTATION_IDENTITY,
        )
        self.assertEqual(
            EXPERIMENT.permutation_carrier(
                pair,
                "partner_substitution",
            ),
            EXPERIMENT.PERMUTATION_IDENTITY,
        )

    def test_matrix_boundary(self) -> None:
        pair = "unit-test"
        self.assertEqual(
            EXPERIMENT.matrix_carrier(pair, "reference"),
            EXPERIMENT.MATRIX_IDENTITY,
        )
        self.assertNotEqual(
            EXPERIMENT.matrix_carrier(pair, "holonomy"),
            EXPERIMENT.MATRIX_IDENTITY,
        )
        self.assertEqual(
            EXPERIMENT.matrix_carrier(pair, "partner_substitution"),
            EXPERIMENT.MATRIX_IDENTITY,
        )

    def test_full_adder_is_class1_boundary(self) -> None:
        self.assertEqual(EXPERIMENT.full_adder_carry("reference"), 0)
        self.assertEqual(EXPERIMENT.full_adder_carry("holonomy"), 1)
        self.assertEqual(
            EXPERIMENT.full_adder_carry("partner_substitution"),
            1,
        )
        self.assertEqual(EXPERIMENT.full_adder_carry("remove_A"), 0)
        self.assertEqual(EXPERIMENT.full_adder_carry("remove_B"), 0)


if __name__ == "__main__":
    unittest.main()
