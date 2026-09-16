# Braid-Quantum-Lorentz Unification Preprint v0.81

This directory contains the public-repository working draft for:

> Satoru Watanabe, *Subjectivity Intersection Mathematics: A Pointed-Braid
> Source for Quantum History, Lorentzian Geometry, and Reciprocal
> Backreaction*, v0.81 (2026).

Version 0.81 is a full integrated revision. It retains only the v0.8
finite-source, quantum-history, Lorentz-carrier, algebraic-completion, and
conditional local results that remain supported, and replaces the open
geometric completion with the post-v0.8 moving-carrier programme through
revision `4b0e803b9`.

The principal new finite results are rank-four projector confinement,
moving-projector curvature, curvature-derived dual completion, a direct
characteristic-zero lift, complementary B/Q carrier lifts, an inverse-closed
reciprocal relative connection, a local 1+3 metric, rank-two relative
nonmetricity, and a positive real relative polar branch. The failed
inverse-transpose transport, failed Gram-adjoint repair, failed common
nondegenerate preserved metric, mark-dependence controls, and unresolved
continuum/stress gates are preserved as primary boundaries.

This is a public working draft. It is not peer reviewed and does not establish
physical spacetime, Einstein dynamics, an infinite-mode QFT, a unique braid
origin of four dimensions, empirical gravity, subjectivity, or consciousness.

## Files

- `BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.81.tex`: authoring source.
- `Braid_Quantum_Lorentz_Unification_Preprint_v0.81.pdf`: reviewed 29-page PDF.
- `ARTIFACT_MANIFEST_v0.81.json`: exact file identities and scope.
- `INTELLECTUAL_PROVENANCE_LEDGER_v0.81.json`: result and claim provenance.
- `PUBLIC_VERIFICATION_NOTES.md`: verification summary and claim boundary.
- `verify_release.py`: local integrity and boundary checks.

## Build

Run XeLaTeX twice from this directory:

```text
xelatex -interaction=nonstopmode -halt-on-error BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.81.tex
```

Then run:

```text
python3 verify_release.py
```

No Zenodo deposit or GitHub Release is created by this repository update.
