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


generate_prediction = load_module("e008e_generate", "generate_prediction.py")
run = load_module("e008e_run", "run.py")


class Experiment008ERegistrationTests(unittest.TestCase):
    def synthetic_benchmark(self, value, half_width=1e-6, overlap=False):
        return {
            "schema": run.BENCHMARK_SCHEMA,
            "source": {
                "id": "doi:independent.test",
                "title": "Independent K-40 benchmark",
                "publication_date": "2030-01-01",
                "benchmark_class": "A",
                "construction_overlap": overlap,
            },
            "record": {
                "target_id": run.TARGET_ID,
                "value_khz": value,
                "half_width_khz": half_width,
                "derivation": "direct independent extraction",
            },
        }

    def test_prediction_generation_loads_no_benchmark(self):
        prediction = run.load_json(run.PREDICTION)
        self.assertFalse(prediction["target_values_loaded"])
        self.assertFalse(prediction["known_K40_second_order_values_loaded"])
        self.assertEqual(prediction["free_fitted_parameters"], 0)
        source = inspect.getsource(generate_prediction)
        self.assertNotIn("benchmark_search_protocol", source)
        self.assertNotIn("benchmark_measurements", source)

    def test_general_spin_coefficients_reproduce_published_cases(self):
        expected = {
            1.0: (1.0 / 36.0, 1.0 / (12.0 * math.sqrt(3.0))),
            1.5: (1.0 / 90.0, 1.0 / (15.0 * math.sqrt(5.0))),
            2.5: (1.0 / 315.0, 8.0 / (105.0 * math.sqrt(30.0))),
            3.5: (1.0 / 756.0, 1.0 / 126.0),
        }
        for spin, (eta, zeta) in expected.items():
            coefficients = generate_prediction.correction_coefficients(spin)
            self.assertAlmostEqual(coefficients["A_P1_2_from_eta"], eta, places=15)
            self.assertAlmostEqual(coefficients["A_P1_2_from_zeta"], zeta, places=15)

    def test_k40_nuclear_input_and_discrepancy_are_frozen(self):
        construction = run.load_json(ROOT / "construction_sources.json")
        k40 = construction["nuclear_inputs"]["K-40"]
        self.assertEqual(k40["nuclear_spin_I"], 4.0)
        self.assertEqual(k40["magnetic_moment_mu_N"]["value"], -1.29797)
        self.assertEqual(k40["quadrupole_moment_barn"]["value"], -0.075)
        discrepancy = construction["source_discrepancy"]
        self.assertTrue(discrepancy["recorded"])
        self.assertEqual(
            discrepancy["secondary_printed_values_barn"]["K-40"], -0.75
        )

    def test_primary_and_secondary_predictions_are_frozen(self):
        prediction = run.load_json(run.PREDICTION)
        k40 = prediction["isotope_predictions"]["K-40"]
        constants = k40["second_order_constants"]
        corrections = k40["predicted_corrections"]
        self.assertAlmostEqual(constants["eta_khz"], 1.7425278814292096, places=14)
        self.assertAlmostEqual(constants["zeta_khz"], 1.0317877006873037, places=14)
        self.assertAlmostEqual(
            corrections["delta_A_P1_2_khz"], 0.008107082333170607, places=16
        )
        self.assertAlmostEqual(
            corrections["delta_A_P3_2_khz"], 0.00015736281192138904, places=16
        )
        self.assertAlmostEqual(
            corrections["delta_B_P3_2_khz"], 0.05226060942263781, places=15
        )

    def test_prediction_regenerates_byte_for_byte(self):
        regenerated = (
            json.dumps(generate_prediction.generate(), indent=2, sort_keys=True) + "\n"
        )
        self.assertEqual(regenerated, run.PREDICTION.read_text(encoding="utf-8"))

    def test_uncertainty_envelopes_contain_central_values(self):
        prediction = run.load_json(run.PREDICTION)
        central = prediction["isotope_predictions"]["K-40"][
            "predicted_corrections"
        ]
        envelope = prediction["input_uncertainty_envelopes"]["K-40"]
        for key, value in central.items():
            self.assertLess(envelope[key]["min"], value)
            self.assertGreater(envelope[key]["max"], value)

    def test_ratio_envelopes_preserve_common_electronic_correlation(self):
        prediction = run.load_json(run.PREDICTION)
        ratio = prediction["generated_ratios"]["K-40_over_K-39"][
            "delta_A_P1_2_khz"
        ]
        envelope = prediction["generated_ratio_envelopes"]["K-40_over_K-39"][
            "delta_A_P1_2_khz"
        ]
        self.assertAlmostEqual(ratio, 1.13365063363239, places=14)
        self.assertLess(envelope["min"], ratio)
        self.assertGreater(envelope["max"], ratio)

    def test_classifier_recovers_support_and_non_support(self):
        prediction = run.primary_prediction()
        supported = run.classify(prediction["central_khz"], 1e-6)
        rejected = run.classify(prediction["central_khz"] * 2.0, 1e-6)
        self.assertEqual(
            supported["decision"], "K40_PRIMARY_PREDICTION_SUPPORTED"
        )
        self.assertTrue(supported["strong_match"])
        self.assertEqual(
            rejected["decision"], "K40_PRIMARY_PREDICTION_NOT_SUPPORTED"
        )

    def test_benchmark_schema_rejects_construction_overlap(self):
        prediction = run.primary_prediction()["central_khz"]
        payload = self.synthetic_benchmark(prediction, overlap=True)
        with self.assertRaises(run.ProvenanceError):
            run.validate_benchmark(payload)

    def test_registration_mode_refuses_benchmark_input(self):
        with tempfile.TemporaryDirectory() as directory:
            benchmark = Path(directory) / "benchmark.json"
            benchmark.write_text("{}", encoding="utf-8")
            self.assertEqual(
                run.main(
                    ["--validate-registration", "--benchmark-file", str(benchmark)]
                ),
                2,
            )

    def test_future_execution_writes_new_atomic_output(self):
        prediction = run.primary_prediction()["central_khz"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            benchmark = root / "benchmark.json"
            benchmark.write_text(
                json.dumps(self.synthetic_benchmark(prediction)), encoding="utf-8"
            )
            output = root / "output"
            self.assertEqual(
                run.main(
                    [
                        "--execute",
                        "--benchmark-file",
                        str(benchmark),
                        "--output-dir",
                        str(output),
                    ]
                ),
                0,
            )
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(
                summary["primary_decision"], "K40_PRIMARY_PREDICTION_SUPPORTED"
            )
            self.assertTrue((output / "report.md").is_file())

    def test_registration_manifest_and_hashes(self):
        manifest = run.verify_registration()
        self.assertEqual(manifest["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertFalse((ROOT / "results").exists())


if __name__ == "__main__":
    unittest.main()
