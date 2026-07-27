#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for the independent Experiment 002A audit."""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_002a", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DualRingAuditTests(unittest.TestCase):
    def test_registration_manifest(self):
        manifest = MODULE.verify_registration()
        self.assertEqual(manifest["experiment"], "Experiment 002A")

    def test_full_adder(self):
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
        for inputs, outputs in expected.items():
            self.assertEqual(MODULE.full_adder(*inputs), outputs)

    def test_single_high_is_locally_complementary(self):
        for state in (0, 1):
            for inverter, reset in MODULE.OPERATIONAL_CONTROLS:
                sum_bit, carry_bit = MODULE.full_adder(
                    1 - state, inverter, reset
                )
                self.assertEqual(sum_bit ^ carry_bit, 1)

    def test_oriented_one_hot_cycles(self):
        state = (1, 0, 0)
        cw = [state]
        ccw = [state]
        for _ in range(3):
            cw.append(MODULE.ring_next(cw[-1], 1, 0, "cw"))
            ccw.append(MODULE.ring_next(ccw[-1], 1, 0, "ccw"))
        self.assertEqual(cw, [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)])
        self.assertEqual(ccw, [(1, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0)])

    def test_double_high_is_common_reset(self):
        for value in range(8):
            for direction in ("cw", "ccw"):
                self.assertEqual(
                    MODULE.ring_next(MODULE.bits(value), 1, 1, direction),
                    MODULE.ZERO,
                )

    def test_registered_classification(self):
        metrics, rows = MODULE.exhaustive_audit()
        self.assertEqual(len(rows), 128)
        self.assertEqual(metrics["operational_invariant_passes"], 128)
        self.assertEqual(metrics["partner_substitution_changes"], 0)
        self.assertEqual(metrics["state_intervention_changes"], 0)
        self.assertEqual(MODULE.classify(metrics)["class_id"], 0)


if __name__ == "__main__":
    unittest.main()
