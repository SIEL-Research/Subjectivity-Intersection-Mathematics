import importlib.util
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e008a_run", ROOT / "run.py")
run = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run)


class Experiment008ARegistrationTests(unittest.TestCase):
    def synthetic_payload(self, ratio):
        nu_h = 10.0
        g_h = run.MU_H / run.SPIN_H
        g_d = run.MU_D / run.SPIN_D
        nu_d = (
            ratio
            * nu_h
            * ((run.SPIN_D + 0.5) / (run.SPIN_H + 0.5))
            * abs(g_d / g_h)
        )
        return {
            "schema": run.MEASUREMENT_SCHEMA,
            "records": [
                {
                    "id": "hydrogen_1s_hfs",
                    "source_id": run.EXPECTED_SOURCE_IDS["hydrogen_1s_hfs"],
                    "frequency_hz": nu_h,
                    "uncertainty_hz": 1e-12,
                },
                {
                    "id": "deuterium_1s_hfs",
                    "source_id": run.EXPECTED_SOURCE_IDS["deuterium_1s_hfs"],
                    "frequency_hz": nu_d,
                    "uncertainty_hz": 1e-12,
                },
            ],
        }

    def test_registered_prediction_is_frozen(self):
        prediction = run.registered_predictions()
        self.assertAlmostEqual(prediction["si_lambda_one_ratio"], 0.9997293072637635)
        self.assertAlmostEqual(prediction["standard_contact_ratio"], 1.0008165196710828)

    def test_bands_do_not_overlap(self):
        prediction = run.registered_predictions()
        self.assertLess(2 * prediction["acceptance_half_width"], prediction["log_separation"])

    def test_observation_map_recovers_constructed_ratio(self):
        target = 1.002
        records = run.validate_measurements(self.synthetic_payload(target))
        self.assertAlmostEqual(run.observed_ratio(records)["ratio"], target)

    def test_classifier_recovers_registered_models(self):
        prediction = run.registered_predictions()
        self.assertEqual(run.classify(prediction["si_lambda_one_ratio"], 0.0)["decision"], "SI_LAMBDA_ONE_SUPPORTED")
        self.assertEqual(run.classify(prediction["standard_contact_ratio"], 0.0)["decision"], "STANDARD_CONTACT_SUPPORTED")

    def test_measurement_schema_rejects_extra_record(self):
        payload = self.synthetic_payload(1.0)
        payload["records"].append(dict(payload["records"][0]))
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_measurement_schema_rejects_wrong_source(self):
        payload = self.synthetic_payload(1.0)
        payload["records"][0]["source_id"] = "replacement"
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_registration_mode_rejects_measurement_file(self):
        with tempfile.TemporaryDirectory() as directory:
            measurement = Path(directory) / "measurement.json"
            measurement.write_text("{}", encoding="utf-8")
            self.assertEqual(run.main(["--validate-registration", "--measurement-file", str(measurement)]), 2)

    def test_execution_requires_measurement_file(self):
        self.assertEqual(run.main(["--execute"]), 2)

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
