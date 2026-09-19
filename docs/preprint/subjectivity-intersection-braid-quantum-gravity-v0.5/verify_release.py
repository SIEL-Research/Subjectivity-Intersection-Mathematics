#!/usr/bin/env python3
"""Verify v0.5 public artifacts and required claim boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "ARTIFACT_MANIFEST_v0.5.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("version") != "0.5":
        raise SystemExit("manifest version is not 0.5")
    for name, record in manifest["files"].items():
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"missing artifact: {name}")
        actual = sha256(path)
        expected = record["sha256"]
        if actual != expected:
            raise SystemExit(f"hash mismatch: {name}: {actual} != {expected}")

    tex = (ROOT / "SUBJECTIVITY_INTERSECTION_BRAID_QUANTUM_GRAVITY_v0.5.tex").read_text(
        encoding="utf-8"
    )
    required = (
        "Subjectivity-Intersection Braid Quantum Gravity",
        "A target-free $1+3$ carrier and its affine completion",
        "Two-principle conditional continuum Einstein theorem",
        "Neither CGR nor MMR is presently derived in full from the pointed-braid source",
        "not as a completed theory of quantum gravity",
        "not consciousness",
    )
    missing = [marker for marker in required if marker not in tex]
    if missing:
        raise SystemExit(f"missing required claim markers: {missing}")

    matrix = (ROOT / "CLAIM_DEPENDENCY_MATRIX_v0.5.md").read_text(encoding="utf-8")
    matrix_markers = ("Source-derived exact mathematical result", "CGR", "MMR", "Open; not claimed")
    missing_matrix = [marker for marker in matrix_markers if marker not in matrix]
    if missing_matrix:
        raise SystemExit(f"missing dependency markers: {missing_matrix}")

    print("PASS: v0.5 public artifacts, version, and claim boundaries verified")


if __name__ == "__main__":
    main()
