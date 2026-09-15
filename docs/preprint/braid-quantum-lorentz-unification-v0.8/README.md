# Braid-Quantum-Lorentz Unification Preprint v0.8

This directory contains the local author-release candidate for:

> Satoru Watanabe, *Subjectivity Intersection Mathematics: A Pointed-Braid
> Source for Quantum History, Lorentzian Geometry, and Reciprocal
> Backreaction*, v0.8 (2026).

This is the Braid-unification preprint series under Zenodo concept DOI
`10.5281/zenodo.22693964`. It is distinct from the Subjectivity-Intersection
Mathematics v4.2 preprint series.

Version 0.8 adds the standard type-`5^infinity` UHF completion and the
post-UB610 stress reduction through UB622. It does not claim physical
continuum, complete finite stress, fixed-coupling closure, general 3+1
Einstein dynamics, completed quantum gravity, natural validation, SIC/O3,
subjectivity, or consciousness.

## Build

Run XeLaTeX three times from this directory:

```text
xelatex -interaction=nonstopmode -halt-on-error BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.8.tex
```

Then run:

```text
python3 verify_release.py
```

The exact committed PDF identity is recorded in `ARTIFACT_MANIFEST_v0.8.json`.
