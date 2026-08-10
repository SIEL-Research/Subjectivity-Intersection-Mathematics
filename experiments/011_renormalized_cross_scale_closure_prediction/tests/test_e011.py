import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run


class RegistrationTests(unittest.TestCase):
    def test_target_exponents_are_held_out(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        explored = set(registry["explored_bridge_exponents"])
        heldout = {item.bridge_exponent for item in run.TARGET_FAMILIES}
        self.assertTrue(explored.isdisjoint(heldout))

    def test_predictions_follow_frozen_transform(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        reference = registry["frozen_mediator_reference"]
        for family in run.TARGET_FAMILIES:
            expected = reference ** (1.0 / (2.0 * family.bridge_exponent))
            observed = registry["predictions"][family.name]["lambda_90"]
            self.assertAlmostEqual(expected, observed, places=15)

    def test_seed_ranges_are_disjoint(self):
        ranges = [
            set(range(item.ensemble_seed, item.ensemble_seed + run.SEED_COUNT))
            for item in run.TARGET_FAMILIES
        ]
        for index, left in enumerate(ranges):
            for right in ranges[index + 1 :]:
                self.assertTrue(left.isdisjoint(right))

    def test_registered_decisions_are_present_without_execution(self):
        source = (ROOT / "run.py").read_text()
        self.assertIn("RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_SUPPORTED", source)
        self.assertIn("RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_PARTIALLY_SUPPORTED", source)
        self.assertIn("RENORMALIZED_CROSS_SCALE_CLOSURE_PREDICTION_NOT_SUPPORTED", source)


if __name__ == "__main__":
    unittest.main()
