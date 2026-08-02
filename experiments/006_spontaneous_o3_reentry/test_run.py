#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import numpy as np

import run


class TestSpontaneousO3Pilot(unittest.TestCase):
    def test_seed_firewall(self):
        confirmatory = set(run.CONFIRMATORY_SEEDS)
        self.assertEqual(confirmatory, set(range(2000, 2024)))
        self.assertTrue(confirmatory.isdisjoint(run.DEVELOPMENT_SEEDS_EXCLUDED))
        self.assertTrue(confirmatory.isdisjoint(range(1000, 1024)))
        self.assertTrue(confirmatory.isdisjoint(run.REGISTRATION_CHECK_SEEDS))

    def test_transitions_are_signal_free(self):
        self.assertTrue(all(step >= run.E009.INTERVENTION_STEP for step in run.TRANSITIONS))
        self.assertTrue(all(step + 1 < run.E009.SEQUENCE_LENGTH for step in run.TRANSITIONS))

    def test_receiver_matching(self):
        architecture = run.P014.NEW_ARCHITECTURE
        rng = np.random.default_rng(19001)
        component = rng.normal(size=(19, run.E009.STATE_DIM))
        randomized = run.receiver_matched_direction(
            component, architecture, np.random.default_rng(19002)
        )
        for indices in run.P014.receiver_indices(architecture):
            np.testing.assert_allclose(
                np.linalg.norm(component[:, indices], axis=1),
                np.linalg.norm(randomized[:, indices], axis=1),
                atol=1e-12,
            )

    def test_one_step_matches_forward(self):
        model = run.P014.initialize("distributed", 19003)
        x = np.random.default_rng(19004).normal(
            size=(11, run.E009.SEQUENCE_LENGTH, run.E009.INPUT_DIM)
        )
        _, states = run.E009.forward(model, x)
        advanced = run.advance(model, states[4], x[:, 4])
        np.testing.assert_allclose(advanced, states[5], atol=1e-12)

    def test_capacity_and_registered_thresholds(self):
        self.assertEqual(
            {
                architecture: run.P014.active_parameter_count(architecture)
                for architecture in run.ARCHITECTURES
            },
            {architecture: 486 for architecture in run.ARCHITECTURES},
        )
        self.assertEqual(run.MINIMUM_SEED_PASSES_PER_ARCHITECTURE, 18)
        self.assertEqual(run.MINIMUM_POOLED_TRANSPORT_SEED_PASSES, 75)


if __name__ == "__main__":
    unittest.main()
