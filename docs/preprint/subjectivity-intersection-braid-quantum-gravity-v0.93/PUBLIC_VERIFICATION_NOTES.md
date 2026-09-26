# Verification notes — v0.93 local release candidate

Date: 2026-09-26

## Build

The manuscript was compiled from the release source with XeLaTeX. The final log contains no fatal error, undefined reference, missing citation, float-too-large warning, or overfull box. Non-fatal font-shape, underfull-box, and retained long-table split warnings do not remove content.

## PDF checks

- Format: A4, unencrypted PDF 1.7.
- Pages: 67; v0.92 had 65 pages.
- Size: 429,500 bytes.
- SHA-256: `ea0f77582c4423f13b88180590770075fea4701f3edadc951996d1257d971081`.
- MD5: `b95f27a963f7d9a177b458f9b38373f5`.
- Extracted text: 5,017 lines and 30,654 words.
- No Japanese abstract or Japanese manuscript text is embedded.
- All 67 final pages were rendered to PNG, inspected in four contact sheets, and checked at readable scale for the title, BGCE570--571 sections, matrices, completion list, ledgers, conclusion, provenance, references, and dependency table.
- No clipping, overlap, black replacement glyph, missing table row, or broken section transition was observed.

## Scientific checks

- The complete 65-page v0.92 text is retained and extended, not summarized.
- Source snapshot: SRA completion-ledger commit `6f92d231444b17bf0f4dcb082f65f0d84518f018`.
- BGCE531 is reported as an exploratory sample-level real-QPU PASS; BGCE533's statistical NO-GO is preserved.
- BQGEULER-004 is limited to all-real-time energy-norm convergence on the hierarchical two-slot carrier; physical ADM/Fierz-Pauli and nonlinear Euler claims are excluded.
- Matter claims separate relative/source-derived, device-relative, declared-completion, observed-label, and empirical layers.
- BGCE569's separated clock/pair NO-GO is preserved; BGCE570 closes only the declared joint clock--Nambu completion and is not described as an unchanged-raw-source theorem.
- BGCE571's CKM, PMNS, and `3x6` active--neutral matrices are reported as unfitted source-order outputs. No observed-name dictionary is selected and no measured-value agreement is claimed.
- The finite coefficient `1` and routing ratio `3/5` are reported as differently typed exact quantities.

## Public boundary

This package is a local release candidate. No v0.93 GitHub push or Zenodo version has been created. The public predecessor is v0.91 at DOI `10.5281/zenodo.22958600`; the all-versions concept DOI is `10.5281/zenodo.22693964`.

Public release requires exact approval of the PDF, metadata, repository action, and Zenodo action. GitHub and Zenodo publication are not journal submission, peer review, independent replication, or empirical validation.
