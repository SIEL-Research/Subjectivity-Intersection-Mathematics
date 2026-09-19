# Public verification notes — v0.4

## Artifact identity

The primary PDF, LaTeX source, Japanese abstract, changelog, release notes, and
license are identified by `ARTIFACT_MANIFEST_v0.4.json`. Run
`python3 verify_release.py` from this directory to verify the SHA-256 hashes
and required claim-boundary markers. The page count was checked separately
with `pdfinfo` during release preparation.

## Build and layout review

- Engine: XeLaTeX.
- Build: two consecutive successful final passes.
- Output: 22 A4 pages.
- Static checks: no undefined citation or reference and no overfull box in the
  final log.
- Visual review: all 22 pages were rendered and inspected for clipping,
  overlap, missing glyphs, and broken page flow.
- PDF metadata: title, subtitle-level subject, author, and keywords match v0.4.

## Scientific provenance

The finite-source construction extends the preserved v0.3 lineage. The new
continuum statement is traced to the SIEL Research Agent through commit
`e1e0ca4a4e22da8a4ede079a1785bb2056a213f6`, especially the BGCE038
conditional four-law packet and the BGCE075--BGCE080 boundary audits. Those
internal certificates are not duplicated in this public directory.

## Claim boundary

The neighborhood Einstein equation is an Euler--Lagrange consequence of the
declared continuum action only under NL1--NL4. The manuscript does not claim
that those laws have been derived from the Braid source alone. The tested
temporal four-flow distribution is noninvolutive, and no first-class
constraint algebra, quantized continuum gravitational field, ultraviolet
completion, or empirical gravitational identification is claimed.

The constructive refutation targets the universal necessity of objectivist
primacy. It does not establish phenomenal consciousness, does not identify
mathematical standpoints with conscious subjects, and does not claim an
empirical disproof of every form of realism.
