import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run


class E010TargetFreeTests(unittest.TestCase):
    def test_registered_hashes_validate_without_target_execution(self):
        manifest, target = run.verify_registration()
        self.assertFalse(manifest["target_execution_performed"])
        self.assertFalse(target["target_execution_performed"])

    def test_rectangle_geometry_is_pure_and_ordered(self):
        geometry = run.rectangle_geometry(2.0, 1.0)
        self.assertEqual(geometry.count("H "), 4)
        self.assertIn("H -1.0 -0.5 0", geometry)
        self.assertIn("H 1.0 0.5 0", geometry)

    def test_target_registry_declares_no_execution(self):
        target = json.loads((ROOT / "target_registry.json").read_text())
        self.assertFalse(target["target_execution_performed"])
        self.assertEqual(target["target"]["name"], "H4_plus_rectangle")
        self.assertEqual(target["basis_profiles"], ["sto-3g", "6-31g", "cc-pvdz"])

    def test_receipt_rejects_unverified_doi(self):
        receipt = {
            "schema": "siel-e010-registration-receipt-v1",
            "tag": "e010-preregistration-v1.0.0",
            "commit": "0" * 40,
            "release_url": "https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics/releases/tag/e010-preregistration-v1.0.0",
            "doi": "pending",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(receipt))
            with self.assertRaises(run.ProvenanceError):
                run.validate_receipt(path)

    def test_execute_requires_receipt_at_cli_contract_level(self):
        self.assertIn("--registration-receipt", Path(run.__file__).read_text())


if __name__ == "__main__":
    unittest.main()
