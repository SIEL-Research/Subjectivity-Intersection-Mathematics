#!/usr/bin/env python3
"""Verify v0.4 public artifacts and required claim boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "ARTIFACT_MANIFEST_v0.4.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name, record in manifest["files"].items():
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"missing artifact: {name}")
        actual = sha256(path)
        expected = record["sha256"]
        if actual != expected:
            raise SystemExit(f"hash mismatch: {name}: {actual} != {expected}")
    tex = (ROOT / "BRAID_FIRST_QUANTUM_SPACETIME_GRAVITY_v0.4.tex").read_text(
        encoding="utf-8"
    )
    required = (
        "Subjectivity-Intersection Braid Quantum Gravity",
        "Conditional continuum Einstein theorem",
        "None of NL1--NL4 is presently derived in full from the pointed-braid source",
        "not as a completed theory of quantum gravity",
        "not consciousness",
    )
    missing = [marker for marker in required if marker not in tex]
    if missing:
        raise SystemExit(f"missing required claim markers: {missing}")

    print("PASS: v0.4 public artifacts, version, and claim boundaries verified")


if __name__ == "__main__":
    main()
