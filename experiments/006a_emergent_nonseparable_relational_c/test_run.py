#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e006a_run_tested", HERE / "run.py")
M = importlib.util.module_from_spec(spec); sys.modules[spec.name] = M; spec.loader.exec_module(M)


class Experiment006ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.e006 = M.load_e006()

    def test_dual_capacity_and_disconnection(self):
        masks = M.U.dual_masks(self.e006)
        self.assertEqual(int(sum(x.sum() for x in masks.values()) + 30), 486)
        self.assertTrue(np.all(masks["recurrent"][:12, 12:] == 0))
        self.assertTrue(np.all(masks["recurrent"][12:, :12] == 0))

    def test_inclusion_exclusion_removes_additive_traces(self):
        rng = np.random.default_rng(4); base = rng.normal(size=(8, 24)); a = rng.normal(size=(8, 24)); b = rng.normal(size=(8, 24))
        np.testing.assert_allclose(M.synergy({"00": base, "a0": base+a, "0b": base+b, "ab": base+a+b}), 0, atol=1e-14)

    def test_seed_allocations_are_disjoint(self):
        self.assertFalse(set(M.CONFIRMATORY_SEEDS) & set(M.DEVELOPMENT_SEEDS_EXCLUDED))
        self.assertFalse(set(M.CONFIRMATORY_SEEDS) & set(M.REGISTRATION_CHECK_SEEDS))

    def test_manifest_matches(self): self.assertTrue(M.verify_manifest())


if __name__ == "__main__": unittest.main()
