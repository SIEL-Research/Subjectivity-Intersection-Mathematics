# Experiment 002A — CDC 6600 Dual-Ring Invariant Classification Audit

## Registration status

**REGISTERED DESIGN — 2026-07-27 — CONFIRMATORY EXECUTION PENDING**

The authoritative registration is the first public GitHub commit containing
this document, `PREREGISTRATION.md`, `run.py`, `test_run.py`, and
`registration_manifest.json`. Confirmatory execution may begin only after
that commit is visible on the public remote.

## Purpose

Luke Casson Leighton proposed a CDC-6600-inspired Boolean construction with
clockwise and anticlockwise three-latch rings. In the single-high operational
mode, each local full adder produces complementary sum and carry outputs. The
proposal combines the two ring readouts into a scalar `CIT` invariant.

Experiment 002A asks two separate questions:

1. Does the preserved implementation produce the proposed dual-ring
   invariant and reset behaviour?
2. Under the frozen Experiment 002 evidence criteria, does that invariant
   require a pair-indexed, history-bearing relational carrier, or is it fully
   reproduced by a local Boolean null model?

This is an additional classification and negative-control audit for
Experiment 002. It is not a new external-domain experiment.

## Construction under test

For each latch bit `Q`, the local full adder receives:

    x = NOT Q
    H = common inverter control
    Z = common reset control

and returns:

    S = x XOR H XOR Z
    K = majority(x, H, Z)

When `H XOR Z = 1`:

    S = Q
    K = NOT Q
    S XOR K = 1

The three local differences are collected in each orientation:

    D_plus  = S_plus XOR K_plus
    D_minus = S_minus XOR K_minus

The proposed readout is:

    CIT_WORD = D_plus AND D_minus
    CIT = AND_reduce(CIT_WORD)

The source proposal predicts `D_plus = D_minus = 111` and `CIT = 1` after
matched-buffer warm-up in either single-high operational mode. It also
predicts that `H = Z = 1` resets both ring states to `000` in one clock.

## Competing explanations

### Relational-carrier hypothesis

The dual orientation, matched buffering, and final comparison generate a
pair-specific invariant that cannot be reproduced by either ring or any one
local full adder alone. The readout should retain or convey information about
the particular pairing or its history, and it should be causally load-bearing
for both rings.

### Local-complementarity null

In each single-high mode, `S XOR K = 1` follows independently at every local
full adder. Consequently one local adder already generates the invariant bit,
one ring already generates `111`, and the final dual-ring `AND` compares two
constants. Ring orientation, partner identity, pair history, and ring state
are therefore unnecessary for the `CIT = 1` result.

## Registered audit ladder

The confirmatory run performs:

1. digest verification and separate execution of the preserved source
   self-test;
2. exhaustive evaluation of all 64 ordered ring-state pairs in both
   single-high operational modes;
3. single-adder and single-ring reduction;
4. partner substitution;
5. orientation exchange and reversal;
6. history-order comparison;
7. every one-bit state intervention on either ring;
8. matched- and mismatched-epoch buffer diagnostics;
9. comparison of `CIT` feedback with the equivalent constant control;
10. exhaustive double-high reset verification; and
11. classification by the frozen decision rule in `PREREGISTRATION.md`.

## Claim boundary

Reproduction of `111`, opposite ring motion, and common reset verifies the
finite Boolean implementation only. A Class 0 result would not show that the
architecture is useless for control design. It would show only that the
registered `CIT` readout is insufficient evidence for a relational carrier.

No result from this experiment establishes a historical reconstruction of
the CDC 6600, a physical implementation, subjectivity, intersection
subjectivity, or ontological irreducibility.

## Registered command

From the repository root, after the registration commit is public:

    python3 experiments/002a_cdc6600_dual_ring_invariant_audit/run.py \
      --mode confirmatory \
      --out-dir experiments/002a_cdc6600_dual_ring_invariant_audit/results \
      --check
