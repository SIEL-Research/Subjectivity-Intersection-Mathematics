#!/usr/bin/env python3
"""Verify primary v0.3 artifact identities and required claim markers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "ARTIFACT_MANIFEST_v0.3.json"


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

    tex = (ROOT / "BRAID_FIRST_QUANTUM_SPACETIME_GRAVITY_v0.3.tex").read_text(
        encoding="utf-8"
    )
    required = (
        "Relative Subjectivity is not an individual subject",
        "G_{\\mu\\nu}=(3/5)\\Theta_{\\mu\\nu}",
        "conditional source-first local Einstein completion",
        "not a completed field theory or a derivation of general relativity",
    )
    missing = [marker for marker in required if marker not in tex]
    if missing:
        raise SystemExit(f"missing required claim markers: {missing}")

    print("PASS: v0.3 primary artifact hashes and claim markers verified")


if __name__ == "__main__":
    main()
