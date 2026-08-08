import importlib.util
import inspect
import json
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name, filename):
    specification = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(specification)
    assert specification.loader is not None
    specification.loader.exec_module(module)
    return module


run = load_module("e008d_run", "run.py")
generate_prediction = load_module("e008d_generate", "generate_prediction.py")


class Experiment008DRegistrationTests(unittest.TestCase):
    def synthetic_payload(self, ratio, relative_rounding=1e-5):
        value41 = 1.0
        value39 = ratio * value41
        return {
            "schema": run.MEASUREMENT_SCHEMA,
            "records": [
                {
                    "id": "potassium39_4p1_2_second_order_delta_A",
                    "source_id": run.SOURCE_ID,
                    "second_order_delta_A_khz": value39,
                    "rounding_half_width_khz": abs(value39) * relative_rounding,
                },
                {
                    "id": "potassium41_4p1_2_second_order_delta_A",
                    "source_id": run.SOURCE_ID,
                    "second_order_delta_A_khz": value41,
                    "rounding_half_width_khz": abs(value41) * relative_rounding,
                },
            ],
        }

    def test_prediction_was_generated_without_target(self):
        prediction = run.load_json(run.PREDICTION)
        self.assertFalse(prediction["target_values_loaded"])
        self.assertEqual(prediction["free_fitted_parameters"], 0)
        source = inspect.getsource(generate_prediction)
        self.assertNotIn(run.SOURCE_ID, source)
        self.assertNotIn("benchmark_sources", source)

    def test_primary_prediction_is_frozen(self):
        predictions = run.registered_predictions()
        self.assertAlmostEqual(predictions["mixed_rank"], 1.4239826742729131)
        self.assertAlmostEqual(predictions["m1_only"], 3.319224048274411)

    def test_all_pyscf_states_converged_and_are_doublets(self):
        prediction = run.load_json(run.PREDICTION)
        self.assertEqual(len(prediction["basis_calculations"]), 4)
        for row in prediction["basis_calculations"]:
            self.assertTrue(row["ground_scf_converged"])
            self.assertTrue(row["excited_scf_converged"])
            self.assertLess(abs(row["spin_square"] - 0.75), 1e-3)

    def test_basis_convergence_gate(self):
        prediction = run.load_json(run.PREDICTION)
        self.assertLess(prediction["uncontracted_tz_qz_log_change"], 0.005)

    def test_registered_model_bands_do_not_overlap(self):
        predictions = run.registered_predictions()
        separation = abs(math.log(predictions["mixed_rank"] / predictions["m1_only"]))
        self.assertGreater(separation, 2.0 * run.ACCEPTANCE_HALF_WIDTH_LOG)
        self.assertGreater(separation, 0.8)

    def test_classifier_recovers_each_registered_model(self):
        predictions = run.registered_predictions()
        mixed = run.classify(predictions["mixed_rank"], 0.0)
        control = run.classify(predictions["m1_only"], 0.0)
        self.assertEqual(
            mixed["decision"], "MIXED_RANK_PROSPECTIVE_PREDICTION_SUPPORTED"
        )
        self.assertEqual(control["decision"], "M1_ONLY_CONTROL_SUPPORTED")
        self.assertTrue(mixed["mixed_rank_strong_match"])

    def test_measurement_schema_rejects_wrong_source(self):
        payload = self.synthetic_payload(run.registered_predictions()["mixed_rank"])
        payload["records"][0]["source_id"] = "replacement"
        with self.assertRaises(run.ProvenanceError):
            run.validate_measurements(payload)

    def test_measurement_schema_rejects_opposite_signs(self):
        payload = self.synthetic_payload(run.registered_predictions()["mixed_rank"])
        payload["records"][0]["second_order_delta_A_khz"] *= -1
        records = run.validate_measurements(payload)
        with self.assertRaises(run.ProvenanceError):
            run.observed_ratio(records)

    def test_registration_mode_refuses_measurement_input(self):
        with tempfile.TemporaryDirectory() as directory:
            measurement = Path(directory) / "measurement.json"
            measurement.write_text("{}", encoding="utf-8")
            self.assertEqual(
                run.main(
                    ["--validate-registration", "--measurement-file", str(measurement)]
                ),
                2,
            )

    def test_execution_writes_new_atomic_output(self):
        prediction = run.registered_predictions()["mixed_rank"]
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
                "MIXED_RANK_PROSPECTIVE_PREDICTION_SUPPORTED",
            )
            self.assertTrue((output / "report.md").is_file())

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
