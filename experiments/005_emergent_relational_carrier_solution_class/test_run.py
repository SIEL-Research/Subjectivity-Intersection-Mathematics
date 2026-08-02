#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import numpy as np

import run


class TestExperiment005(unittest.TestCase):
    def test_seed_firewall(self):
        confirmatory = set(run.CONFIRMATORY_SEEDS)
        self.assertEqual(confirmatory, set(range(1000, 1024)))
        self.assertTrue(confirmatory.isdisjoint(range(0, 8)))
        self.assertTrue(confirmatory.isdisjoint(range(100, 112)))
        self.assertTrue(confirmatory.isdisjoint(range(200, 224)))
        self.assertTrue(confirmatory.isdisjoint(run.REGISTRATION_CHECK_SEEDS))

    def test_capacity_is_exactly_matched(self):
        self.assertEqual(
            {
                architecture: run.P014.active_parameter_count(architecture)
                for architecture in run.ARCHITECTURES
            },
            {architecture: 486 for architecture in run.ARCHITECTURES},
        )

    def test_receiver_norm_matched_control(self):
        rng = np.random.default_rng(5005)
        component = rng.normal(size=(17, run.E009.STATE_DIM))
        randomized = run.matched_random_component(
            component,
            run.NEW_ARCHITECTURE,
            np.random.default_rng(5006),
        )
        for indices in run.P014.receiver_indices(run.NEW_ARCHITECTURE):
            np.testing.assert_allclose(
                np.linalg.norm(component[:, indices], axis=1),
                np.linalg.norm(randomized[:, indices], axis=1),
                atol=1e-12,
            )

    def test_rank_null_and_primary_floor(self):
        self.assertAlmostEqual(run.RANK_NULL_PROBABILITY, 4.0 / 65.0)
        self.assertEqual(run.MINIMUM_TOP_095_PER_PASSING_ARCHITECTURE, 14)
        self.assertEqual(run.MINIMUM_PASSING_ARCHITECTURES, 3)
        self.assertEqual(run.MINIMUM_POOLED_TOP_095, 60)
        self.assertLess(
            run.binomial_upper_tail(24, 14, run.RANK_NULL_PROBABILITY),
            run.PER_ARCHITECTURE_ALPHA,
        )

    def test_reciprocal_targets_are_receiver_specific(self):
        profiles = run.E009.pair_profiles()
        _, targets, _ = run.P015.sample_batch(
            5007, run.E009.TRAIN_PAIRS, 64, profiles, noise=False
        )
        self.assertEqual(targets.shape, (64, 2))
        self.assertTrue(np.all((0 <= targets) & (targets < 3)))


if __name__ == "__main__":
    unittest.main()
