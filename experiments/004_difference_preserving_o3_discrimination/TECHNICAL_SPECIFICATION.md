# Experiment 004 Technical Specification

## 1. Scope

Experiment 004 is a confirmatory computational construction and architecture
discrimination study. It tests whether differentiated A/B input and retained
difference history can be transported through a recurrent relational carrier,
a recurrent self-state, and a bilateral return path.

The public runner imports the same hash-frozen private subjectivity-agent
runtime used by E003R. No private source code is copied into this repository.

## 2. Data firewall

Development and confirmation use disjoint allocations:

| Allocation | Descriptor indices | Matrix seeds |
|---|---:|---:|
| Development | 0–127 | 20261001–20261012 |
| Confirmation | 128–255 | 20261101–20261112 |

The confirmatory runner terminates before endpoint analysis unless all 128 A
states, B states, A/B pairs, and four-encounter interaction-packet sequences
are content-unique.

## 3. Common and difference modes

At encounter `t`, the two input vectors are decomposed as:

`common_t = (A_t + B_t) / 2`

`difference_t = (A_t - B_t) / 2`

The intervention reconstructs the two routes using a frozen orientation
coefficient `lambda_t`:

`A'_t = common_t + lambda_t difference_t`

`B'_t = common_t - lambda_t difference_t`

Changing `lambda_t` from `+1` to `-1` reverses the A/B difference orientation
while preserving the common mode exactly.

## 4. Architectures

### 4.1 Candidate O3

The candidate uses distinct A and B matrix routes and a multiplicative joint
term. Its carrier and self-state are recurrent, and the action is read from the
self-state.

### 4.2 Symmetric recurrent control

The symmetric control receives only the normalized sum of A and B before
joint generation. All downstream recurrence and action dimensions are
retained. It is exactly invariant under a pure reversal of A/B difference.

### 4.3 Role-aware memoryless control

The memoryless control retains distinct A and B routes at the current
encounter but resets carrier and self-state recurrence at every encounter. It
tests current route asymmetry without retained relational history.

### 4.4 Role-aware recurrent control

The role-aware recurrent control retains distinct A and B routes and both
recurrent states but omits the candidate multiplicative joint term. It tests
whether the registered effects have multiple realizations within a broader
difference-preserving recurrent class.

## 5. Temporal interventions

| Condition | Difference orientations |
|---|---|
| Baseline | `+ + + +` |
| All flip | `- - - -` |
| Early only | `- + + +` |
| Prior only | `- - - +` |
| Last only | `+ + + -` |

The early-only and prior-only conditions end with the same current input as
baseline. A final-action difference therefore requires retained history.

## 6. O3 path intervention

The runner records the all-flip effect at carrier, self-state, and action.
It then replaces the final self-state with a zero vector before the fixed
action readout. The already formed carrier is not recomputed. This isolates
the registered carrier-to-self-to-action path.

## 7. Same-family C exchange

Each 64-pair history family uses a cyclic donor offset of one. Recipient A and
B current states are held fixed while the completed candidate C state is
replaced by the donor C state. Both A-return and B-return distances must pass
the frozen threshold. No exchange changes history family.

## 8. Inference unit

The pair is the primary unit. The twelve matrix seeds are within-pair
robustness repetitions. A pair passes an endpoint with at least 10 passing
seeds. A primary hypothesis requires at least 112 passing pairs and at least
52 passing pairs in each history family.

## 9. Registered interpretation

A successful conjunction demonstrates an executable difference-preserving,
history-retaining relational architecture with an operational O3 path and
same-family pair sensitivity. The architecture-class control determines
whether this behavior is specific to the candidate equation or admits
multiple realization.

The operational states are not identified directly with ontological
subjectivity.
