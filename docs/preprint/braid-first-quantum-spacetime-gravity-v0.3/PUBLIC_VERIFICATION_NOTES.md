# Public verification notes

## Artifact identity

The primary PDF and LaTeX source are identified by
`ARTIFACT_MANIFEST_v0.3.json`. Run `python3 verify_release.py` from this
directory to check their SHA-256 hashes and the expected manuscript markers.

## Build and layout review

- Engine: XeLaTeX.
- Build: two consecutive successful passes.
- Output: 22 A4 pages.
- Static checks: no undefined citation or reference and no overfull horizontal
  or vertical box reported.
- Visual review: all pages rendered to PNG; the updated definition pages,
  long-table transition, conclusion, provenance, and references were inspected
  for clipping, overlap, missing glyphs, and broken page flow.

## Scientific provenance

The manuscript reports theoretical and computational results from the SIEL
Research Agent audit lineage through commit `27dd70da0`, including records
identified in the manuscript as A57S-X62--X99 and A57S-CE1A--CE4W. Those
scientific certificates are not duplicated in this repository directory.

## Claim boundary

The exact pointwise Einstein relation is conditional on explicit bridges and
does not establish general relativity in a neighborhood. The two finite actions
have not yet been shown to close all Euler equations when summed with their
frozen unit coefficients. The manuscript is not peer reviewed, independently
replicated, or empirically validated.

The statement that Relative Subjectivity is non-personal and exists prior to
life is part of the declared ontology. The finite Braid mathematics supplies a
structural realization of distinct source standpoints and their generated
carrier; it does not by itself prove the identification with physical time or
consciousness.
