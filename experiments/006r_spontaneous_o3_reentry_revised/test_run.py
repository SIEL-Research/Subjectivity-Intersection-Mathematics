#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import run


class TestExperiment006R(unittest.TestCase):
    def test_seed_firewall(self):
        confirmatory = set(run.CONFIRMATORY_SEEDS)
        self.assertEqual(confirmatory, set(range(3000, 3048)))
        self.assertTrue(confirmatory.isdisjoint(run.DEVELOPMENT_SEEDS_EXCLUDED))
        self.assertTrue(confirmatory.isdisjoint(run.REGISTRATION_CHECK_SEEDS))
        self.assertTrue(confirmatory.isdisjoint(range(1000, 1024)))
        self.assertTrue(confirmatory.isdisjoint(range(2000, 2024)))

    def test_evaluation_firewall(self):
        self.assertEqual(run.CONFIRMATORY_EVALUATION_SEEDS, (61650001, 61650002))
        self.assertTrue(
            set(run.CONFIRMATORY_EVALUATION_SEEDS).isdisjoint(
                run.REGISTRATION_CHECK_EVALUATION_SEEDS
            )
        )

    def test_primary_thresholds(self):
        self.assertEqual(run.MINIMUM_COMPETENT_SEEDS, 44)
        self.assertEqual(run.MINIMUM_TRANSPORT_SEEDS_PER_ARCHITECTURE, 40)
        self.assertEqual(run.MINIMUM_ACTION_SEEDS_PER_ARCHITECTURE, 36)
        self.assertEqual(run.MINIMUM_POOLED_TRANSPORT_SEEDS, 168)

    def test_secondary_is_separate(self):
        self.assertEqual(run.SECONDARY_PARTITIONED_MINIMUM, 40)
        self.assertEqual(run.SECONDARY_DISTRIBUTED_MAXIMUM, 39)
        self.assertEqual(run.SECONDARY_MINIMUM_GAP, 6)

    def test_frozen_source_exists(self):
        self.assertTrue(run.E006_SOURCE.is_file())


if __name__ == "__main__":
    unittest.main()
