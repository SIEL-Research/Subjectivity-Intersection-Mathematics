# Verification notes — v0.92 local release candidate

Date: 2026-09-26

## Build

The manuscript was compiled from the release source with XeLaTeX. The final log contains no fatal error, undefined reference, missing citation, float-too-large warning, or overfull box. Non-fatal font-shape, underfull-box, and retained long-table split warnings do not remove content.

## PDF checks

- Format: A4, unencrypted PDF 1.7.
- Pages: 65; v0.91 had 59 pages.
- Size: 417,979 bytes.
- SHA-256: `378a9107c3a93829dd922f56ac6708216b55fc8f6b02f485a3a861e950652ea8`.
- MD5: `c1ce3998784b4583b7ff9a270aa7d5a4`.
- Extracted text: 4,815 lines and 29,507 words.
- No Japanese abstract or Japanese manuscript text is embedded.
- All 65 final pages were rendered to PNG, inspected in five contact sheets, and checked at readable scale for the title, new sections, completion list, ledgers, conclusion, provenance, references, and dependency table.
- No clipping, overlap, black replacement glyph, missing table row, or broken section transition was observed.

## Scientific checks

- The complete v0.91 text is retained and extended, not summarized.
- Source snapshot: SRA completion-ledger commit `50aca5a404fbed180a2d76f8a4c6176b9949db91`.
- BGCE531 is reported as an exploratory sample-level real-QPU PASS; BGCE533's statistical NO-GO is preserved.
- BQGEULER-004 is limited to all-real-time energy-norm convergence on the hierarchical two-slot carrier; physical ADM/Fierz-Pauli and nonlinear Euler claims are excluded.
- Matter claims separate relative/source-derived, device-relative, conditional-extension, and observed-physics layers.
- BGCE568's `y_nu=+1` is explicitly conditional; BGCE569's Majorana-scale NO-GO is preserved.
- The finite coefficient `1` and routing ratio `3/5` are reported as differently typed exact quantities.

## Public boundary

This package is a local release candidate. No v0.92 GitHub push or Zenodo version has been created. The public predecessor is v0.91 at DOI `10.5281/zenodo.22958600`; the all-versions concept DOI is `10.5281/zenodo.22693964`.

Public release requires exact approval of the PDF, metadata, repository action, and Zenodo action. GitHub and Zenodo publication are not journal submission, peer review, independent replication, or empirical validation.
