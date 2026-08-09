import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import run


SOURCE_ROOT = Path("/private/tmp/minimal-cell-life-audit")


class Experiment009Tests(unittest.TestCase):
    def test_no_o3_state_is_installed(self):
        self.assertNotIn("o3", {name.lower() for name in core.STATE_NAMES})

    def test_joint_erasure_preserves_reference_point(self):
        self.assertEqual(core.joint_gate(1.0, 1.0, False), 1.0)
        self.assertEqual(core.joint_gate(1.0, 1.0, True), 1.0)

    def test_joint_erasure_removes_bilinear_interaction(self):
        x, y = 0.8, 0.7
        full = core.joint_gate(x, y, False)
        erased = core.joint_gate(x, y, True)
        interaction = (x - 1.0) * (y - 1.0)
        self.assertAlmostEqual(full - erased, interaction)

    @unittest.skipUnless(SOURCE_ROOT.exists(), "pinned Minimal_Cell checkout unavailable")
    def test_source_anchors_are_locked(self):
        anchors = core.verify_and_read_anchors(SOURCE_ROOT)
        self.assertEqual(anchors["external_glucose_mm"], 40.0)
        self.assertEqual(anchors["cell_radius_m"], 2e-7)
        self.assertGreater(anchors["membrane_gene_count"], 1)

    def test_source_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in core.SOURCE_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("modified")
            with self.assertRaises(ValueError):
                core.verify_and_read_anchors(root)

    def test_simulation_is_deterministic(self):
        config = replace(core.DynamicsConfig(), duration_minutes=110.0)
        first = core.simulate(42, config)
        second = core.simulate(42, config)
        np.testing.assert_array_equal(first["states"], second["states"])

    def test_module_observable_has_three_distributed_components(self):
        state = np.array([[1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 1.0]])
        modules = core.module_observables(state)
        self.assertEqual(modules.shape, (1, 3))
        self.assertTrue(np.all(modules > 0.0))

    def test_confirmation_seed_ranges_are_frozen_and_disjoint(self):
        self.assertEqual(run.TRAIN_SEEDS, tuple(range(2026090900, 2026090916)))
        self.assertEqual(run.TEST_SEEDS, tuple(range(2026091900, 2026091932)))
        self.assertTrue(set(run.TRAIN_SEEDS).isdisjoint(run.TEST_SEEDS))

    def test_registered_decisions_preserve_negative_outcome(self):
        source = Path(run.__file__).read_text()
        self.assertIn("REDUCED_MODEL_DYNAMIC_O3_SELF_REENTRY_CLOSURE_SUPPORTED", source)
        self.assertIn("REDUCED_MODEL_DYNAMIC_O3_SELF_REENTRY_CLOSURE_NOT_SUPPORTED", source)


if __name__ == "__main__":
    unittest.main()
