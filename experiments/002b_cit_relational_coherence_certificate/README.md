# Experiment 002B — CIT Relational-Coherence Certificate Audit

## Registration status

**REGISTERED DESIGN — 2026-07-28 — CONFIRMATORY EXECUTION PENDING**

The authoritative registration is the first public GitHub commit containing
this document, `PREREGISTRATION.md`, `run.py`, `test_run.py`, and
`registration_manifest.json`. Confirmatory execution may begin only after
that commit is visible on the public remote.

## Purpose

Experiment 002A reproduced Luke Casson Leighton's dual-ring Boolean
construction but classified its scalar `CIT` readout as Class 0 when tested as
a pair-indexed, history-bearing relational carrier. Each local full adder
already forces its distinction bit to one in the registered operational
modes.

Subsequent discussion with Luke and Marcel Wende identified a different
possible role. `CIT` may be a certificate that several comparison sites agree
that a coordinated process remains structurally and temporally valid, without
itself storing the process history.

Experiment 002B tests that narrower possibility. It does not reopen the
Experiment 002A carrier classification.

## Central test

The decisive case is one in which:

1. the clockwise ring remains locally valid;
2. the anticlockwise ring remains locally valid;
3. both local SUM/CARRY complement relations remain valid;
4. the registered relation between the orientations is broken; and
5. only the complete two-orientation readout detects the failure.

Sensitivity to a broken SUM, CARRY, delay, or comparison channel is useful,
but is classified as local integrity detection if either ring can detect it
alone.

## Registered certificate classes

- **RC-0 — static local tautology:** no registered fault-detection role beyond
  a constant-one control.
- **RC-1 — reducible distributed integrity certificate:** aggregates local
  integrity checks across the two rings, but is exactly reproduced by their
  conjunction and has no exclusive relational detection.
- **RC-2 — irreducible two-orientation coherence certificate:** detects at
  least one registered relation-only failure while both local certificates
  remain valid, and the detection is unavailable from either ring or their
  registered local controls alone.

These classes are separate from the carrier classes of Experiment 002.

## Audit structure

The executable audit evaluates:

- admissible state, label, and orientation transformations;
- local integrity failures, including bit corruption and unmatched local
  delays;
- relation-only failures, including whole-ring epoch skew, locally valid
  partner substitution, inconsistent cross-ring operational controls, and
  site remapping that preserves each local comparison;
- the exact equivalence or non-equivalence between full `CIT` and the
  conjunction of the two local ring certificates;
- safety and liveness in a registered abstract gating task; and
- detection latency and recovery for temporary local and relation-only
  faults.

## Claim boundary

This is a finite Boolean audit. It does not reconstruct the historical CDC
6600, establish a physical implementation, or provide evidence for
subjectivity. An RC-2 result would establish only the registered finite role
of a relational-coherence certificate. It would not make `CIT` identical to
`C`, a relational carrier, or intersection subjectivity.

## Registered command

From the repository root, after the registration commit is public:

    python3 experiments/002b_cit_relational_coherence_certificate/run.py \
      --mode confirmatory \
      --out-dir experiments/002b_cit_relational_coherence_certificate/results \
      --check
