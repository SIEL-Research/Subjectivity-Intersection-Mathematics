# Public verification notes — v0.91

Date: 2026-09-25

## Build

The manuscript was compiled from the release source with XeLaTeX in three
passes. The final log contains no fatal error, undefined reference, missing
citation, or overfull box. The remaining font-substitution and underfull-box
warnings are non-fatal and do not remove manuscript content.

## PDF checks

- Format: A4, unencrypted PDF 1.7.
- Pages: 59.
- Size: 393,245 bytes.
- SHA-256: `d1c9367dadacc1d1f25f5a8582e16b7a0cce76bcdda5f1407da93e1744bee296`.
- MD5: `d98794e82d6338b2102eed18eeedd5bf`.
- Extracted text: 3,442 lines and 26,940 words.
- All 59 final pages were rendered to PNG and inspected in contact sheets.
- The title and abstract, new quantum-reconstruction and actuation sections,
  claim ledger, chronology, conclusion, appendices, bibliography, and final
  dependency table were additionally checked at readable scale.
- A first visual pass exposed literal `qquad` strings in nine new equations.
  They were corrected to LaTeX spacing commands, the PDF was rebuilt in three
  passes, and the affected pages and all-page contact sheets were reinspected.
- No clipping, overlap, black replacement glyph, missing table row, or broken
  continuation was observed.
- No Japanese abstract or Japanese manuscript text is embedded.

## Scientific checks

- The v0.9 content and its scoped BGCE138–457 lineage are retained without
  compression. The new scientific snapshot is the completion-ledger revision
  `041fca39d39ff77b82024c45dbf4b1749d9b8f16` through BGCE491.
- BGCE458–464 reconstruct the 36-dimensional finite complex carrier, declared
  source-dagger probability rule, exact `Z2` superselection, and
  `M18(C) direct-sum M18(C)` observable algebra. Ordinary flip also generates
  a complex sector, so Braid exclusivity is not claimed.
- BGCE465–476 establish the canonically compressed six-order mixed-unitary
  engine, minimal typed controlled-`C` route, carrier reflection, spectral
  polynomial, and associated route-specific NO-GO results.
- BGCE477–487 preserve the distinction between observable membership and
  coherent actuation, close the typed source-word LCU block encodings, identify
  the exact four-probability control solder, and construct a raw-source signal
  qubit with continuous `SU(2) tensor I36` action.
- BGCE488 gives an exact heralded actuator for all 32 declared sector/control
  cases with success probabilities approximately `10^-45.89` to `10^-88.47`.
- BGCE489 gives exact phase-matched unit-success amplification but requires
  approximately `10^23.14` to `10^44.43` actuator calls for the fixed Lagrange
  black box. The manuscript preserves this scoped efficiency NO-GO.
- BGCE490 changes to an exact Chebyshev basis, improves success by 39.40–87.10
  decimal orders, and reduces deterministic actuation to 7–2,793 base calls
  and 203–39,102 block-encoding queries across all 32 cases.
- BGCE491 hermitianizes the existing source-word LCU unitary and uses the
  success-address reflection to reproduce the exact Chebyshev walk without an
  explicit square-root-defect or spectral-read primitive.
- The manuscript explicitly separates standard dagger probability, LCU, block
  encoding, QSP/QSVT, and amplitude-amplification machinery from the
  source-specific finite decomposition and certificates.
- The typed source-word `SELECT` and success-address mark remain explicit
  extensions. No hardware
  execution, Braid-versus-GR apparatus residual, prediction of Newton's
  constant, unrestricted physical UV completion, or empirical quantum-gravity
  validation is asserted.

## Public boundary

This package is the approved GitHub working-preprint release. The Zenodo
version deposit is separately in progress and no v0.91 DOI is asserted until
the public record and deposited-file identity have been verified. GitHub
publication is not a GitHub Release, journal submission, peer review,
independent replication, or empirical validation.
