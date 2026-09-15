#!/usr/bin/env python3
"""Verify the local Braid-unification v0.8 release package."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "ARTIFACT_MANIFEST_v0.8.json"
TEX = PACKAGE / "BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.8.tex"
PDF = PACKAGE / "Braid_Quantum_Lorentz_Unification_Preprint_v0.8.pdf"
METADATA = PACKAGE / "ZENODO_METADATA_v0.8.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads(MANIFEST.read_text())
metadata = json.loads(METADATA.read_text())
assert manifest["version"] == "v0.8"
assert manifest["zenodo_concept_doi"] == "10.5281/zenodo.22693964"
assert manifest["previous_public_version"]["doi"] == "10.5281/zenodo.22732287"
assert manifest["source_boundaries"]["main_stress_reduction_line"]["through"] == "UB622"

for record in manifest["files"]:
    path = PACKAGE / record["name"]
    assert path.is_file(), path
    assert path.stat().st_size == record["bytes"], path
    assert sha256(path) == record["sha256"], path

tex = TEX.read_text()
required_phrases = [
    "Working preprint v0.8",
    "type-$5^\\infty$ UHF",
    "E_{2,\\infty}",
    "\\rank L_\\infty=10",
    "Post-UB610 stress reduction",
    "one global moving-reference inequality",
    "not completed quantum gravity",
]
for phrase in required_phrases:
    assert phrase in tex, phrase
assert "Working preprint v0.7" not in tex
assert "Japanese" not in tex

pdfinfo = subprocess.run(
    ["pdfinfo", str(PDF)], check=True, capture_output=True, text=True
).stdout
assert "Encrypted:       no" in pdfinfo
pages = next(
    int(line.split(":", 1)[1])
    for line in pdfinfo.splitlines()
    if line.startswith("Pages:")
)
assert pages == manifest["pdf_pages"] == metadata["file"]["pages"]
assert PDF.stat().st_size == metadata["file"]["bytes"]
assert sha256(PDF) == metadata["file"]["sha256"]

log = PACKAGE / "BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.8.log"
if log.exists():
    log_text = log.read_text(errors="replace")
    assert "Undefined control sequence" not in log_text
    assert "Citation `" not in log_text or "undefined" not in log_text
    assert "Reference `" not in log_text or "undefined" not in log_text

print(
    json.dumps(
        {
            "version": "v0.8",
            "manifest_files": len(manifest["files"]),
            "pdf_pages": pages,
            "pdf_sha256": sha256(PDF),
            "series_identity": "BRAID_UNIFICATION_NOT_SIM_V4_2",
            "uhf_scope_explicit": "PASS",
            "physical_continuum_not_inferred": "PASS",
            "stress_boundary_explicit": "PASS",
            "status": "PASS_LOCAL_AUTHOR_RELEASE_REVIEW_PACKAGE",
        },
        indent=2,
    )
)
