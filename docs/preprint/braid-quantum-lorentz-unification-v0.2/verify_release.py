#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
TITLE="Subjectivity Intersection Mathematics: A Common Pointed-Braid Source for Quantum History and Lorentzian Geometry"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((HERE/"ARTIFACT_MANIFEST_v0.2.json").read_text())
z=json.loads((HERE/"ZENODO_METADATA_v0.2.json").read_text())
p=next(x for x in m["files"] if x["role"]=="public_preprint_pdf")
t=next(x for x in m["files"] if x["role"]=="public_authoring_source")
pdf=HERE/p["path"]; tex=HERE/t["path"]
assert m["version"]==z["version"]=="v0.2"
assert m["result_boundary"]["new_content"]=="UB344-UB387"
assert z["title"]==TITLE and z["record"]=="new_version_of_10.5281/zenodo.22693965"
assert pdf.stat().st_size==p["bytes"] and sha(pdf)==p["sha256"] and sha(tex)==t["sha256"]
info=subprocess.check_output(["pdfinfo",str(pdf)],text=True)
assert f"Title:           {TITLE}" in info and "Pages:           16" in info and "Encrypted:       no" in info
text=subprocess.check_output(["pdftotext",str(pdf),"-"],text=True)
for q in ("Working preprint v0.2","A certified finite PBM–BIX realization","Braid-null transduction","Restricted same-source dynamic patch","UB386/387","10.5281/zenodo.22693965","It is not peer reviewed","OpenAI Codex"): assert q in text,q
print("public_v0.2_release_verification PASS")
print("pdf_sha256",p["sha256"])
