#!/usr/bin/env python3
"""Post-registration integrity tests for the completed E008E search."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class E008EResultIntegrityTests(unittest.TestCase):
    def test_registered_sources_remain_unchanged(self):
        registration = load_json(ROOT / "registration_manifest.json")
        for relative, expected in registration["source_sha256"].items():
            self.assertEqual(sha256_file(REPO_ROOT / relative), expected, relative)

    def test_prediction_identity_is_preserved(self):
        summary = load_json(ROOT / "results" / "summary.json")
        self.assertEqual(
            sha256_file(ROOT / "prediction_before_benchmark.json"),
            summary["registration"]["prediction_sha256"],
        )
        self.assertEqual(
            summary["registered_prediction"]["central_khz"],
            0.008107082333170607,
        )

    def test_no_benchmark_decision_follows_audit(self):
        audit = load_json(ROOT / "results" / "search_audit.json")
        summary = load_json(ROOT / "results" / "summary.json")
        decision = "OPEN_NOVEL_PREDICTION_NO_INDEPENDENT_BENCHMARK"
        self.assertEqual(audit["eligible_benchmarks"], [])
        self.assertFalse(audit["numerical_target_extracted"])
        self.assertFalse(audit["registered_evaluator_executed"])
        self.assertEqual(audit["decision"], decision)
        self.assertEqual(summary["primary_decision"], decision)
        self.assertIsNone(summary["benchmark"])
        self.assertFalse(summary["registered_evaluator_executed"])

    def test_result_manifest_hashes(self):
        manifest = load_json(ROOT / "results" / "result_manifest.json")
        for relative, expected in manifest["result_sha256"].items():
            self.assertEqual(sha256_file(REPO_ROOT / relative), expected, relative)


if __name__ == "__main__":
    unittest.main()
