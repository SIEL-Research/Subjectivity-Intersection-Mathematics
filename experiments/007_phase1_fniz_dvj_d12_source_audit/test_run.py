#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the Experiment 007 Phase 1 audit helpers."""

import importlib.util
import unittest
from pathlib import Path


RUN_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_007_phase1", RUN_PATH)
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class Phase1AuditTests(unittest.TestCase):
    def test_generated_subgroups(self):
        self.assertEqual(RUN.generated_subgroup(0, 0), (0,))
        self.assertEqual(RUN.generated_subgroup(4, 8), (0, 4, 8))
        self.assertEqual(RUN.generated_subgroup(1, 0), tuple(range(12)))

    def test_conditional_candidate_family(self):
        rows, orders = RUN.conditional_candidates()
        self.assertEqual(len(rows), 144)
        self.assertEqual(orders, [1, 2, 3, 4, 6, 12])
        self.assertTrue(all(row["lagrange_divides_12"] for row in rows))
        self.assertFalse(any(row["selected"] for row in rows))

    def test_classification_without_connector(self):
        connector = {"explicit_executable_connector_found": False}
        rows, unused = RUN.conditional_candidates()
        result = RUN.classify(
            connector,
            rows,
            {"restoration_work_explicit": True},
        )
        self.assertEqual(result, "INCOMPLETE_SOURCE_DEFINITION")

    def test_remote_normalization(self):
        self.assertEqual(
            RUN.normalized_remote("https://example.test/repo.git"),
            RUN.normalized_remote("https://example.test/repo/"),
        )


if __name__ == "__main__":
    unittest.main()
