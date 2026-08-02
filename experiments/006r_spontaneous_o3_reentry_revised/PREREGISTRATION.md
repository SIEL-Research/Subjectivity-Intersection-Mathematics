# Experiment 006R Preregistration

## Revised Confirmation of Spontaneous Operational O3 Re-entry

Status: PREREGISTERED RESULT-INFORMED DESIGN — NOT EXECUTED

## 1. Reason for the revision

Experiment 006 preregistered a conjunction of spontaneous O3 re-entry and
universal dominance over a matched individual-history direction. Its primary
readout was `NOT_SUPPORTED`: 13 of 14 checks passed, including all 96
interaction runs passing the all-three-transition transport-rank test, but the
distributed architecture achieved 17 rather than the required 18
individual-history separation passes.

Experiment 006R does not reinterpret Experiment 006 as positive and does not
change its threshold. It registers a narrower primary hypothesis that was
conflated with the stronger implementation-identifiability hypothesis in the
original conjunction. The individual-history comparison remains frozen and is
reported as a secondary implementation-boundary readout.

## 2. Primary hypothesis

Ordinary delayed reciprocal-recall learning, without an explicit C state, O3
state, O3 target, or O3-specific loss, repeatedly generates a directed relation
component whose causal contribution:

1. is transported through unchanged recurrent dynamics into the subsequent
   relation state across three signal-free transitions;
2. is privileged relative to receiver-norm-matched random directions;
3. changes the later action of both receivers when removed; and
4. is pair-specific under transported-state exchange.

This is the operational O3 re-entry claim. It does not require the transported
relation contribution to dominate every equal-norm individual-history
direction in every implementation topology.

## 3. Result-informed development and confirmation firewall

The revision is informed by the public Experiment 006 results and a separate
local scope pilot using training seeds `400..447` and evaluation seeds
`61640001` and `61640002`. The pilot tested the revised primary scope and the
individual-history boundary. These development seeds and all outputs are
excluded from confirmation.

The following allocations are also excluded:

- Experiment 005 confirmation seeds `1000..1023`;
- Experiment 006 confirmation seeds `2000..2023`;
- earlier O3 development seeds `300..311`; and
- registration-check seed `2900`.

The new confirmatory allocation is:

- training seeds `3000..3047`;
- evaluation seeds `61650001` and `61650002`;
- 4,096 held-out evaluation episodes;
- transitions `4->5`, `5->6`, and `6->7`; and
- 64 receiver-norm-matched random directions per transition.

The allocation must not be executed before the preregistration GitHub Release
and Zenodo DOI have both been verified.

## 4. Frozen systems and extraction

The five 486-parameter architectures, task, optimizer, state update, and
directed relation-component extractor are unchanged from Experiment 006:

1. `independent`;
2. `distributed`;
3. `central_shared`;
4. `directional_relay`; and
5. `four_channel_crossbar`.

For receiver A coordinates the component is `h_AB,t-h_A0,t`; for receiver B
coordinates it is `h_AB,t-h_0B,t`. Receiver identity is preserved. All tested
transitions occur after the private signals disappear.

For each transition, `C_t` is removed before one unchanged recurrent update.
The lost part of the re-extracted `C_(t+1)` is the transported contribution.
The runner continues without that contribution and measures later relation and
bilateral-action changes.

## 5. Primary controls

The primary conjunction retains every Experiment 006 control relevant to
operational O3 re-entry:

- 64 receiver-norm-matched random directions;
- an equal-capacity independent architecture;
- exact one-step re-entry reconstruction;
- transported-state erasure;
- cross-pair transported-state exchange;
- final action-loss rank;
- final probability-response rank; and
- bilateral receiver response.

The matched individual-history direction is also computed with the unchanged
Experiment 006 rule, but it is not part of the primary conjunction.

## 6. Seed-level primary decisions

A competent seed has held-out both-correct accuracy of at least `0.95`.

For each competent interaction seed:

- transport recurrence passes when the relation-state loss is at or above the
  0.95 random-direction percentile at all three transitions;
- action loss passes when final cross-entropy increase is at or above the 0.95
  percentile in at least two of three transitions; and
- action magnitude passes when final probability-response magnitude is at or
  above the 0.95 percentile in at least two of three transitions.

## 7. Revised primary conjunction

The primary readout is supported only if all conditions pass:

1. every architecture has exactly 486 active parameters;
2. each interaction architecture is competent in at least 44 of 48 seeds;
3. each interaction architecture has at least 40 of 48 all-three-transition
   transport-recurrence passes;
4. at least 168 of 192 interaction architecture-seed units pass transport
   recurrence;
5. each interaction architecture has at least 36 of 48 action-loss passes;
6. each interaction architecture has at least 36 of 48 action-magnitude
   passes;
7. each interaction architecture has median transported fraction at least
   `0.75`;
8. each interaction architecture has median transport alignment at least
   `0.60`;
9. each interaction architecture has median exchange cross-entropy increase
   at least `0.25`;
10. each interaction architecture has median bilateral erasure response at
    least `0.95`;
11. the independent architecture has maximum held-out both-correct accuracy at
    most `0.20` and maximum extracted-component norm at most `1e-10`; and
12. maximum one-step re-entry reconstruction error is at most `1e-12`.

No composite score can compensate for a failed primary gate. No confirmatory
seed may be replaced. Thresholds cannot be changed after execution.

## 8. Secondary implementation-boundary readout

For every architecture, the runner reports the number of competent seeds in
which the relation contribution exceeds the receiver-norm-matched individual-
history contribution in at least two of three transitions.

The preregistered secondary pattern is:

- at least 40 of 48 passes in each of `central_shared`, `directional_relay`,
  and `four_channel_crossbar`;
- fewer than 40 of 48 passes in `distributed`; and
- the distributed count is at least six below the minimum of the other three
  interaction architectures.

This secondary readout cannot change the primary O3 decision. It tests the
result-informed hypothesis that distributed implementations mix relation and
individual history more strongly than the three more structurally partitioned
implementations.

## 9. Interpretation

A supported primary result establishes that spontaneous operational O3
re-entry transfers to a new 48-seed allocation across multiple equal-capacity
interaction architectures. It demonstrates that a learned directed relation
component can causally participate in its own later relational continuation
and in bilateral action without an explicitly installed O3 variable or
objective.

A supported secondary result identifies an implementation boundary: O3
re-entry may be stable even where the transported relation component is not
universally identifiable as dominant over a matched individual-history
direction.

Neither result identifies the component with ontological subjectivity,
demonstrates consciousness, or proves a unique physical mechanism.

## 10. Publication order

1. freeze this result-informed plan, code, tests, upstream hashes, seeds,
   thresholds, and output schema in a GitHub Release;
2. verify the preregistration Zenodo DOI;
3. execute the confirmatory command once from the registered commit; and
4. publish all outputs and both decisions regardless of outcome.
