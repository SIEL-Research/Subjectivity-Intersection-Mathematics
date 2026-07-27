# Experiment 002B Preregistration

## Title

**CIT as a Relational-Coherence Certificate**

## Registration date

2026-07-28

## Registration rule

This preregistration is frozen by the first public GitHub commit containing:

- this document;
- `README.md`;
- `run.py`;
- `test_run.py`; and
- `registration_manifest.json`.

The registered upstream authorities are the preserved Luke Casson Leighton
source and the independent Experiment 002A implementation recorded by hash in
the manifest. Confirmatory output may be generated only after the registration
commit is public. The program refuses to overwrite an existing result
directory and records the registration commit in its result receipt.

## Question

Can the complete `CIT` readout detect a failure in the relation between two
oppositely oriented processes when both processes remain locally valid, or is
it only the reducible conjunction of local integrity checks?

## Scope correction from Experiment 002A

Experiment 002A asked whether `CIT` was a pair-indexed, history-bearing
relational carrier. It was classified as Class 0 for that purpose. Experiment
002B does not modify or appeal that result.

The new candidate is a certificate, not a carrier. A certificate may report
whether registered coordination conditions hold without retaining pair
identity or history.

## Registered hypotheses

### H0 — static local tautology

`CIT` remains one throughout the registered admissible and fault conditions
and supplies no fault-detection role beyond a constant-one gate.

### H1 — reducible distributed integrity certificate

`CIT` detects at least one registered local integrity failure and preserves
all admissible cases, but every detection is exactly reproduced by the
conjunction of the two local ring certificates. No relation-only failure is
detected while both local certificates pass.

### H2 — irreducible two-orientation coherence certificate

At least one registered relation-only failure makes the complete certificate
fail while both local ring certificates remain valid. The result cannot be
reproduced by a constant-one gate, either local ring alone, or the registered
conjunction of local integrity decisions.

## Registered classes

- H0 maps to `RC-0`.
- H1 maps to `RC-1`.
- H2 maps to `RC-2`.

The labels `RC-0`, `RC-1`, and `RC-2` are certificate classifications and do
not reuse the carrier classes of Experiment 002.

## Frozen construction

For each ring and site, the operational distinction is:

    D = buffered_SUM XOR buffered_CARRY

The local ring certificates are:

    L_plus  = AND_reduce(D_plus)
    L_minus = AND_reduce(D_minus)

The complete readout is:

    CIT = AND_reduce(D_plus AND D_minus)

The executable separately computes:

    L_combined = L_plus AND L_minus

Equality between `CIT` and `L_combined` is tested in every case rather than
assumed in the interpretation.

## Intervention taxonomy

### A — admissible transformations

These cases are registered as valid and should remain permitted:

- all 64 paired three-bit states in both single-high operational modes;
- exchange of the two orientation labels;
- cyclic relabelling of all three sites by one position; and
- cyclic relabelling of all three sites by two positions.

### L — local integrity failures

These cases test fault detection but cannot establish an irreducible relation:

- inversion of each SUM or CARRY bit on either ring;
- one-epoch delay of only SUM or only CARRY on either ring; and
- all present/prior state combinations for the unmatched-delay test.

### R — specifically relational failures

In every R case, both local certificates must remain valid by construction.
The registered relation is nevertheless marked invalid through one of:

- a matched whole-ring epoch skew, preserving the ring's internal SUM/CARRY
  epoch;
- substitution of a locally valid but phase-incompatible opposite ring in the
  registered one-hot dual cycle;
- different single-high operational controls on the two rings; or
- a cyclic remapping of one ring's complete SUM/CARRY site pairs relative to
  the other ring.

An R case can support RC-2 only when `L_plus = L_minus = 1` and `CIT = 0`.

## Primary endpoint

The primary endpoint is the number of exclusive relational detections:

    count(R cases with L_plus = 1, L_minus = 1, and CIT = 0)

RC-2 requires this count to be greater than zero.

## Secondary endpoints

- admissible-case false-block rate;
- local-integrity-fault detection rate;
- relation-only-fault detection rate;
- exact equality rate between `CIT` and `L_combined`;
- safety: invalid cases blocked;
- liveness: valid cases permitted;
- valid cycles completed in the temporary-fault sequences;
- fault-detection latency; and
- recovery latency after a temporary fault is removed.

The timing-reference oracle is reported only as the registered task upper
bound. It is not evidence for the `CIT` mechanism.

## Frozen gate controls

- full `CIT`;
- local `L_plus`;
- local `L_minus`;
- registered local conjunction `L_combined`;
- constant-one gate; and
- task-validity oracle.

## Decision rule

1. Return `RC-2` only if the exclusive relational-detection count is positive
   and the full readout is not identical to the local conjunction across all
   registered cases.
2. Otherwise return `RC-1` when all admissible cases pass and `CIT` detects at
   least one local integrity failure.
3. Otherwise return `RC-0`.

No safety score, local fault detection, or historical interpretation may
override the primary endpoint.

## Confirmatory command

    python3 experiments/002b_cit_relational_coherence_certificate/run.py \
      --mode confirmatory \
      --out-dir experiments/002b_cit_relational_coherence_certificate/results \
      --check

## Falsification and interpretation

RC-2 is unsupported if no complete-readout failure occurs while both local
certificates pass, even if `CIT` detects every local corruption. RC-1 means
that `CIT` may still be a useful system-wide integrity aggregation, but not an
irreducible relation detector under the registered construction.

No outcome establishes a historical CDC 6600 implementation, a relational
carrier, subjectivity, three-way subjectivity, or intersection subjectivity.
