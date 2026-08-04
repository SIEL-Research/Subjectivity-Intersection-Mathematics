# Experiment 006A Preregistration

## Emergent Nonseparable Relational C

Status: PREREGISTERED RESULT-INFORMED DESIGN - NOT EXECUTED

## 1. Primary question

Can ordinary delayed reciprocal-recall learning amplify a distributed
second-order interaction component that cannot be produced by an equally
competent, equal-capacity pair of independent directed relays, and does that
component causally participate in its own later continuation and bilateral
action?

## 2. Component fixed before confirmation

For four input-matched counterfactual trajectories,

`C_t = H_t(ab) - H_t(a0) - H_t(0b) + H_t(00)`.

This inclusion-exclusion term is exactly zero for an additive pair of
independent directed traces. It is extracted only after training. No C state,
third agent, carrier register, carrier label, carrier target, carrier loss,
pair identifier, or carrier regularizer is present in training.

## 3. Result-informed firewall

The design is informed by local exploratory seeds 7000-7007, 7100-7107, and
development seeds 7200-7223. All are permanently excluded. Experiment 005,
006, and 006R confirmation allocations are also not reused.

Confirmation uses:

- training seeds 8000-8047;
- evaluation seeds 61790001 and 61790002;
- 4,096 held-out episodes;
- transitions 4->5, 5->6, and 6->7;
- 4,000 updates, batch size 256, learning rate 0.004; and
- 32 receiver-wise norm-matched random directions, reported as a secondary
  boundary.

No confirmatory allocation may be executed before the preregistration GitHub
Release and Zenodo DOI are verified.

## 4. Systems

Five systems have exactly 486 active parameters:

1. distributed;
2. central_shared;
3. directional_relay;
4. four_channel_crossbar; and
5. dual_independent_relay.

The dual relay has two disconnected 12-dimensional recurrent blocks. One
receives only B and produces only A's answer; the other receives only A and
produces only B's answer. It can solve reciprocal recall but cannot form a
second-order cross-block interaction.

## 5. Interventions

At each signal-free transition, the extracted C is removed from `H_t(ab)` and
the unchanged recurrent update is applied. The next C is re-extracted with all
other counterfactual trajectories unchanged. The lost next component is the
transported contribution. The runner also measures receiver support, bilateral
probability response, cross-pair C exchange, training amplification relative
to initialization, random-direction ranks, and exact one-step reconstruction.

## 6. Frozen primary conjunction

The primary readout is `SUPPORTED` only if all ten checks pass:

1. every architecture has exactly 486 active parameters;
2. every architecture, including dual relay, has at least 44/48 competent
   seeds at held-out both-correct accuracy >= 0.95;
3. dual relay has maximum C norm <= 1e-10;
4. every interacting architecture has median C norm >= 0.02;
5. every interacting architecture has median bilateral C-support >= 0.99;
6. every interacting architecture has median trained/untrained C-norm ratio >=
   100 and at least 44/48 seeds with ratio > 1;
7. every interacting architecture has median transported fraction >= 0.40;
8. every interacting architecture has median bilateral output-response
   fraction >= 0.95;
9. every interacting architecture has positive median cross-pair exchange
   cross-entropy increase; and
10. maximum one-step reconstruction error is <= 1e-12.

No composite score compensates for a failed gate. No seed may be removed or
replaced. Thresholds cannot change after execution.

## 7. Secondary random-direction boundary

Receiver-wise norm-matched random-direction transport and output-response
percentiles are reported in full but cannot change the primary decision.
Arbitrary off-manifold damage magnitude tests a different question from
nonseparability. Experiments 005/006R retain their preregistered
random-direction claims for the full directed carrier.

## 8. Interpretation boundary

A supported result establishes an operational, learned, distributed
second-order interaction component that is absent from a competent additive
two-relay solution and causally continues into later interaction states and
bilateral action. It does not establish ontological unity, consciousness, a
third subject, or a unique physical mechanism.

## 9. Publication order

1. freeze plan, runner, tests, upstream hashes, seeds, thresholds, and schema in
   a GitHub Release;
2. verify the Zenodo preregistration DOI;
3. execute once from the registered commit; and
4. publish every output and the decision regardless of outcome.
