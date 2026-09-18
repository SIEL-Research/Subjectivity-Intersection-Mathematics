# Braid-First Quantum Spacetime Gravity Preprint v0.3

This directory contains the public-repository working draft for:

> Satoru Watanabe, *A Braid-First Route to Quantum Structure, Spacetime,
> and Gravity: From Generated Objectivity to a Finite Metric-Affine Action
> Principle*, v0.3 (18 September 2026).

The manuscript develops one integrated Braid-first chain from a
quantum-algebraic pointed-braid source to a classical four-dimensional
carrier, finite coframe and metric-affine dynamics, source-graph locality,
continuous cell representatives, two source-native finite actions, local
Noether identities, and a conditional source-first local Einstein metric
two-jet.

The pointwise relation

```text
G_{mu nu} = (3/5) Theta_{mu nu}
```

is exact at the registered base point under three explicit bridge assumptions:
the response is read as physical stress-energy, the previously registered
coupling `kappa = 3/5` is retained, and free Weyl curvature is set to zero.
This is a conditional local Einstein completion, not a derivation of general
relativity or a neighborhood solution of the Einstein equations.

The ontology is also stated explicitly: Relative Subjectivity is not a person,
organism, mind, or conscious observer. It is the proposed non-personal relative
mode associated with time, clocking, ordering, and comparison. On that
interpretation it belongs to physical reality before life and humanity. This
ontological identification is not itself proved by the Braid certificates.

## Files

- `BRAID_FIRST_QUANTUM_SPACETIME_GRAVITY_v0.3.tex`: authoring source.
- `BRAID_FIRST_QUANTUM_SPACETIME_GRAVITY_v0.3.pdf`: reviewed 22-page PDF.
- `ARTIFACT_MANIFEST_v0.3.json`: exact identities of the primary artifacts.
- `PUBLIC_VERIFICATION_NOTES.md`: build, inspection, and claim boundaries.
- `RELEASE_NOTES.md`: scope of the v0.3 working draft.
- `verify_release.py`: local integrity checks for the primary artifacts.

## Build and verification

Run XeLaTeX twice from this directory:

```text
xelatex -interaction=nonstopmode -halt-on-error BRAID_FIRST_QUANTUM_SPACETIME_GRAVITY_v0.3.tex
```

Then run:

```text
python3 verify_release.py
```

This repository update publishes a working draft only. It does not create a
Zenodo version, DOI, GitHub Release, journal submission, peer-review claim, or
empirical validation claim.
