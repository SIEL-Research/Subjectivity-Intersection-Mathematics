import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e014_run_test", ROOT / "run.py")
RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN
SPEC.loader.exec_module(RUN)


class E014TargetFreeTests(unittest.TestCase):
    def test_registry_declares_no_target_execution(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        self.assertFalse(registry["target_execution_performed"])

    def test_reserved_targets_are_exact(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        self.assertEqual(registry["atomic"]["target"], "helium4_hydrogenic")
        self.assertEqual(registry["molecular"]["b_angstrom"], 1.1)
        self.assertEqual(registry["cellular"]["damage_amplitudes"], [0.675, 0.825])
        self.assertTrue(all(seed >= 2026191001 for seed in registry["cellular"]["cohort_starts"]))

    def test_nonperiodic_shift_does_not_wrap(self):
        values = np.asarray([1.0, 2.0, 3.0, 4.0])
        np.testing.assert_allclose(RUN.nonperiodic_shift(values, 1), [1.0, 1.0, 2.0, 3.0])
        np.testing.assert_allclose(RUN.nonperiodic_shift(values, -1), [2.0, 3.0, 4.0, 4.0])

    def test_directional_logic_can_fail(self):
        passes = {"atomic": True, "molecular": True, "cellular": False}
        result = RUN.leave_one_domain_out(passes)
        self.assertFalse(result["cellular"]["pass"])

    def test_receipt_rejects_wrong_tag_without_execution(self):
        receipt = {
            "schema": "siel-e014-registration-receipt-v1",
            "tag": "wrong",
            "commit": "0" * 40,
            "release_url": "https://github.com/x/y/releases/tag/wrong",
            "doi": "10.5281/zenodo.1",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt))
            with self.assertRaises(RUN.ProvenanceError):
                RUN.validate_receipt(path)

    def test_hellinger_identity_and_difference(self):
        left = np.asarray([0.25, 0.75])
        self.assertAlmostEqual(RUN.hellinger_similarity(left, left), 1.0)
        self.assertLess(RUN.hellinger_similarity(left, left[::-1]), 1.0)


if __name__ == "__main__":
    unittest.main()
