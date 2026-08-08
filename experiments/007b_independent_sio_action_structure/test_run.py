#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for Experiment 007B helpers."""

import importlib.util
import unittest
from pathlib import Path


RUN_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("e007b", RUN_PATH)
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class IndependentSIOActionStructureTests(unittest.TestCase):
    def test_canonical_key_ignores_site_label(self):
        base = {
            "canonical_rule": "erase_relation",
            "input_types": ["JOINT_STATE", "RELATION_COMPONENT"],
            "output_type": "JOINT_STATE",
            "linearity": "linear",
            "direction": "current_pair",
        }
        left = {**base, "site_id": "left"}
        right = {**base, "site_id": "right"}
        self.assertEqual(RUN.canonical_key(left), RUN.canonical_key(right))

    def test_typed_nonlinear_classification(self):
        primitives = [
            {
                "primitive_id": "P01",
                "canonical_rule": "extract_relation",
                "input_types": ["STATE_BUNDLE"],
                "output_type": "RELATION_COMPONENT",
                "linearity": "linear",
            },
            {
                "primitive_id": "P02",
                "canonical_rule": "advance_recurrently",
                "input_types": ["MODEL", "JOINT_STATE", "INPUT_STEP"],
                "output_type": "JOINT_STATE",
                "linearity": "nonlinear",
            },
        ]
        self.assertEqual(
            RUN.structural_class(primitives),
            "STABLE_NONLINEAR_OR_TYPED_ACTION_STRUCTURE",
        )

    def test_common_endomorphism_gate(self):
        primitives = [
            {
                "linearity": "linear",
                "input_types": ["RELATION_COMPONENT"],
                "output_type": "RELATION_COMPONENT",
            },
            {
                "linearity": "linear",
                "input_types": ["RELATION_COMPONENT"],
                "output_type": "RELATION_COMPONENT",
            },
        ]
        self.assertEqual(
            RUN.common_linear_endomorphism_carrier(primitives),
            "RELATION_COMPONENT",
        )

    def test_djs_is_not_assumed(self):
        result = RUN.djs_audit([])
        self.assertFalse(result["all_axioms_forced"])
        self.assertEqual(
            result["classification"], "REGISTERED_COMPARATOR_NOT_NULL_FLOOR"
        )


if __name__ == "__main__":
    unittest.main()
