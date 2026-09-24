# Subjectivity-Intersection Braid Quantum Gravity v0.83

This directory contains the canonical full v0.83 working preprint and its public verification materials.

- `SUBJECTIVITY_INTERSECTION_BRAID_QUANTUM_GRAVITY_v0.83.pdf` is the canonical 48-page manuscript.
- `SUBJECTIVITY_INTERSECTION_BRAID_QUANTUM_GRAVITY_v0.83.tex` is its LaTeX source.
- `SUBJECTIVITY_INTERSECTION_BRAID_QUANTUM_GRAVITY_v0.7_RETAINED_DERIVATION.tex` preserves the still-operative detailed derivation inherited through v0.82.
- `CHANGELOG_v0.83.md` records the change from v0.82.
- `CLAIM_EVIDENCE_MATRIX_v0.83.md` separates exact results, scoped derivations, negative results, calibration inputs, and open claims.
- `ARTIFACT_MANIFEST_v0.83.json` records the immutable file identities in this repository release.
- `PUBLIC_VERIFICATION_NOTES.md` records the build, evidence, and visual checks.
- `ZENODO_METADATA_v0.83.json` is a proposed metadata packet only; no v0.83 Zenodo deposit is asserted.

## Main result and boundary

Version 0.83 retains the complete v0.82 manuscript: the finite Lorentz parent, four-component total Ward law, one-cycle CPTP backreaction, scoped Einstein equation `G=(3/5)T`, two-helicity massless spin-2 limit, and the declared extension producing Standard-Model representation and interaction types.

It adds the executed BGCE440 calibration through revisions 19--21. A real AWS Braket/Rigetti Cepheus-1-108Q Ramsey run produced 768 per-shot outcomes from 12 programs and passed the revision-matched independent E2 audit. The fitted transition frequency is `4,484,999,494.698898 Hz` with standard error `9,314.910565190186 Hz` and `R^2 = 0.9825714110512933`. Under the frozen source gap `4`, this gives `tau* = 1.419442238778493e-10 s`, `ell* = 0.04255380777524273 m`, and `E* = 7.429480314095178e-25 J`.

Using the external CODATA 2022 input `G = 6.67430(15)e-11 m^3 kg^-1 s^-2`, exact `c`, and frozen direct-parent coupling `kappa = 1`, the scoped conversion gives `kappa_cal = 2.076647442844972e-43 m/J` and `sigma* = 2.659257381834094e45 Pa`, with partial relative standard uncertainty `2.285490726338230e-5`.

These are not a prediction of Newton's constant, a Braid gravity measurement, or empirical quantum gravity. The Ramsey result is an exploratory, device-relative implemented-Braid calibration. Public AWS metadata does not establish the provider clock's complete SI traceability or its systematic uncertainty; provider attestation remains required.

The constraint boundary is also updated through BGCE442. The fixed finite source algebra has only inner derivations and no outer three-plane, so the next live route is the BGCE443 refinement-limit search for closable unbounded derivations. No gravitational first-class constraint algebra is claimed.

The ultraviolet/all-scale package is updated through BGCE449. The compatible finite source-cylinder channels extend to a strongly continuous AF/quasi-local UCP semigroup with complete bound one at every refinement depth. The ten source-fixed metric directions generate 55 unordered second-response columns, and an exact rational interval certificate proves row rank 35 for the actual UB612 quartic tensor throughout its saved coefficient box. This closes the registered all-refinement channel and actual-quartic-response problem in scope. It does not establish a full metric Frechet Hessian, uniform nonpolynomial sampling, bounded composite stress, smooth-spacetime renormalizability, or full physical UV completion.

## Version relation

v0.83 supersedes v0.82 as the current GitHub working manuscript without overwriting it. The public v0.8 record remains preserved at [Zenodo DOI 10.5281/zenodo.22735310](https://doi.org/10.5281/zenodo.22735310).

## Release status

`PUBLIC_GITHUB_WORKING_PREPRINT__ZENODO_NOT_DEPOSITED`.

This repository publication is not peer review, journal acceptance, independent replication, a new Zenodo version, or empirical confirmation of quantum gravity.
