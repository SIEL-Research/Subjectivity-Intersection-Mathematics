# Experiment 002B Result

## Status

**PASS**

## Classification

**RC-1 — reducible distributed integrity certificate**

## Primary endpoint

- exclusive relational detections: `0`
- CIT/local-conjunction equality: `3116/3116`

## Gate performance

- admissible cases permitted: `512/512`
- local integrity faults blocked: `1984/1984`
- relation-only faults blocked: `0/620`

## Interpretation

The complete readout detects registered local corruptions across both
rings and preserves every admissible case. It is nevertheless exactly
equal to the conjunction of the two local ring certificates in every
registered case. No relation-only failure is detected while both local
certificates pass.

The registered construction therefore supports a reducible distributed
integrity role, not an irreducible two-orientation coherence certificate.
This does not alter Experiment 002A and does not identify CIT with a
relational carrier or subjectivity.

## Reproducibility receipt

- registration commit: `6558d7c3430cbe8e3818bed46afa2f3325bd60d6`
- remote: `https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics.git`
- schema: `siel-experiment-002b-cit-certificate-v1`
