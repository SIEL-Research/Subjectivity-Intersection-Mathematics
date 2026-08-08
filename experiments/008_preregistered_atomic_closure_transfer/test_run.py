import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e008_run", ROOT / "run.py")
run = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run)


class Experiment008RegistrationTests(unittest.TestCase):
    def test_frozen_holdouts_exclude_hydrogen_deuterium(self):
        self.assertEqual(
            set(run.EXPECTED_SOURCE_IDS),
            {"muonium_1s2s", "positronium_1s2s"},
        )

    def test_frozen_structural_candidate_sets(self):
        self.assertEqual(run.TOTAL_EXPONENTS.count(0.0), 1)
        self.assertEqual(run.DIMENSIONS, tuple(range(1, 13)))
        self.assertEqual(run.RADII, (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0))

    def test_measurement_schema_rejects_extra_record(self):
        payload = {
            "schema": "siel-e008-measurements-v1",
            "records": [
                {
                    "id": "muonium_1s2s",
                    "source_id": run.EXPECTED_SOURCE_IDS["muonium_1s2s"],
                    "frequency_hz": 1.0,
                    "uncertainty_hz": 1.0,
                },
                {
                    "id": "positronium_1s2s",
                    "source_id": run.EXPECTED_SOURCE_IDS["positronium_1s2s"],
                    "frequency_hz": 1.0,
                    "uncertainty_hz": 1.0,
                },
                {
                    "id": "hydrogen_deuterium",
                    "source_id": "excluded",
                    "frequency_hz": 1.0,
                    "uncertainty_hz": 1.0,
                },
            ],
        }
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_measurement_schema_accepts_only_registered_records(self):
        payload = {
            "schema": "siel-e008-measurements-v1",
            "records": [
                {
                    "id": record_id,
                    "source_id": source_id,
                    "frequency_hz": 1.0,
                    "uncertainty_hz": 0.1,
                }
                for record_id, source_id in reversed(sorted(run.EXPECTED_SOURCE_IDS.items()))
            ],
        }
        records = run.validate_measurements(payload)
        self.assertEqual([item["id"] for item in records], sorted(run.EXPECTED_SOURCE_IDS))

    def test_registration_mode_does_not_accept_measurement_file(self):
        with tempfile.TemporaryDirectory() as directory:
            measurement = Path(directory) / "measurements.json"
            measurement.write_text("{}", encoding="utf-8")
            self.assertEqual(
                run.main(["--validate-registration", "--measurement-file", str(measurement)]),
                2,
            )

    def test_scientific_execution_requires_measurement_file(self):
        self.assertEqual(run.main(["--execute"]), 2)

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
