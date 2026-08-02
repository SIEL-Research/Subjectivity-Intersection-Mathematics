# Experiment 005 Preregistration

## Emergent Relational-Carrier Solution Class in Equal-Capacity Recurrent Systems

Status: PREREGISTERED DESIGN — NOT EXECUTED

## 1. Research question

When recurrent systems learn an ordinary reciprocal coordination task without
an explicit relational-carrier state, label, loss, or auxiliary objective, do
multiple interaction architectures repeatedly develop an internally generated
relation component whose causal effect is unusually strong relative to
receiver-matched random directions?

Experiment 005 is a confirmatory computational experiment. It tests whether a
relational-carrier-like solution class emerges under generic task learning. It
does not install the proposed carrier in the learning objective.

## 2. Development provenance and data firewall

The design was developed through local exploratory and calibration runs. Those
runs used training-seed indices `0..7`, `100..111`, and `200..223`. They fixed
the task, capacity, architectures, extractor, matched random null, sample size,
and population-level decision rules used here.

All development seeds, generated episodes, outputs, and threshold-selection
work are excluded from confirmation.

The confirmatory allocation is:

- training-seed indices: `1000..1023`;
- held-out evaluation seeds: `51630001` and `51630002`;
- 4,096 evaluation episodes;
- 64 deletion-rank controls per interacting architecture-seed run;
- 8 full intervention-context controls per interacting architecture-seed run.

The confirmatory allocation must not be executed before the preregistration
GitHub Release and Zenodo DOI have both been verified.

## 3. Task

The frozen task is delayed reciprocal recall.

- A privately receives one of three temporally encoded values.
- B privately receives one of three temporally encoded values.
- The private signals disappear before the readout period.
- Receiver A must report B's value.
- Receiver B must report A's value.

Both outputs must be correct for an episode to count as task-correct. A model is
task competent when held-out both-correct accuracy is at least `0.95`.

## 4. Equal-capacity architectures

Five recurrent architectures are trained independently. Each has exactly 486
active parameters.

1. `independent`: two recurrent partitions without cross-partition paths;
2. `distributed`: recurrent cross-partition communication distributed across
   the state;
3. `central_shared`: local receiver states coupled through a shared recurrent
   region;
4. `directional_relay`: separate directional relay regions;
5. `four_channel_crossbar`: separate local and A-to-B/B-to-A channels.

The independent architecture is the carrier-absent control. The other four are
the interacting architectures.

No architecture receives a variable named or supervised as C. There is no
carrier loss, carrier target, communication loss, curriculum, restart
selection, or post-training seed replacement.

## 5. Frozen relation-component extractor

At the intervention boundary, the runner computes four prefix states:

- `h_AB`: both inputs present;
- `h_A0`: A present and B removed;
- `h_0B`: B present and A removed;
- `h_00`: both removed.

For the state coordinates read by receiver A, the directed component is
`h_AB - h_A0`, isolating B-to-A influence. For the coordinates read by receiver
B, it is `h_AB - h_0B`, isolating A-to-B influence. These two directed parts are
combined without merging the receiver identities.

The extractor is applied only after ordinary task learning and does not affect
training.

## 6. Causal interventions

Five frozen operations are applied to the extracted component:

- deletion;
- exchange with a fixed-point-free donor from another held-out pair;
- sign reversal;
- composition with a donor component;
- replacement by the component extracted after temporal reversal.

The runner records probability-response fields for both receivers. The minimum
bilateral-response proportion is the minimum, across the five operations, of
the proportion of episodes in which both receivers change.

## 7. Receiver-matched random null

For each interacting architecture-seed run, 64 random deletion directions are
generated. In every episode, the random direction preserves the extracted
component's norm separately in the receiver-A and receiver-B coordinate
partitions. Thus the null matches intervention strength on both sides while
randomizing direction.

The empirical deletion percentile is the fraction of random directions whose
cross-entropy increase is smaller than that produced by deleting the extracted
relation component, with half weight assigned to ties.

A run is `top-0.95` when this percentile is at least `0.95`. With 64 random
directions and one registered direction, the exchangeable rank-null
probability is `4/65`.

## 8. Cross-architecture comparison

For every competent seed, the full five-operation probability-response field
is represented in four nonredundant receiver coordinates per operation.
Mapping-free linear CKA compares this intervention context across
architectures. Eight receiver-matched random intervention contexts provide the
comparison null.

The preregistered cross-architecture tests concern the three comparisons
between the crossbar and the other interacting architectures.

## 9. Confirmatory hypotheses

### H1. Emergent high-rank relation component

At least three of the four interacting architectures will produce at least 14
top-0.95 runs among the 24 fixed seeds, and every counted architecture will
pass the exact one-sided rank-null test at Bonferroni alpha `0.0125`.

### H2. Pooled recurrence across architectures

At least 60 of the 96 interacting architecture-seed runs will be top-0.95.

### H3. Directional rather than arbitrary causal effect

At least three interacting architectures will have positive
delete-versus-random-median selectivity in at least 14 competent runs.

### H4. Bilateral action

Every interacting architecture will have median minimum-bilateral response at
least `0.95`, and at least 22 of 24 runs in every architecture will have
minimum-bilateral response at least `0.90`.

### H5. Cross-architecture intervention geometry

For each crossbar comparison, median relation-context CKA will be at least
`0.35`, and median relation-minus-random specificity will be at least `0.15`.

## 10. Complete decision rule

The complete registered conjunction requires all of the following:

1. every architecture has exactly 486 active parameters;
2. every interacting architecture is task competent in at least 22 of 24
   seeds;
3. H1 passes;
4. H2 passes;
5. H3 passes;
6. H4 passes;
7. every independent run has extracted-component norm below `1e-10`, and the
   maximum independent held-out both-correct accuracy is at most `0.20`;
8. H5 passes.

No composite score may compensate for a failed gate. Every fixed seed remains
in the competence denominator. Carrier metrics are interpreted only for models
meeting the frozen task-competence threshold, and all incompetent runs remain
reported.

## 11. Falsification conditions

The registered claim is not supported if any gate in the complete conjunction
fails. In particular, the experiment fails if the effect is confined to fewer
than three interaction architectures, if the pooled effect floor is missed, if
the independent architecture produces the same extracted component, or if the
bilateral and cross-architecture conditions fail.

## 12. Interpretation boundary

A successful result would show that ordinary reciprocal task learning can
repeatedly produce a receiver-specific relational component with unusual
causal rank and a shared intervention geometry across multiple recurrent
communication topologies. This would establish an operational emergent
relational-carrier solution class under the registered construction.

It would not show that every trained model must develop this component. It
would not identify the component with subjectivity, consciousness, or the
ontological whole of Intersection Subjectivity. It would not establish that
the tested extractor is the unique representation of relational state.

## 13. Publication order

1. freeze this plan, the technical specification, public source, tests,
   confirmatory seeds, thresholds, and source hashes in a GitHub Release;
2. obtain and verify the preregistration Zenodo DOI;
3. execute the confirmatory command once from the registered commit;
4. publish all outputs and the complete decision, regardless of outcome.
