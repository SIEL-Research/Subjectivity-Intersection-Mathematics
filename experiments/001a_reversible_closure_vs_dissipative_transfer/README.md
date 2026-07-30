# Experiment 001A — Reversible Closure versus Dissipative Relational Transfer

## Registration status

**REGISTERED DESIGN — 2026-07-30 — CONFIRMATORY EXECUTION PENDING**

The authoritative registration is the first public GitHub commit containing
this document, `PREREGISTRATION.md`, `run.py`, `test_run.py`, and
`registration_manifest.json`. Confirmatory execution may begin only after
that commit is public.

## Purpose

Experiment 001A compares the reversible `C3`-type positive control from
Experiment 001 with the standard full-adder kill/generate/propagate process.
It asks whether the latter retains history beyond its current carry and
ordinary SUM buffering, or instead provides an exact dissipative null for
relational-carrier tests.

The canonical full adder is treated as a Mealy transducer. Its persistent
carry state, emitted SUM/carry output, one-step SUM buffer, role-exchange
symmetry, overwrite behavior, and exact observational equivalence classes are
audited separately.

## Frozen classification

- `DT-0`: reducible overwrite-and-propagate control;
- `DT-1`: dissipative or buffered state transfer reproduced by registered
  non-relational memory controls;
- `DT-2`: operational relational-carrier candidate satisfying every frozen
  strong condition.

The complete criteria and claim boundary are specified in
[PREREGISTRATION.md](PREREGISTRATION.md).

## Confirmatory command

From the repository root, after the registration commit is public:

    python3 experiments/001a_reversible_closure_vs_dissipative_transfer/run.py \
      --mode confirmatory \
      --out-dir experiments/001a_reversible_closure_vs_dissipative_transfer/results \
      --check

The command refuses to overwrite an existing result directory.

## Claim boundary

This is a finite mathematical calibration. It does not test subjectivity,
Intersection Subjectivity, a physical CDC 6600 implementation, or a
biological system. A mathematical state or output channel is not identified
with subjectivity.
