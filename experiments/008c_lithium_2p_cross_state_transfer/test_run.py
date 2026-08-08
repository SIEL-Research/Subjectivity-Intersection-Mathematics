import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e008c_run", ROOT / "run.py")
run = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run)


class Experiment008CRegistrationTests(unittest.TestCase):
    def synthetic_payload(self, ratio, relative_uncertainty=1e-9):
        a7 = 1.0e8
        interval7 = abs(a7) * run.INTERVAL_FACTOR_LI7
        interval6 = ratio * interval7
        a6 = interval6 / run.INTERVAL_FACTOR_LI6
        return {
            "schema": run.MEASUREMENT_SCHEMA,
            "records": [
                {
                    "id": "lithium6_2p1_2_hfs_A",
                    "source_id": run.SOURCE_ID,
                    "magnetic_dipole_constant_hz": a6,
                    "uncertainty_hz": abs(a6) * relative_uncertainty,
                },
                {
                    "id": "lithium7_2p1_2_hfs_A",
                    "source_id": run.SOURCE_ID,
                    "magnetic_dipole_constant_hz": a7,
                    "uncertainty_hz": abs(a7) * relative_uncertainty,
                },
            ],
        }

    def test_registered_predictions_are_frozen(self):
        prediction = run.registered_predictions()
        self.assertAlmostEqual(
            prediction["factorised_base_ratio_li6_over_li7"],
            0.28399324742025683,
        )
        self.assertAlmostEqual(
            prediction["bilateral_mass_only_ratio_li6_over_li7"],
            0.28400802967617617,
        )
        self.assertAlmostEqual(
            prediction["recursive_sector_ratio_li6_over_li7"],
            0.2840139905285925,
        )
        self.assertAlmostEqual(
            prediction["maximum_measurement_sigma_log"],
            1.681013068429318e-6,
        )

    def test_registered_model_bands_do_not_overlap(self):
        prediction = run.registered_predictions()
        tau = prediction["acceptance_half_width"]
        models = (
            prediction["factorised_base_ratio_li6_over_li7"],
            prediction["bilateral_mass_only_ratio_li6_over_li7"],
            prediction["recursive_sector_ratio_li6_over_li7"],
        )
        for index, left in enumerate(models):
            for right in models[index + 1 :]:
                self.assertLess(2.0 * tau, abs(math.log(left / right)))

    def test_observation_map_uses_interval_factors(self):
        target = 0.284
        records = run.validate_measurements(self.synthetic_payload(target))
        self.assertAlmostEqual(run.observed_ratio(records)["ratio_li6_over_li7"], target)

    def test_classifier_recovers_each_registered_model(self):
        prediction = run.registered_predictions()
        cases = (
            ("factorised_base_ratio_li6_over_li7", "FACTORISED_BASE_TRANSFER_SUPPORTED"),
            (
                "bilateral_mass_only_ratio_li6_over_li7",
                "BILATERAL_MASS_ONLY_TRANSFER_SUPPORTED",
            ),
            ("recursive_sector_ratio_li6_over_li7", "RECURSIVE_SECTOR_TRANSFER_SUPPORTED"),
        )
        for key, expected in cases:
            with self.subTest(key=key):
                self.assertEqual(run.classify(prediction[key], 0.0)["decision"], expected)

    def test_precision_gate_precedes_model_classification(self):
        prediction = run.registered_predictions()
        decision = run.classify(
            prediction["recursive_sector_ratio_li6_over_li7"],
            prediction["maximum_measurement_sigma_log"] * 1.01,
        )
        self.assertEqual(decision["decision"], "INSUFFICIENT_PRECISION")
        self.assertFalse(decision["precision_gate_pass"])
        self.assertEqual(decision["models"], {})

    def test_measurement_schema_accepts_signed_nonzero_constants(self):
        payload = self.synthetic_payload(0.284)
        payload["records"][0]["magnetic_dipole_constant_hz"] *= -1
        records = run.validate_measurements(payload)
        self.assertLess(records[0]["magnetic_dipole_constant_hz"], 0)

    def test_measurement_schema_rejects_wrong_source(self):
        payload = self.synthetic_payload(0.284)
        payload["records"][0]["source_id"] = "replacement"
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
            "recursive_sector_ratio_li6_over_li7"
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
                "RECURSIVE_SECTOR_TRANSFER_SUPPORTED",
            )
            self.assertTrue((output / "report.md").is_file())

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
