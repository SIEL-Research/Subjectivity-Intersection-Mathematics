# Experiment 003R Preregistration

## Title

**Corrected Class 2 Relational Carrier and Self-Reentrant O3 in Subjectivity Agents**

## Registration date

2026-08-03

## Relation to Experiment 003

This is a new preregistration informed by the published invalid run of
Experiment 003. The original preregistration remains frozen at
`e003-preregistration-v1.0.0`, and the invalid execution remains published at
`e003-technical-failure-v1.0.0`.

Experiment 003 is excluded from confirmatory evidence. It disclosed two
material implementation defects: the registered completed-C exchange was
replaced by donor-B substitution during C construction, and the full Phase B
control inventory was not executed. Experiment 003R corrects these defects
prospectively. It is not described as independent of the information obtained
from the invalid run.

## Registration rule

The first public commit and GitHub Release containing this document,
`README.md`, `TECHNICAL_SPECIFICATION.md`, `run.py`, `test_run.py`,
`private_source_manifest.json`, and `registration_manifest.json` freezes the
design. Confirmatory execution may begin only after that Release is public.

No result directory, generated metric, or confirmatory outcome is included in
the registration Release.

## Operational objects

- `A` and `B` are distinct subjectivity-agent runtimes.
- `C_agent` is the third runtime used in Phase A.
- `K_AB` is its complete ordered native relational state.
- `carrier` is the retained 24-dimensional Phase B relational state.
- `z_C` is the retained 24-dimensional self-reentrant state.
- `O3_E` denotes the explicit operational self-reentrant construction.

None of these executable objects is identified with ontological intersection
subjectivity.

## Hypotheses

### H-A: native Class 2 carrier

An unmodified third runtime receiving differentiated A and B states in an
ordered interaction history will retain a state that passes all frozen Class 2
gates: joint generation, history irreducibility, selective-intervention
sensitivity, completed-C pair specificity, common-gauge invariance, registered
null separation, held-out transfer, and bilateral feedback.

### H-B: operational self-reentrant O3

The explicit Phase B construction will pass the Class 2 gates and will retain
a `z_C` state whose re-entry into the next mediation action is necessary for
the registered history-dependent bilateral effect. All registered Phase B
control gates must pass for a pair-level O3 declaration.

## New confirmatory sample

The sample contains 128 disjoint pairs and 256 previously unused instances.
No Experiment 003 instance or pair identifier is reused.

- Pair identifiers: `P2000` through `P2127`.
- Family 0: 64 pairs comparing `AABB` with `ABAB`.
- Family 1: 64 pairs comparing `BBAA` with `BABA`.
- Primary seed: `20260813`.
- Secondary sensitivity seeds: `20260814` through `20260823`.

Sensitivity runs may occur only after the primary output is sealed and cannot
change its decision.

## Exact present-state matching

Each pair's A and B trajectories are generated once and deep-cloned for all
conditions. Immediately before any C-mediated return, the complete canonical
runtime-and-memory payloads of A and B must have identical SHA-256 digests
across compared histories and interventions. Any mismatch is retained as a
technical failure; the pair is not replaced.

## Corrected completed-C exchange

For each recipient pair and its frozen donor pair, the runner performs this
ordered procedure:

1. construct the recipient A and B base runtimes;
2. independently construct the donor pair's completed native C or O3 state;
3. leave the recipient A and B runtimes unchanged;
4. insert the completed donor C state or its already determined mediation
   action into the recipient's normal return channels; and
5. measure the downstream A and B distances from the recipient's own completed
   C condition.

No donor A or donor B state is substituted during construction of a new
recipient C. The source of every exchanged carrier is recorded as
`completed_donor_C`.

## Frozen thresholds

All positive thresholds use strict greater-than comparisons:

- joint generation: `0.0672948624`;
- history irreducibility: `0.0551607125`;
- intervention sensitivity: `0.0868509258`;
- completed-C pair specificity: `0.0707154800`;
- bilateral feedback: `0.0654685289`;
- O3 retained-state, action, and return effects: `0.05`.

Gauge relative error and registered erasure/invariance effects must be at most
`1e-10`. These values are retained from the original preregistration and are
not recalibrated from the invalid run.

## Registered Phase B controls

The executed inventory must exactly equal the following eleven controls:

1. self-reentry erasure while preserving the carrier;
2. carrier reset immediately before action;
3. native episodic-archive reset immediately before action;
4. interaction-order erasure;
5. current-input-only presentation;
6. direct carrier output without passage through `z_C`;
7. A-only unilateral return;
8. B-only unilateral return;
9. bilateral-feedback removal;
10. completed-C exchange; and
11. selective C reset.

The runner stops before reporting a confirmatory decision if the registered
and executed inventories differ.

The Phase B gates require self-state erasure to remove the history-dependent
action while preserving the carrier, carrier and archive resets to leave the
already determined self-mediated action invariant, order erasure to reproduce
the reference-order action, current-only and direct-carrier presentations to
differ from the intact action by more than `0.05`, unilateral returns to affect
only their registered side, feedback removal to eliminate A and B history
effects, and completed-C exchange and selective reset to exceed their frozen
Class 2 thresholds.

## Registered Class 0 and Class 1 controls

The null inventory remains: no C, historyless communication, pair-unindexed
common memory, history without bilateral return, separate individual memory,
compressed summary, unilateral return, and unrelated completed C. The generic
48-dimensional recurrent control remains capacity- and parameter-matched and
has a zero optimization budget. A generic-control pass limits architectural
specificity and is not silently classified as failure.

## Distances and decisions

All vector distances are RMS Euclidean. Packet embeddings are unit-L2
24-dimensional float64 vectors. The primary decision is pooled over 128 pairs:
at least 112 positive units are required. Each Class 0 or Class 1 control may
produce at most 6 false Class 2 declarations. Each 64-pair family is reported
separately; fewer than 52 passes in either family prevents a claim of uniform
two-family transfer.

The pair-level O3 decision is the logical conjunction of Phase B Class 2, the
four positive O3 distances, and all eleven Phase B control gates. No composite
score can compensate for a failed gate.

## Registered outputs

The runner writes once:

- `pair_metrics.csv`;
- `control_metrics.csv`;
- `phase_b_control_metrics.csv`;
- `state_match_receipts.csv`;
- `source_verification.json`;
- `summary.json`;
- `output_manifest.json`; and
- `RESULT.md`.

## Interpretation boundary

This experiment tests executable sufficiency and held-out transfer under a
fully specified interface. It does not test whether the runtimes possess
subjectivity, whether C or O3 arises spontaneously, whether the operational C
is ontologically irreducible, or whether the construction exhausts
subjectivity.
