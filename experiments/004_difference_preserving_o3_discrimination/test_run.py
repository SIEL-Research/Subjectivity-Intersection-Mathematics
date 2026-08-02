#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("siel_e004_test_target", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestExperiment004(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()
        cls.e003r = cls.runner.load_e003r()

    def test_allocations_are_disjoint(self):
        development = set(range(
            self.runner.DEVELOPMENT_START,
            self.runner.DEVELOPMENT_START + self.runner.PAIR_COUNT,
        ))
        confirmatory = set(range(
            self.runner.CONFIRMATORY_START,
            self.runner.CONFIRMATORY_START + self.runner.PAIR_COUNT,
        ))
        self.assertFalse(development & confirmatory)
        self.assertFalse(
            set(self.runner.DEVELOPMENT_SEEDS) & set(self.runner.CONFIRMATORY_SEEDS)
        )

    def test_descriptor_allocation_is_unique(self):
        for start in (self.runner.DEVELOPMENT_START, self.runner.CONFIRMATORY_START):
            pairs = {
                (
                    self.runner.rich_descriptor(self.e003r, index, 0),
                    self.runner.rich_descriptor(self.e003r, index, 1),
                )
                for index in range(start, start + self.runner.PAIR_COUNT)
            }
            self.assertEqual(len(pairs), self.runner.PAIR_COUNT)

    def test_donor_stays_in_family_and_has_no_fixed_point(self):
        for index in range(self.runner.PAIR_COUNT):
            donor = self.runner.donor_index(index)
            self.assertNotEqual(index, donor)
            self.assertEqual(
                index // self.runner.FAMILY_SIZE,
                donor // self.runner.FAMILY_SIZE,
            )

    def test_symmetric_joint_is_difference_invariant(self):
        matrices = self.e003r.orthogonal_matrices(12345)
        rng = np.random.default_rng(54321)
        common = rng.normal(size=self.e003r.DIM)
        difference = rng.normal(size=self.e003r.DIM)
        forward = self.runner.joint_state(
            common + difference,
            common - difference,
            matrices,
            "symmetric_recurrent",
        )
        reverse = self.runner.joint_state(
            common - difference,
            common + difference,
            matrices,
            "symmetric_recurrent",
        )
        np.testing.assert_array_equal(forward, reverse)

    def test_candidate_joint_preserves_difference_route(self):
        matrices = self.e003r.orthogonal_matrices(12345)
        rng = np.random.default_rng(54321)
        common = rng.normal(size=self.e003r.DIM)
        difference = rng.normal(size=self.e003r.DIM)
        forward = self.runner.joint_state(
            common + difference,
            common - difference,
            matrices,
            "candidate_o3",
        )
        reverse = self.runner.joint_state(
            common - difference,
            common + difference,
            matrices,
            "candidate_o3",
        )
        self.assertGreater(float(np.linalg.norm(forward - reverse)), 0.0)

    def test_confirmation_requires_full_pair_count_and_check(self):
        self.assertEqual(self.runner.PAIR_COUNT, 128)
        self.assertEqual(len(self.runner.CONFIRMATORY_SEEDS), 12)
        self.assertEqual(self.runner.MIN_SEED_PASSES, 10)
        self.assertEqual(self.runner.MIN_PAIR_PASSES, 112)
        self.assertEqual(self.runner.MIN_FAMILY_PASSES, 52)


if __name__ == "__main__":
    unittest.main()
