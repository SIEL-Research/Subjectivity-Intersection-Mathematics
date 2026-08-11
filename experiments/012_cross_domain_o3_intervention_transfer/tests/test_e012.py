import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e012_run_test", ROOT / "run.py")
RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUN
SPEC.loader.exec_module(RUN)


class E012TargetFreeTests(unittest.TestCase):
    def test_target_registry_declares_no_execution(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        self.assertFalse(registry["target_execution_performed"])

    def test_confirmatory_cell_seeds_exclude_prior_ranges(self):
        registry = json.loads((ROOT / "target_registry.json").read_text())
        starts = registry["cellular"]["cohort_starts"]
        self.assertTrue(all(start >= 2026140000 for start in starts))

    def test_gate_logic_can_fail(self):
        thresholds = {
            "high_minimum": 0.8,
            "low_maximum": 0.5,
            "specific_return_advantage_minimum": 0.25,
        }
        failed = RUN.gates(
            {"intact": 0.9, "removed": 0.7, "mismatched_return": 0.6, "correct_return": 0.75},
            thresholds,
        )
        self.assertFalse(all(failed.values()))

    def test_receipt_rejects_wrong_tag_without_execution(self):
        receipt = {
            "schema": "siel-e012-registration-receipt-v1",
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


if __name__ == "__main__":
    unittest.main()
