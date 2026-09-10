#!/usr/bin/env python3
import hashlib
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
PDF = PACKAGE / "Braid_Quantum_Lorentz_Unification_Preprint_v0.1.pdf"
TEX = PACKAGE / "BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.1.tex"
TITLE = "Subjectivity Intersection Mathematics: A Common Pointed-Braid Source for Quantum History and Lorentzian Geometry"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


metadata = json.loads((PACKAGE / "ZENODO_METADATA_v0.1.json").read_text())
manifest = json.loads((PACKAGE / "ARTIFACT_MANIFEST_v0.1.json").read_text())
entries = {entry["role"]: entry for entry in manifest["files"]}

assert metadata["title"] == TITLE
assert metadata["resource_type"] == "publication-preprint"
assert metadata["version"] == "v0.1"
assert metadata["access_right"] == "open"
assert metadata["license"] == "cc-by-4.0"
assert PDF.stat().st_size == entries["public_preprint_pdf"]["bytes"]
assert sha256(PDF) == entries["public_preprint_pdf"]["sha256"]
assert sha256(TEX) == entries["public_authoring_source"]["sha256"]

info = subprocess.check_output(["pdfinfo", str(PDF)], text=True)
assert f"Title:           {TITLE}" in info
assert "Pages:           14" in info
assert "Encrypted:       no" in info

text = subprocess.check_output(["pdftotext", str(PDF), "-"], text=True)
for required in (
    "Subjectivity Intersection Mathematics:",
    "Theorem 5.1 (Pointed Correlation-Kernel Braid Quantum",
    "Geometry Local Composition)",
    "This is a working theoretical preprint.",
    "It is not peer reviewed",
    "doi:10.5281/zenodo.22166167",
    "OpenAI Codex",
):
    assert required in text, required

print("title_consistency PASS")
print("metadata_consistency PASS")
print("pdf_sha256 PASS", entries["public_preprint_pdf"]["sha256"])
print("tex_sha256 PASS", entries["public_authoring_source"]["sha256"])
print("pdf_structure PASS 14_pages_unencrypted")
print("claim_ceiling_and_ai_disclosure PASS")
