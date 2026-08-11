import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e013_run_test", ROOT / "run.py")
RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN
SPEC.loader.exec_module(RUN)


class E013TargetFreeTests(unittest.TestCase):
    def test_registry_declares_no_target_execution(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        self.assertFalse(registry["target_execution_performed"])

    def test_targets_are_disjoint_from_e012_and_e013_exploration(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        self.assertEqual(set(registry["atomic"]["targets"]), {"tritium", "helium3_hydrogenic"})
        self.assertEqual(registry["molecular"]["b_angstrom"], 1.0)
        self.assertTrue(all(start >= 2026162000 for start in registry["cellular"]["cohort_starts"]))

    def test_mismatch_selector_uses_structure_only(self):
        candidate = np.array([0.0, 1.0, 3.0, 2.0, -1.0, -2.0])
        shift, shifted, overlap = RUN.first_admissible_roll(candidate, 0, 0.25)
        self.assertGreaterEqual(shift, 1)
        self.assertLessEqual(overlap, 0.25)
        self.assertAlmostEqual(float(np.linalg.norm(candidate)), float(np.linalg.norm(shifted)))

    def test_gate_logic_can_fail(self):
        thresholds = {"high_minimum": 0.8, "low_maximum": 0.5, "specific_return_advantage_minimum": 0.25}
        result = RUN.gates({"intact": 0.9, "removed": 0.7, "mismatched_return": 0.6, "correct_return": 0.75}, thresholds)
        self.assertFalse(all(result.values()))

    def test_causal_lodo_recomputes_heldout_edges(self):
        good = {"intact": 1.0, "removed": 0.1, "mismatched_return": 0.2, "correct_return": 0.9}
        bad = {"intact": 1.0, "removed": 0.1, "mismatched_return": 0.8, "correct_return": 0.7}
        scores = {"atomic": {"a": good}, "molecular": {"m": good}, "cellular": {"c": bad}}
        result = RUN.causal_lodo(scores)
        self.assertTrue(result["cellular"]["training_pass"])
        self.assertFalse(result["cellular"]["pass"])

    def test_receipt_rejects_wrong_tag_without_execution(self):
        receipt = {"schema": "siel-e013-registration-receipt-v1", "tag": "wrong", "commit": "0" * 40, "release_url": "https://github.com/x/y/releases/tag/wrong", "doi": "10.5281/zenodo.1"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt))
            with self.assertRaises(RUN.ProvenanceError):
                RUN.validate_receipt(path)


if __name__ == "__main__":
    unittest.main()
