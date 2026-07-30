# Experiment 001A Result

## Status

**PASS**

## Classification

**DT-1 — dissipative or buffered state transfer**

- F0 carry-only component: `DT-0`
- F1 buffered component: `DT-1`

## Primary endpoints

- F0 exact behavioral classes: `2`
- F1 exact behavioral classes: `4`
- full-present-matched future-divergence witnesses: `0`
- latest-overwrite violations in F0: `0`
- unexpected role-exchange effects: `0`
- relational recoveries: `0`
- scalar-return cases: `6`
- complete-state-return cases: `4`

## Exact finite structure

- F0 transition monoid order: `3`
- F1 transition monoid order: `8`
- exhaustive history cases: `524286`
- coordinate covariance: `true`

## Interpretation

The canonical carry-only process is fully determined by its current
carry and the most recent kill or generate event. The explicit SUM
buffer adds a current output record, but its distinctions are exactly
accounted for by ordinary declared memory. No matched-present history
pair develops different future behavior, and exchanging the two input
roles produces no effect beyond the symmetric full-adder equations.

Kill/generate excursions can restore a scalar value, and in restricted
cases a complete declared state, but no nontrivial pair-specific
bilateral structure exists to be restored. These returns are therefore
classified as value restoration or buffering, not relational recovery.

Experiment 001A consequently identifies the registered full-adder
system as a dissipative finite-state control and matched null, not as
an operational relational carrier.

## Claim boundary

This result concerns only the registered finite models. It does not
establish subjectivity, Intersection Subjectivity, a historical CDC
6600 implementation, or any unregistered physical realization.

## Reproducibility receipt

- registration commit: `a7ebf8c99b6390dc69e025c203e5b75353a9bd82`
- remote: `https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics.git`
- schema: `siel-experiment-001a-dissipative-transfer-v1`
