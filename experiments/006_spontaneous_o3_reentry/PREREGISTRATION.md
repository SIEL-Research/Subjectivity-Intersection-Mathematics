# Experiment 006 Preregistration

## Spontaneous Operational O3 Re-entry after Ordinary Relational Learning

Status: PREREGISTERED DESIGN — NOT EXECUTED

## 1. Research question

Experiment 005 found that ordinary reciprocal-recall learning can generate a
directed relational-carrier solution class without an explicit carrier state,
target, or loss. Experiment 006 asks the next question: does the learned
relation component causally re-enter the dynamics and generate the subsequent
relation state and bilateral action without an explicit O3 state, O3 target,
or O3-specific objective?

The registered operational sequence is:

`C_t -> C_(t+1) -> bilateral action`.

The experiment distinguishes this claim from the weaker observation that a
recurrent system contains history or that deleting an arbitrary hidden-state
direction changes its output.

## 2. Development provenance and confirmation firewall

The method was developed locally with training-seed indices `300..311`. The
development runs fixed the task, temporal transitions, extractor,
receiver-matched random null, individual-history control, sample size, and
decision rules.

All development outputs and threshold-selection work are excluded from
confirmation. Public Experiment 005 confirmatory seeds `1000..1023` are also
excluded.

The new confirmatory allocation is:

- training-seed indices: `2000..2023`;
- held-out evaluation seeds: `61630001` and `61630002`;
- 4,096 evaluation episodes;
- three signal-free transitions: `4->5`, `5->6`, and `6->7`;
- 64 receiver-norm-matched random directions per transition.

The confirmatory allocation must not be executed before the preregistration
GitHub Release and Zenodo DOI have both been verified.

## 3. Frozen learned systems

The task and five equal-capacity recurrent architectures are inherited from
Experiment 005. Each architecture has exactly 486 active parameters.

1. `independent`;
2. `distributed`;
3. `central_shared`;
4. `directional_relay`;
5. `four_channel_crossbar`.

The systems learn delayed reciprocal recall. A receives one temporally encoded
value, B receives another, both signals disappear, and each receiver must later
report the other receiver's value.

No architecture contains a variable named C or O3. Training includes no
carrier state, O3 state, relation target, self-reentry target, auxiliary loss,
communication loss, curriculum, restart selection, or seed replacement.

## 4. Directed relation component

At each registered time `t`, four state trajectories are evaluated:

- `h_AB,t`: both earlier signals present;
- `h_A0,t`: only A's earlier signal present;
- `h_0B,t`: only B's earlier signal present;
- `h_00,t`: neither earlier signal present.

For coordinates read by receiver A, the directed relation component is
`h_AB,t - h_A0,t`. For coordinates read by receiver B, it is
`h_AB,t - h_0B,t`. The two receiver identities remain separate.

All three registered transitions occur after the external private signals have
disappeared. Their external inputs are therefore matched; only retained state
can transport the earlier interaction.

## 5. Operational O3 re-entry intervention

For each transition `t->t+1`, the runner:

1. extracts `C_t` from the natural trajectories;
2. records `C_t` before intervention;
3. removes `C_t` from the current joint state;
4. applies one unchanged recurrent update;
5. re-extracts the resulting relation component at `t+1`;
6. defines the lost part of `C_(t+1)` as the transported contribution of
   `C_t`;
7. continues from the state in which this transported contribution is absent;
8. measures the subsequent effect on both receivers.

The state reconstructed by subtracting the transported contribution at
`t+1` must agree numerically with the state obtained by deleting `C_t` before
the recurrent update. This stage receipt tests the complete causal path rather
than inferring self-reentry from final output alone.

## 6. Controls

### 6.1 Receiver-matched random directions

For each transition, 64 random hidden-state directions preserve the norm of
`C_t` separately in receiver A's and receiver B's coordinate partitions. The
registered `C_t` deletion is ranked against these controls for:

- loss of the subsequent relation component;
- final cross-entropy increase; and
- final probability-response magnitude.

A percentile of at least `0.95` is the registered top-rank event.

### 6.2 Matched individual-history direction

An individual-history direction is constructed from `h_A0,t-h_00,t` in A's
receiver partition and `h_0B,t-h_00,t` in B's receiver partition. It is
rescaled to the same per-receiver norm as `C_t`.

This control asks whether the directed relation component is specifically
important for producing the next relation state, rather than merely being one
history-bearing direction among many.

### 6.3 Independent architecture

The independent architecture has no cross-partition path. Its extracted
relation component must remain zero and its held-out both-correct accuracy
must not exceed `0.20`.

### 6.4 Cross-pair transported-state exchange

After the transported contribution has formed at `t+1`, it is exchanged with
one from a fixed-point-free donor belonging to another held-out pair. The
median final cross-entropy increase must be positive and exceed the registered
floor.

## 7. Seed-level decisions

A competent seed has held-out both-correct accuracy of at least `0.95`.

For each interacting architecture, a seed passes:

- **transport recurrence** when relation-state loss is top-0.95 at all three
  transitions;
- **action loss** when final loss increase is top-0.95 at least twice in three
  transitions;
- **action magnitude** when final probability response is top-0.95 at least
  twice in three transitions;
- **relation-over-individual specificity** when relation-state loss exceeds
  the matched individual-history loss at least twice in three transitions.

## 8. Complete registered conjunction

The primary readout is supported only if every condition below passes:

1. all architectures have exactly 486 active parameters;
2. every interacting architecture is competent in at least 22 of 24 seeds;
3. every interacting architecture has at least 18 transport-recurrence seed
   passes;
4. at least 75 of 96 interacting architecture-seed units pass transport
   recurrence;
5. every interacting architecture has at least 18 action-loss seed passes;
6. every interacting architecture has at least 18 action-magnitude seed
   passes;
7. every interacting architecture has at least 18
   relation-over-individual-specificity seed passes;
8. every interacting architecture has median transported fraction of the next
   relation state at least `0.75`;
9. every interacting architecture has median alignment between the transported
   contribution and the next relation state at least `0.60`;
10. every interacting architecture has median cross-pair exchange
    cross-entropy increase at least `0.25`;
11. every interacting architecture has median bilateral erasure response at
    least `0.95`;
12. the independent architecture has maximum accuracy at most `0.20` and
    extracted-component norm at most `1e-10`;
13. maximum re-entry reconstruction error is at most `1e-12`.

No composite score can compensate for a failed gate. Fixed seeds cannot be
replaced. Thresholds and controls cannot be changed after execution.

## 9. Interpretation

A supported result establishes an operational spontaneous O3 re-entry solution
class under the registered construction. It means that ordinary learning has
generated a directed relation component whose own causal contribution is
transported into later relation states and bilateral action without an
explicitly installed O3 state or objective.

The claim does not require the emergent implementation to contain a separately
named or spatially localized `z_C`; the tested object may be distributed across
the recurrent state. The experiment does not identify the learned state with
ontological subjectivity, demonstrate consciousness, or establish a unique
physical realization.

## 10. Publication order

1. freeze this plan, source, tests, upstream source hashes, seeds, thresholds,
   and output schema in a GitHub Release;
2. obtain and verify the preregistration Zenodo DOI;
3. execute the confirmatory command once from the registered commit;
4. publish all outputs and the complete decision regardless of outcome.
