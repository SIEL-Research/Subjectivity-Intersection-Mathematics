#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for Experiment 007 Phase 2 helpers."""

import importlib.util
import unittest
from pathlib import Path


RUN_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("experiment_007_phase2", RUN_PATH)
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class Phase2Tests(unittest.TestCase):
    def test_c12_orders(self):
        self.assertEqual(RUN.c12_order(0), 1)
        self.assertEqual(RUN.c12_order(1), 12)
        self.assertEqual(RUN.c12_order(4), 3)
        self.assertEqual(RUN.c12_order(6), 2)
        self.assertEqual(RUN.generated_order(4, 6), 6)
        self.assertEqual(RUN.generated_order(4, 5), 12)

    def test_development_words_are_balanced(self):
        for word in RUN.DEVELOPMENT_WORDS:
            self.assertEqual(len(word), 12)
            self.assertEqual({op: word.count(op) for op in RUN.OPERATIONS}, {
                "+": 3, "-": 3, "*": 3, "/": 3,
            })

    def test_equivalence_contains_units_and_exchange(self):
        key = RUN.equivalence_key(1, 5)
        self.assertEqual(key, RUN.equivalence_key(5, 1))
        self.assertEqual(key, RUN.equivalence_key(7, 11))

    def test_classifications(self):
        self.assertEqual(RUN.classify([]), "NO_ADMISSIBLE_CANDIDATE")
        self.assertEqual(
            RUN.classify([{"equivalence_key": (1, 5)}]),
            "UNIQUE_CONSTRUCTED_RULE_SELECTED",
        )
        self.assertEqual(
            RUN.classify([
                {"equivalence_key": (1, 5)},
                {"equivalence_key": (1, 5)},
            ]),
            "ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED",
        )
        self.assertEqual(
            RUN.classify([
                {"equivalence_key": (1, 5)},
                {"equivalence_key": (1, 7)},
            ]),
            "MULTIPLE_TOP_EQUIVALENCE_CLASSES",
        )


if __name__ == "__main__":
    unittest.main()
