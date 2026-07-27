# Experiment 002A Preregistration

## Title

**CDC 6600 Dual-Ring Invariant Classification Audit**

## Registration date

2026-07-27

## Registration rule

This preregistration is frozen by the first public GitHub commit containing:

- this document;
- `README.md`;
- `run.py`;
- `test_run.py`;
- `registration_manifest.json`; and
- the preserved source and provenance files under
  `third_party/luke_casson_leighton/`.

Confirmatory execution must occur only after that commit has been pushed to
the public repository. The program records the Git commit and remote URL in
the result package and refuses to overwrite an existing confirmatory result
directory.

## Primary question

Does the proposed `CIT = 1` invariant require the paired clockwise and
anticlockwise architecture, or is it fully explained by the local
full-adder identity that holds when `H XOR Z = 1`?

## Registered hypotheses

### H1 — implementation reproduction

The preserved source passes its four self-tests:

- raw `D_plus = D_minus = 111` in both operational modes;
- matched one-clock buffers preserve `111`;
- double-high control resets both rings to `000`; and
- one-hot clockwise and anticlockwise states traverse opposite three-cycles.

### H2R — relational-carrier hypothesis

The registered `CIT` readout is a relational-carrier candidate only if it
cannot be reproduced by a single local unit and if the exhaustive audit
supports all of the following:

- joint generation by both rings;
- dependence on pair history;
- sensitivity to a selective intervention on the candidate relation;
- pair specificity under partner substitution;
- invariance under admissible orientation relabelling;
- separation from the registered local-complementarity null;
- transfer under the frozen rule; and
- causal feedback to both ring states or readouts.

### H2N — local-complementarity null

For every latch bit `Q` and either single-high mode:

    S = Q
    K = NOT Q
    S XOR K = 1

Therefore `D_plus`, `D_minus`, `CIT_WORD`, and `CIT` are fixed without using
the second ring, its orientation, its state, or the pair history. The
double-high `000` state is a common reset induced directly by `H = Z = 1`,
not a selectively disrupted relational state.

## Frozen inputs

- Preserved source:
  `third_party/luke_casson_leighton/cdc6600_dual_ring_cit_demo.py`
- Required source SHA-256:
  `5471c379d9009a7425aca394fa835d827280448a7edd59bbceebfc92de8c9db5`
- All three-bit ring states: integers `0` through `7`
- Operational control modes: `(H,Z) = (1,0)` and `(0,1)`
- Common-reset control: `(H,Z) = (1,1)`
- Registered history length: six clocks
- No random seed and no fitted parameter

## Frozen controls

### C1 — source reproduction

Run the preserved source as a separate process with `--self-test`. A nonzero
exit status fails H1.

### C2 — exhaustive paired-state sweep

Evaluate all `8 x 8 x 2 = 128` paired operational cases. Every raw and
matched-buffer readout must be recorded.

### C3 — local reduction

Evaluate both possible local latch bits under both operational controls, then
all eight states of one ring. If the same invariant bit and word are obtained,
joint generation fails.

### C4 — partner substitution

Hold one ring and its control fixed while replacing the other ring by each of
the eight possible states. If `CIT` never changes, pair specificity fails.

### C5 — orientation intervention

Exchange the two rings and reverse either ring's rotation convention. If the
readout is unchanged, orientation invariance passes but supplies no evidence
of relational generation by itself.

### C6 — history intervention

Compare forward, reverse, and state-shuffled six-clock trajectories. If the
complete `CIT` trace after warm-up is identical, history dependence fails.

### C7 — state intervention

Flip each of the six ring-state bits separately for every paired state and
both operational controls. If the readout is unchanged, the candidate is not
state-sensitive.

### C8 — buffer alignment

Compare matched same-epoch sum/carry buffers with deliberately mismatched
epochs. A failure under mismatching is classified as a measurement-alignment
effect, not as pair-history evidence, because the comparison remains local to
each ring.

### C9 — feedback equivalence

Feed the prior `CIT` value into `H` with `Z = 0` and compare the resulting
trajectory with the constant control `H = 1, Z = 0`. Equality shows that the
feedback carries no state-dependent information beyond a constant one.

### C10 — common reset

Apply `H = Z = 1` to all 64 paired states. Both rings must become `000` in one
clock. This verifies reset behaviour but does not count as selective
relational intervention.

## Frozen classification rule

- **Class 2 — pair-indexed relational carrier:** all seven evidence gates and
  bilateral feedback pass.
- **Class 1 — incomplete shared-history state:** a shared history state is
  detected, but at least one of pair specificity, null separation, or
  bilateral feedback fails.
- **Class 0 — no shared history-bearing carrier:** a local or common-control
  null fully reproduces the readout, and pair/history interventions do not
  alter it.

H1 and the carrier classification are reported separately. Passing the source
self-tests cannot override a Class 0 or Class 1 result.

## Registered acceptance checks

The execution is valid only if:

- the registered files and preserved source match their frozen hashes;
- the preserved source self-test completes successfully;
- all 128 operational paired-state cases are evaluated;
- all registered substitutions and interventions are evaluated;
- all 64 common-reset cases are evaluated;
- the result includes the seven individual evidence-gate decisions and the
  separate bilateral-feedback decision; and
- the classification follows the frozen rule without manual rescue.

## Confirmatory command

    python3 experiments/002a_cdc6600_dual_ring_invariant_audit/run.py \
      --mode confirmatory \
      --out-dir experiments/002a_cdc6600_dual_ring_invariant_audit/results \
      --check

## Interpretation boundary

This finite audit can classify the proposed Boolean readout relative to the
registered Experiment 002 criteria. It cannot establish an external
relational carrier, a physical or neural implementation, subjectivity,
intersection subjectivity, or an ontological conclusion.
