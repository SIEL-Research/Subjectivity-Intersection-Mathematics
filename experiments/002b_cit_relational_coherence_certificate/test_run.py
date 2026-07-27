#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for Experiment 002B."""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_002b", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CitCertificateTests(unittest.TestCase):
    def test_cit_is_local_conjunction(self):
        for cw in range(8):
            for ccw in range(8):
                value = MODULE.signals(
                    MODULE.A2.bits(cw), MODULE.A2.bits(ccw), (1, 0)
                )
                result = MODULE.readout(value)
                self.assertEqual(result["cit"], result["l_combined"])

    def test_local_corruption_is_detected(self):
        value = MODULE.signals((1, 0, 0), (1, 0, 0), (1, 0))
        changed = MODULE.copy_signals(value)
        word = list(changed["cw_sum"])
        word[0] ^= 1
        changed["cw_sum"] = tuple(word)
        result = MODULE.readout(changed)
        self.assertEqual(result["l_plus"], 0)
        self.assertEqual(result["cit"], 0)

    def test_whole_ring_epoch_skew_is_locally_valid(self):
        value = MODULE.signals((1, 0, 0), (1, 0, 0), (1, 0))
        prior_sum, prior_carry = MODULE.A2.local_outputs((0, 1, 0), 1, 0)
        value["ccw_sum"] = prior_sum
        value["ccw_carry"] = prior_carry
        result = MODULE.readout(value)
        self.assertEqual(result["l_plus"], 1)
        self.assertEqual(result["l_minus"], 1)
        self.assertEqual(result["cit"], 1)

    def test_registered_case_construction(self):
        rows = (
            MODULE.admissible_cases()
            + MODULE.local_integrity_cases()
            + MODULE.relation_only_cases()
        )
        metrics = MODULE.summarize(rows, MODULE.sequence_rows())
        self.assertEqual(metrics["case_counts"], {
            "admissible": 512,
            "local_integrity": 1984,
            "relation_only": 620,
        })
        for row in rows:
            if row["category"] == "relation_only":
                self.assertEqual(row["l_plus"], 1)
                self.assertEqual(row["l_minus"], 1)


if __name__ == "__main__":
    unittest.main()
