#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for Experiment 007A Phase 1 helpers."""

import importlib.util
import unittest
from fractions import Fraction
from pathlib import Path


RUN_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("e007a_phase1", RUN_PATH)
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class OperatorObjectAuditTests(unittest.TestCase):
    def test_normalized_remote(self):
        self.assertEqual(
            RUN.normalized_remote("https://example.test/repo.git"),
            RUN.normalized_remote("https://example.test/repo/"),
        )

    def test_linear_coordinates(self):
        basis = (
            ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(0))),
            ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))),
        )
        target = ((Fraction(2), Fraction(0)), (Fraction(0), Fraction(3)))
        self.assertEqual(RUN.linear_coordinates(basis, target), (2, 3))

    def test_classification_routes_underdefined_sio(self):
        d12 = {"classification": "SEVEN_DIMENSIONAL_UNITAL_OPERATOR_ALGEBRA"}
        sio = {"classification": "SIO_OPERATOR_ALGEBRA_UNDERDEFINED"}
        self.assertEqual(
            RUN.classify(d12, sio),
            "D12_TARGET_DEFINED_SIO_EXTRACTION_UNDERDEFINED",
        )

    def test_seven_basis_exponents_are_not_set_closed(self):
        exponents = set(RUN.EXPECTED_CHARACTER_EXPONENTS)
        self.assertNotIn((1 + 2) % 12, exponents)


if __name__ == "__main__":
    unittest.main()
