# Experiment 001 Result — Exact Relational Holonomy

## Status

**EXACT FINITE CALIBRATION PASSED**

The frozen implementation reproduced every acceptance target and passed all
seven registered evidence gates within the constructed finite system.

## Principal result

All six orderings of two `A` events and two `B` events have the same
registered non-relational information:

```text
current A state:        0
current B state:        0
local A history:        AA
local B history:        BB
shared event counts:    A=2, B=2
pre-existing object:    constant
```

Despite this match, the path-ordered carrier takes three distinct values.

```text
AABB, ABBA, BAAB, BBAA  -> identity carrier
ABAB                    -> order-three carrier (0 1 2)
BABA                    -> inverse order-three carrier (0 2 1)
```

For the prespecified comparison:

```text
AABB carrier feedback = (0,2)
ABAB carrier feedback = (1,1)
```

The two histories therefore return the registered individual and environmental
variables to the same endpoint while producing different subsequent joint
readouts.

## Control results

### Joint generation

Two `A` actions alone and two `B` actions alone both return the carrier to the
identity. The nontrivial state requires ordered participation by both actions.

### Relational intervention

Resetting the `ABAB` carrier to identity, or replacing the history by the
endpoint-matched ordering `AABB`, restores the baseline feedback.

### Partner substitution

Replacing the overlapping partner action `B = (1 2)` with the disjoint action
`B* = (2 3)` makes the two participant actions commute:

```text
AB*AB* -> identity carrier
```

The nontrivial feedback consequently disappears.

### Coordinate gauge

The audit tested:

```text
24 simultaneous label permutations
x 6 endpoint-matched histories
= 144 gauge-history cases
```

Every case preserved:

- exact conjugacy of the carrier;
- carrier cycle type;
- feedback after decoding to the original labels.

## Evidence-gate readout

| Gate | Result |
|---|---|
| J — Joint generation | PASS |
| H — History irreducibility | PASS |
| I — Intervention sensitivity | PASS |
| P — Pair specificity | PASS |
| G — Gauge invariance | PASS |
| N — Registered null separation | PASS |
| T — Frozen transfer | PASS |

These results apply to the finite benchmark and to the prespecified null
family. They are not an empirical acceptance of a `C_intersection` candidate.

## Scientific interpretation

The benchmark gives an exact witness of relational holonomy:

> The joint ordering of two individually self-cancelling actions can remain in
> a path-ordered relational carrier, act back on both participant readouts,
> disappear under an appropriate partner substitution, and remain invariant
> under simultaneous coordinate relabeling.

This proves that the seven-gate framework is not internally empty: there is a
finite system in which all gates can be satisfied simultaneously.

It also identifies the minimum information that the registered null family
lacks. Current endpoints, isolated local histories, and order-free common
counts do not contain the cross-participant interleaving.

## Limitation

The carrier is an exact construction from the complete ordered history. A
general model that receives that complete history can reproduce it. The result
therefore establishes discrimination from the registered alternatives, not
the uniqueness of the carrier representation or an absolute impossibility of
reduction.

No inference is made here about human subjectivity, biological realization,
or ontological completeness.

## Next experiment

Experiment 002 should remove the benchmark's privileged access to an exact
carrier. It should generate noisy dyadic trajectories, expose only observable
projections, infer a candidate history state on training pairs, and freeze the
model before testing:

- held-out histories;
- held-out pairs;
- partner substitution;
- carrier disruption;
- coordinate changes;
- matched common-driver, individual-memory, and full-history alternatives.
