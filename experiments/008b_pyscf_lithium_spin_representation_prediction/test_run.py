import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e008b_run", ROOT / "run.py")
run = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run)


class Experiment008BRegistrationTests(unittest.TestCase):
    def synthetic_payload(self, ratio):
        frequency7 = 1.0e9
        frequency6 = ratio * frequency7
        return {
            "schema": run.MEASUREMENT_SCHEMA,
            "records": [
                {
                    "id": "lithium6_2s_ground_hfs",
                    "source_id": run.EXPECTED_SOURCE_IDS["lithium6_2s_ground_hfs"],
                    "frequency_hz": frequency6,
                    "uncertainty_hz": 1e-3,
                },
                {
                    "id": "lithium7_2s_ground_hfs",
                    "source_id": run.EXPECTED_SOURCE_IDS["lithium7_2s_ground_hfs"],
                    "frequency_hz": frequency7,
                    "uncertainty_hz": 1e-3,
                },
            ],
        }

    def test_registered_predictions_are_frozen(self):
        prediction = run.registered_predictions()
        self.assertAlmostEqual(
            prediction["full_factorised_ratio_li6_over_li7"],
            0.28399324742025683,
        )
        self.assertAlmostEqual(
            prediction["nuclear_g_only_ratio_li6_over_li7"],
            0.3786576632270091,
        )
        self.assertAlmostEqual(
            prediction["representation_only_ratio_li6_over_li7"], 0.75
        )
        self.assertAlmostEqual(
            prediction["clamped_interval_li6_mhz"], 217.07253597376808
        )
        self.assertAlmostEqual(
            prediction["clamped_interval_li7_mhz"], 764.3580893053467
        )

    def test_primary_bands_do_not_overlap(self):
        prediction = run.registered_predictions()
        tau = prediction["acceptance_half_width"]
        full = prediction["full_factorised_ratio_li6_over_li7"]
        controls = (
            prediction["nuclear_g_only_ratio_li6_over_li7"],
            prediction["representation_only_ratio_li6_over_li7"],
        )
        self.assertTrue(
            all(2.0 * tau < abs(math.log(full / value)) for value in controls)
        )

    def test_observation_map_recovers_constructed_ratio(self):
        target = 0.3
        records = run.validate_measurements(self.synthetic_payload(target))
        self.assertAlmostEqual(run.observed_ratio(records)["ratio_li6_over_li7"], target)

    def test_classifier_recovers_each_registered_model(self):
        prediction = run.registered_predictions()
        cases = (
            ("full_factorised_ratio_li6_over_li7", "FULL_FACTORISED_GENERATOR_SUPPORTED"),
            ("nuclear_g_only_ratio_li6_over_li7", "NUCLEAR_G_ONLY_CONTROL_SUPPORTED"),
            ("representation_only_ratio_li6_over_li7", "REPRESENTATION_ONLY_CONTROL_SUPPORTED"),
        )
        for key, expected in cases:
            with self.subTest(key=key):
                decision = run.classify(prediction[key], 0.0)["decision"]
                self.assertEqual(decision, expected)

    def test_classifier_rejects_value_outside_all_bands(self):
        self.assertEqual(
            run.classify(0.55, 0.0)["decision"],
            "NEITHER_REGISTERED_MODEL_SUPPORTED",
        )

    def test_measurement_schema_rejects_extra_record(self):
        payload = self.synthetic_payload(0.3)
        payload["records"].append(dict(payload["records"][0]))
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_measurement_schema_rejects_wrong_source(self):
        payload = self.synthetic_payload(0.3)
        payload["records"][0]["source_id"] = "replacement"
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_measurement_schema_rejects_boolean_number(self):
        payload = self.synthetic_payload(0.3)
        payload["records"][0]["frequency_hz"] = True
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_registration_mode_rejects_measurement_file(self):
        with tempfile.TemporaryDirectory() as directory:
            measurement = Path(directory) / "measurement.json"
            measurement.write_text("{}", encoding="utf-8")
            self.assertEqual(
                run.main(
                    ["--validate-registration", "--measurement-file", str(measurement)]
                ),
                2,
            )

    def test_execution_requires_measurement_file(self):
        self.assertEqual(run.main(["--execute"]), 2)

    def test_execution_writes_new_atomic_output(self):
        prediction = run.registered_predictions()[
            "full_factorised_ratio_li6_over_li7"
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            measurement = root / "measurement.json"
            measurement.write_text(
                json.dumps(self.synthetic_payload(prediction)), encoding="utf-8"
            )
            output = root / "output"
            self.assertEqual(
                run.main(
                    [
                        "--execute",
                        "--measurement-file",
                        str(measurement),
                        "--output-dir",
                        str(output),
                    ]
                ),
                0,
            )
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(
                summary["primary_decision"],
                "FULL_FACTORISED_GENERATOR_SUPPORTED",
            )
            self.assertTrue((output / "report.md").is_file())

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
