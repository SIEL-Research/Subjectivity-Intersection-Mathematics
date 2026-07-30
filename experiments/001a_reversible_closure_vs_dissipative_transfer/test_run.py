#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for Experiment 001A."""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_001a", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DissipativeTransferTests(unittest.TestCase):
    def test_full_adder_truth_table(self):
        expected = {
            (0, 0, 0): (0, 0),
            (0, 0, 1): (1, 0),
            (0, 1, 0): (1, 0),
            (0, 1, 1): (0, 1),
            (1, 0, 0): (1, 0),
            (1, 0, 1): (0, 1),
            (1, 1, 0): (0, 1),
            (1, 1, 1): (1, 1),
        }
        for (a, b, carry), output in expected.items():
            self.assertEqual(MODULE.full_adder(carry, (a, b)), output)

    def test_carry_generators_are_kill_propagate_generate(self):
        maps = {
            event: tuple(
                MODULE.step("F0", state, event)[0]
                for state in MODULE.F0_STATES
            )
            for event in MODULE.INPUTS
        }
        self.assertEqual(maps[(0, 0)], (0, 0))
        self.assertEqual(maps[(0, 1)], (0, 1))
        self.assertEqual(maps[(1, 0)], (0, 1))
        self.assertEqual(maps[(1, 1)], (1, 1))

    def test_registered_transition_monoid_orders(self):
        self.assertEqual(MODULE.transition_monoid("F0")[2]["monoid_order"], 3)
        self.assertEqual(MODULE.transition_monoid("F1")[2]["monoid_order"], 8)

    def test_behavioral_partitions_include_declared_observation(self):
        f0 = MODULE.behavioral_partition("F0")
        f1 = MODULE.behavioral_partition("F1")
        self.assertEqual(len(set(f0.values())), 2)
        self.assertEqual(len(set(f1.values())), 4)

    def test_latest_overwrite_is_exact(self):
        for initial in MODULE.F0_STATES:
            for word in MODULE.history_words(5):
                final, _ = MODULE.simulate("F0", initial, word)
                predicted, _ = MODULE.latest_overwrite_prediction(initial, word)
                self.assertEqual(final, predicted)

    def test_role_exchange_is_exact_symmetry(self):
        for model in ("F0", "F1"):
            for initial in MODULE.states(model):
                for word in MODULE.history_words(4):
                    self.assertEqual(
                        MODULE.simulate(model, initial, word),
                        MODULE.simulate(model, initial, MODULE.swap_word(word)),
                    )

    def test_registered_coordinate_maps_commute(self):
        rows = MODULE.gauge_rows()
        self.assertEqual(len(rows), 48)
        self.assertTrue(all(row["state_covariant"] for row in rows))
        self.assertTrue(all(row["output_covariant"] for row in rows))

    def test_scalar_return_is_not_relational_recovery(self):
        partitions = {
            model: MODULE.behavioral_partition(model)
            for model in ("F0", "F1")
        }
        rows = MODULE.recovery_rows(partitions)
        self.assertGreater(sum(row["scalar_return"] for row in rows), 0)
        self.assertEqual(sum(row["relational_recovery"] for row in rows), 0)
        self.assertTrue(all(
            row["nontrivial_bilateral_precondition"] == 0 for row in rows
        ))

    def test_registered_history_count(self):
        words = sum(4 ** length for length in range(9))
        self.assertEqual(words, 87381)
        self.assertEqual(words * 2 + words * 4, 524286)


if __name__ == "__main__":
    unittest.main()
