#!/usr/bin/env python3
"""Verify the public-repository Braid-unification v0.81 working draft."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "ARTIFACT_MANIFEST_v0.81.json"
TEX = PACKAGE / "BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.81.tex"
PDF = PACKAGE / "Braid_Quantum_Lorentz_Unification_Preprint_v0.81.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads(MANIFEST.read_text())
assert manifest["version"] == "v0.81"
assert manifest["parent_version"] == "v0.8"
assert manifest["evidence_cutoff_commit"] == "4b0e803b9"
assert manifest["release_state"] == "PUBLIC_REPOSITORY_WORKING_DRAFT_NOT_ZENODO_NOT_GITHUB_RELEASE"

for record in manifest["files"]:
    path = PACKAGE / record["name"]
    assert path.is_file(), path
    assert path.stat().st_size == record["bytes"], path
    assert sha256(path) == record["sha256"], path

tex = TEX.read_text()
for phrase in (
    "Public working preprint v0.81",
    "Finite rank-four confinement",
    "Metric NO-GO and metric-affine completion",
    "Current assumption ledger",
    "Reproducibility checklist",
    "not peer reviewed",
):
    assert phrase in tex, phrase

pdfinfo = subprocess.run(
    ["pdfinfo", str(PDF)], check=True, capture_output=True, text=True
).stdout
assert "Pages:           29" in pdfinfo
assert "Page size:       595.28 x 841.89 pts (A4)" in pdfinfo
assert "Encrypted:       no" in pdfinfo

text = subprocess.run(
    ["pdftotext", str(PDF), "-"], check=True, capture_output=True, text=True
).stdout
for phrase in (
    "Public working preprint v0.81",
    "Metric NO-GO",
    "Current assumption ledger",
    "Reproducibility checklist",
):
    assert phrase in text, phrase

print(json.dumps({
    "version": "v0.81",
    "pdf_pages": 29,
    "pdf_sha256": sha256(PDF),
    "tex_sha256": sha256(TEX),
    "evidence_cutoff": "4b0e803b9",
    "status": "PASS_PUBLIC_REPOSITORY_WORKING_DRAFT",
}, indent=2))
