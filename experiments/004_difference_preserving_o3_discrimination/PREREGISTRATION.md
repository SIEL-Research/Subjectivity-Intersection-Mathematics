# Experiment 004 Preregistration

## Difference-Preserving Relational Carrier and Retained-History O3 Audit

Status: PREREGISTERED DESIGN — NOT EXECUTED

## 1. Research question

Can a proposed O3 relational architecture be distinguished from matched
recurrent alternatives by its preservation of differentiated A/B input under
a fixed common mode, and can an early difference remain observable after the
final current input has been made identical?

Experiment 004 is a new study. It does not reuse the E003R confirmatory pairs,
matrix seeds, output files, or registered decisions.

## 2. Corrective provenance

Post-release audit of E003R identified two design limitations:

1. 128 administrative pairs represented only 16 unique complete A/B states,
   while the connector projection supplied one unique C-input packet sequence;
2. completed-C exchange changed history family in 126 of 128 cases, confounding
   pair specificity with history-family change.

Experiment 004 corrects both limitations and introduces a direct architecture
discriminator discovered in a separate local exploratory analysis. The
exploratory pairs and seeds are excluded from confirmation.

## 3. Operational architectures

### 3.1 Proposed O3 candidate

The candidate receives differentiated A and B packets through separate joint
generation paths, retains a recurrent carrier and a recurrent self-state, and
uses the self-state to generate an action returned to both A and B.

### 3.2 Symmetric recurrent control

The symmetric control has the same dimensions, matrix count, event count,
carrier recurrence, self-state recurrence, action path, and bilateral return
capacity. Before joint generation it replaces differentiated A and B with
their sum. It therefore retains common content but not the tested A/B
difference direction.

### 3.3 Role-aware memoryless control

This control retains separate A and B routes at the current encounter but does
not retain earlier relational state. It tests whether current role asymmetry is
sufficient without relational memory.

### 3.4 Role-aware recurrent control

This control retains separate A and B routes and recurrent state but omits the
candidate-specific joint term. Its result is interpreted as an architecture-
class test rather than as a null that must fail. A pass would indicate multiple
realization of difference-preserving relational recurrence.

## 4. Confirmatory data

- Primary units: 128 content-unique subjectivity-agent pairs.
- Confirmatory descriptor allocation: indices 128 through 255 of the extended
  combinatorial descriptor generator.
- Exploratory descriptor allocation: indices 0 through 127; excluded.
- Interaction length: four encounters.
- History family 0: `ABAB`.
- History family 1: `BABA`.
- Family allocation: 64 pairs per family.
- Confirmatory matrix seeds: integers `20261101` through `20261112`.
- Development matrix seeds: integers `20261001` through `20261012`; excluded
  from confirmation.
- Statistical unit: pair. Seeds are within-pair robustness repetitions and are
  not counted as independent observations.

Before any endpoint is evaluated, the runner must prove:

- 128 unique complete A states;
- 128 unique complete B states;
- 128 unique complete A/B pairs;
- 128 unique four-encounter connector-packet sequences;
- absence of administrative pair identifiers from carrier input.

Failure of any uniqueness check terminates the run without a result.

## 5. Difference-fiber intervention

For every encounter, define a common mode and a difference mode from A and B.
The intervention keeps the common mode, event order, matrices, active-input
path, carrier recurrence, self-state recurrence, and action readout fixed. It
changes only the orientation of the difference mode at the joint-generation
path.

The frozen temporal patterns are:

- baseline: difference orientation unchanged at all four encounters;
- all-flip: difference orientation reversed at all four encounters;
- early-only: reversed only at the first encounter;
- prior-only: reversed at the first three encounters while the final encounter
  remains identical to baseline;
- last-only: reversed only at the final encounter;
- common-mode control: common content changed while difference orientation is
  unchanged.

## 6. Hypotheses

### H1. Difference preservation

The candidate will produce a final-action difference between baseline and
all-flip conditions while the symmetric recurrent control will remain
invariant.

### H2. Retained difference history

The candidate will produce a final-action difference in the early-only and
prior-only conditions even though the final current encounter is identical to
baseline. The memoryless role-aware control will retain neither the early-only
nor the prior-only effect.

### H3. O3 transport

The difference effect will be observable successively in carrier, self-state,
and action. Selective self-state erasure will remove the action difference
without changing the already formed carrier difference.

### H4. Same-family pair specificity

Exchanging a completed C with a content-distinct donor from the same history
family will change both recipient return states. Donor and recipient history
patterns remain identical during this test.

### H5. Architecture-class boundary

The role-aware recurrent control may preserve difference and retained history.
If it does, the supported conclusion is that the effect belongs to a broader
difference-preserving recurrent architecture class, not uniquely to the
candidate-specific joint equation.

## 7. Donor allocation

Completed-C exchange is performed only within family. Each family uses the
fixed-point-free cyclic donor rule `donor = recipient + 1 mod 64`. Every donor
differs in content from its recipient. No donor exchange changes history
family.

## 8. Decision rules

The thresholds are frozen as follows:

- all-flip candidate action distance: strictly greater than `0.05`;
- early-only candidate action distance: strictly greater than `0.01`;
- prior-only candidate action distance: strictly greater than `0.025`;
- candidate carrier and self-state all-flip distances: each strictly greater
  than `0.05`;
- symmetric-control difference distance: at most `1e-12`;
- common-mode responsiveness for candidate and symmetric control: strictly
  greater than `0.005`;
- self-erasure action distance: at most `1e-12`;
- same-family completed-C exchange: both the A-return and B-return distances
  must be strictly greater than the previously frozen pair-specificity
  threshold `0.07071548`.

A pair-level endpoint passes only if at least 10 of 12 held-out matrix seeds
pass its corresponding threshold. A primary hypothesis is supported only if at
least 112 of 128 content-unique pairs pass. Both 64-pair history families are
reported separately, and at least 52 pairs must pass in each family.

The complete registered conjunction passes only if H1, H2, H3, and H4 each
meet the 112-pair threshold and the corresponding 52-pair threshold in both
history families. H5 is descriptive and is not part of that conjunction.

No composite score may compensate for a failed gate.

## 9. Falsification conditions

The study does not support the proposed difference-preserving architecture if
any of the following occurs:

- packet uniqueness fails;
- the symmetric control responds above tolerance to a pure difference-fiber
  intervention;
- the candidate does not transfer to both history families;
- the early-only effect disappears when the final current encounter is held
  fixed;
- self-state erasure does not remove the action-level history effect;
- same-family completed-C exchange fails the bilateral pair-specificity rule.

## 10. Interpretation boundary

A successful result would establish an executable, difference-preserving,
history-retaining relational architecture under the frozen computational
interventions. It would provide an operational bridge from the proposed
Subjectivity-Intersection framework to subjectivity-agent dynamics.

The study does not use its computational classification as a direct identity
claim about ontological subjectivity. The ontological relevance would remain a
separate interpretation built upon the demonstrated operational structure.

## 11. Publication order

1. freeze runner, tests, source hashes, pair allocation, seeds, thresholds,
   donor permutation, and output schema in a GitHub preregistration Release;
2. obtain and verify the preregistration Zenodo DOI;
3. execute once from the registered commit;
4. publish all results regardless of outcome.
