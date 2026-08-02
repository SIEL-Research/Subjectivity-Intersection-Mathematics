# Experiment 003R Technical Specification

## 1. Frozen source boundary

The public runner imports only the V61 runtime and V89f natural-lineage
projection whose private Git commit and file digests are recorded in
`private_source_manifest.json`. Every imported private file must match its
registered SHA-256 digest before output creation.

## 2. Allocation and provenance firewall

Pairs `P2000` through `P2127` are new confirmatory allocations. Administrative
pair tokens are scrubbed before any state enters C. The invalid Experiment 003
pairs `P1000` through `P1127` and its seed are excluded.

## 3. Recipient and donor separation

Each recipient pair has one deterministic donor selected by the frozen rule
`(recipient_index + 65) mod 128`. The donor's history family is computed from
the donor index. Recipient A and B are never replaced.

For `pair_exchange`, the runner first completes the donor C using the donor A,
donor B, and donor history. Phase A then serializes that completed donor C and
returns it through unchanged recipient A and B interfaces. Phase B determines
the completed donor O3 action before returning it through the same unchanged
recipient interfaces. The receipt field `carrier_source` must equal
`completed_donor_C`.

## 4. Stage-level state objects

Phase A records complete `K_AB`. Phase B records:

- `K_AB`: the complete native C runtime vector;
- `carrier`: the retained 24-dimensional relational state;
- `z_C`: the retained 24-dimensional self-reentrant state;
- `action`: the 24-dimensional mediation action;
- downstream complete A state; and
- downstream complete B state.

History, reset, exchange, and control distances are written to
`phase_b_control_metrics.csv`.

## 5. Phase B controls

`phase_b_control_outputs()` constructs an output for every registered control.
It compares its key set with `REGISTERED_PHASE_B_CONTROLS` and terminates on
any missing or unexpected item. `phase_b_control_metrics()` independently
constructs a gate for every registered key and performs the same equality
check.

Self-reentry erasure zeros only `z_C`. Carrier reset zeros only `carrier` after
history completion. Native-archive reset replaces only the native runtime
archive after history completion. Direct-carrier output applies the frozen
action matrix to `carrier` rather than `z_C`. Unilateral controls use the same
completed action and disable exactly one return channel.

## 6. Matched generic recurrent control

The generic control uses the same differentiated inputs, event count, state
dimensions, seven 24-by-24 matrices, action channel, return channels, completed
C exchange, and complete Phase B control inventory. It uses seed `20260913`.
Candidate and control both have zero training, search, seed selection, and
result-dependent reinitialization.

## 7. Numerical and decision rules

All calculations use NumPy float64 in source order. Distances are RMS
Euclidean. State equality uses canonical JSON SHA-256. Positive thresholds,
invariance tolerances, Wilson aggregation, family reporting, and null bounds
are defined in `PREREGISTRATION.md` and duplicated in
`registration_manifest.json`.

## 8. Write-once execution

The runner verifies both public and private manifests before importing the
private runtime. It refuses an existing output directory. The eight registered
outputs are written once, and `output_manifest.json` records SHA-256 digests of
the other seven artifacts.
