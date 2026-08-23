# Experiment E015R Preregistration v1.0.0

## Title

Prospective Replication of Endogenous Standpoint Constitution and Relational-C
Re-entry

## Registration state

- Experiment ID: `E015R`
- Evidence status before execution: **Operational hypothesis**
- Scientific layers: operationalization, hypothesis, experimental prediction,
  method, and registered decision
- Public repository:
  `SIEL-Research/Subjectivity-Intersection-Mathematics`
- Preregistration tag: `e015r-preregistration-v1.0.0`
- Result tag reserved in advance: `e015r-results-v1.0.0`
- Confirmatory state: **not executed**
- Outcome access for E015R seeds `98100..98147`: **none**
- Execution gate: **blocked until the public preregistration DOI is issued,
  reopened, and checksum-verified**

## Research question

Can two structurally identical interacting units, without supplied self/other
labels, actor identities, source labels, fixed port names, or stable event
positions, use their own action-consequence histories to constitute operational
standpoint roles that subsequently organize a learned predictive system into a
nonadditive relational component with bilateral causal effects and later
relational re-entry?

## Scientific motivation

Three observations must hold together for the registered claim.

1. The system must infer which consequences belong to its own causal history
   rather than relying on a fixed participant label or array position.
2. A predictor trained only for ordinary next-consequence prediction must form
   a joint component that is absent from an equally dimensional additive
   control.
3. That joint component must be causally load-bearing for both viewpoints and
   must affect the corresponding joint component one transition later.

Success on only one or two parts is insufficient. Role classification without
joint organization, nonzero interaction without a competent additive control,
or an extracted component without intervention effects does not satisfy the
hypothesis.

## Prior evidence and replication status

V73 previously supported fixed-index-independent causal self/other attribution.
E006A previously supported a learned nonadditive four-history component against
a competent additive control with fixed A/B identities. E006R previously
supported later relational re-entry with fixed A/B identities. E015 joined
those elements in one synthetic system and supplied the exact mechanism,
thresholds, and decision rule used here.

The E015 outcome is known. E015R is therefore an exact, result-informed,
out-of-sample replication rather than a discovery experiment. No E015R
confirmatory seed may be used to tune the model, redefine an endpoint, choose a
comparator, or change a threshold.

## North-star hypothesis

### H1 — constituted-standpoint relational re-entry

Local causal history supplies operational viewpoint coordinates. In those
coordinates, a connected predictor trained only on the ordinary prediction
task develops a nonadditive four-history component `C` that is absent from a
competent additive predictor, contributes to the future outputs of both local
viewpoints, and is carried into the next-step `C` under the unchanged update.

### Registered competing hypotheses

- `H0a — fixed identity or position`: apparent role attribution depends on
  actor index, source label, event position, channel name, or port name.
- `H0b — generic task capacity`: the connected learner does not outperform an
  equal-dimensional competent additive learner on held-out prediction.
- `H0c — extractor artifact`: the four-history inclusion-exclusion expression
  produces a comparable component in the additive control.
- `H0d — epiphenomenal component`: `C` is nonzero but deleting it does not
  affect both viewpoints or the next-step relational component.
- `H0e — role-state bypass`: downstream organization is unaffected when the
  inferred standpoint state is exchanged without its matching history and
  viewpoint configuration.
- `H0f — leakage`: role performance can be obtained from fixed position or
  observation-only features that exclude the observer's motor history.

## Discriminating prediction

If H1 is supported, all nine A-class primary gates and all seven B-class
validity gates will pass jointly on the fresh 48-seed sample. If validity holds
but any A-class gate fails, the operational conjunction does not replicate.
No favorable endpoint compensates for another endpoint's failure.

## Operational definitions

### Actor and viewpoint

An actor is one of two structurally identical action-generating units. A
viewpoint is the observer-local representation constructed from that actor's
own motor-command history and an unordered pair of consequences. Simulator
source identities are retained only for scoring and are excluded from learner
inputs and prediction targets.

### Constituted standpoint role

At every step, an observer compares its recent motor commands with the two
unlabelled observed consequences. It selects one of eight candidate causal
maps, `sign in {-1,+1}` and `delay in {1,2,3,4}`, by minimum mean squared error
over a trailing eight-step window. The event closest to the selected
action-derived prediction is assigned the observer-local role `self`; the
other event is assigned `other`. Ties are resolved by the frozen candidate and
event ordering in the runner.

`role_accuracy` is the fraction of assignments matching simulator provenance
from step 24 onward. `post_swap_accuracy` is measured after the eight-step
readaptation interval ending at step 56 in port-swap episodes.

### Connected and additive predictors

Both predictors have 48 hidden dimensions and receive the same nine-dimensional
viewpoint vector. The connected predictor permits every hidden dimension to
use every input. The additive predictor divides its hidden dimensions into two
24-dimensional blocks: one block receives the self/history/role coordinates
and the other receives only the attributed-other stream. The additive control
therefore has the same hidden dimension and prediction task but prohibits A/B
mixing within the frozen representation.

### Relational component C

After prediction training is complete, four hidden-state trajectories are
computed under the same frozen learner:

- `H(ab)`: full viewpoint input;
- `H(a0)`: attributed-other coordinate zeroed;
- `H(0b)`: all self/history/role coordinates zeroed;
- `H(00)`: all inputs zeroed.

The registered component is

`C_t = H_t(ab) - H_t(a0) - H_t(0b) + H_t(00)`.

`C` is not a training target, label, named hidden register, loss term,
regularizer, selection signal, or third agent. “Nonadditive” in E015R means
nonzero under this registered four-history contrast relative to the registered
additive control; it is not an unrestricted claim over all possible nonlinear
representations.

### Bilateral causal contribution

At step 64, `C_t` is subtracted from the full connected hidden state. The
unchanged learner then generates a 12-step future output. For each two-viewpoint
episode, the smaller of the two normalized output changes is retained. A
positive bilateral minimum therefore requires a nonzero effect for both local
viewpoints rather than a large effect on only one.

### Later-C transport

The C-deleted state is advanced once using the unchanged recurrent update. The
missing portion of the next-step four-history component is measured relative
to the baseline next-step `C`. The transport fraction is its norm divided by
the baseline next-step `C` norm.

### Exchange tests

- `C exchange`: the recipient's `C_t` is replaced with a norm-matched `C_t`
  from the same observer position in another held-out episode. The normalized
  future-output difference is the exchange effect.
- `state-only viewpoint exchange`: a donor hidden state is combined with the
  recipient viewpoint history. A positive impairment indicates that the
  stored state is not sufficient independently of its constituting viewpoint.
- `coherent viewpoint-bundle exchange`: the donor hidden state is combined
  with the matching donor input history and compared with the donor baseline.
  Equivalence within the registered margin tests restoration under a coherent
  exchange.

## Frozen generative system

- Two actors independently choose actions from `{-1,0,+1}`.
- Each episode contains 96 steps.
- Each actor receives a distinct map from the eight sign-delay candidates.
- At each step, the actor-specific base consequence is its delayed action
  multiplied by the assigned sign.
- Reciprocal interaction multiplies that base by
  `1 + 0.80*tanh(previous consequence of the other actor)`.
- Independent uniform noise in `[-0.045,0.045]` is added.
- The two consequences are randomly permuted at every step before observation.
- In half of the episodes, the two causal maps exchange at step 48.
- Evaluation begins at step 24; post-swap scoring begins at step 56.

## Frozen learner and input

The nine input coordinates are:

1. attributed-self consequence;
2. attributed-other consequence;
3. current motor command;
4. motor command lag 1;
5. motor command lag 2;
6. motor command lag 3;
7. inferred causal sign;
8. normalized inferred delay;
9. expected next self consequence under the inferred map.

The target is the next attributed-self consequence. Both models use:

- 48 hidden dimensions;
- leaky hidden update with retained-state coefficient `0.35`;
- 500 Adam representation-training steps;
- learning rate `0.008`;
- minibatch size `min(384, available rows)`;
- input-weight initialization standard deviation `0.22`;
- prediction-readout initialization standard deviation `0.08`;
- parameter penalty `1e-5` during representation learning; and
- ridge readout penalty `0.001`, with unpenalized intercept.

The simulator and learner are frozen in `e015_x3_frozen_base.py`, whose SHA-256
is `9c56bc3a6293e40345ed35aa1d97815228e405eda5106ae9d521a5d2684b43f1`.

## Sampling and seed separation

- Specification/debug outer seeds: `98000..98007`.
- Confirmatory outer seeds: `98100..98147` (48).
- Sign-flip randomization seeds: advantage `981501`, shuffle `981502`, and
  C exchange `981503`.
- Every outer seed generates 20 training episodes and 12 separate held-out
  evaluation episodes.
- Port-swap status alternates by episode index.
- All V73, E015-X1–X7, original E015, and E015R debug seeds are excluded.
- All 48 confirmatory seeds are executed once in ascending order.
- No early efficacy stop and no seed replacement are permitted.

The inference unit is the outer training seed. Episode and viewpoint values are
aggregated inside their originating outer seed before cross-seed inference.

## A-class primary gates

All nine gates must pass.

1. **Role constitution**: mean role accuracy `>=0.75` and at least 44/48
   seed-level accuracies `>=0.70`.
2. **Post-swap tracking**: mean post-swap accuracy `>=0.75` and at least 44/48
   seed-level accuracies `>=0.68`.
3. **Model competence**: mean connected held-out `R2>=0.60`; at least 44/48
   connected values `>=0.50`; at least 44/48 additive values `>=0.30`.
4. **Connected advantage**: mean connected-minus-additive `R2>=0.05`, positive
   in at least 44/48 seeds, with its Holm-corrected sign-flip test passing.
5. **Attributed-other dependence**: mean held-out `R2` drop after cross-episode
   attributed-other-stream replacement `>=0.10`, positive in at least 44/48
   seeds, with its Holm-corrected sign-flip test passing.
6. **Nonadditive C**: median connected `C` RMS `>=0.03` and maximum additive
   `C` RMS across seed-level records `<=1e-10`.
7. **Bilateral causal effect**: median bilateral minimum deletion effect
   `>=0.003` and positive in at least 44/48 seeds.
8. **Later-C transport**: median transport fraction `>=0.40` and at least
   44/48 seed-level fractions `>=0.10`.
9. **Cross-pair C exchange**: median exchange effect `>0` with its
   Holm-corrected sign-flip test passing.

## B-class validity gates

All seven gates must pass before the A-class conjunction is interpreted.

1. **Frozen-source and public-registration integrity**: source identity,
   manifest, seed separation, scientific baseline, DOI-1 receipt, and clean
   pre-output Git state all pass.
2. **Leakage nulls**: mean fixed-position accuracy and mean observation-only
   lookup accuracy are each `<=0.55`. The observation-only lookup uses event
   position, consequence-value bin, and time parity but no motor history.
3. **Permutation invariance**: maximum full-renaming difference and maximum
   event-channel permutation difference are exactly zero across the tested
   features and viewpoint outputs.
4. **State-only exchange impairment**: median normalized impairment `>=0.003`
   and positive in at least 44/48 seeds.
5. **Coherent exchange restoration**: the seed-level coherent-exchange error
   passes two one-sided normal-approximation equivalence tests with margin
   `0.03` and alpha `0.05`.
6. **Exact one-step reconstruction**: maximum re-entry reconstruction error
   `<=1e-12`.
7. **Runtime integrity**: exactly 48 finite seed rows, no seed replacement, no
   overwritten output directory, and complete error/partial-output retention.

## Statistical analysis

- The connected advantage, attributed-other shuffle drop, and C-exchange
  effect each receive a one-sided paired sign-flip randomization test with
  10,000 randomizations.
- The three unadjusted p-values are ordered and tested with Holm family-wise
  alpha `0.05`; the implementation uses strict `p < alpha/(m-rank)`.
- Coherent-exchange equivalence uses two one-sided normal-approximation tests,
  alpha `0.05`, margin `0.03`.
- Means are used only where specified; medians and seed counts are used only
  where specified.
- No alternative estimator, transformation, subgroup, threshold, or seed set
  may replace a registered primary analysis after outcome access.
- Any unregistered analysis is labelled exploratory and cannot change the
  registered decision.

## Decision rule

### Inconclusive result

Classify E015R as **Inconclusive result** if any B-class gate fails or if a
manifest, DOI receipt, source identity, leakage, permutation, pairing,
finite-value, reconstruction, runtime, or retention failure prevents a valid
test.

### Negative result

Classify E015R as **Negative result** if every B-class gate passes but any of
the nine A-class gates fails. Favorable individual endpoints remain reported
but do not compensate.

### SIEL replicated result

Classify E015R as **SIEL replicated result** only if every A-class and B-class
gate passes without material deviation.

## Missing data, failures, deviations, and stopping

- Do not replace a failed or extreme seed.
- Retain the partial raw file after every completed seed.
- Retain execution errors, environment information, timestamps, and deviations.
- An existing `results/` directory prohibits execution and must not be deleted
  to rerun the registered experiment.
- A code defect discovered after confirmatory outcome access closes this
  execution. Any repaired confirmation requires a new identifier or a
  pre-outcome amendment on still-unseen data.
- Maximum planned resources are two hours, 8 GB RAM, and four logical CPU
  cores. Resource exhaustion is retained as a technical failure; it does not
  authorize seed removal or threshold changes.

## Confirmatory, adversarial, and outside boundaries

E015R tests direct out-of-sample replication of the registered E015
conjunction. Large norm-matched random-lesion banks, shifted or spliced
histories, latent twins, proxy-dominant environment changes, alternative
optimizers, and new model topologies are post-replication adversarial studies
and cannot replace this experiment's primary question.

The experiment does not test phenomenal consciousness, qualia, human or
biological selfhood, ontological Intersection Subjectivity, ontological `C` or
O3, QPU/EEG claims, or cross-domain physical identity.

## Reproducibility artifacts

The preregistration Release freezes:

- this preregistration;
- technical specification and source provenance;
- self-contained simulator and decision runner;
- tests, dependency pin, seeds, source hashes, and frozen manifest;
- DOI-1 receipt template; and
- the mandatory DOI-2 result inventory.

The result Release must retain raw and partial seed rows, the machine-readable
decision, report, execution log, source and output manifests, deviations, and
the DOI-1 receipt regardless of outcome.

## DOI-1 gate before execution

Execution is prohibited until the GitHub preregistration Release is public,
the connected Zenodo integration publishes a version DOI, the GitHub Release
and Zenodo record are independently reopened, the archived files and checksums
match the frozen package, and `registration_receipt.json` records a complete
`PASS`. A reserved DOI, Git commit, Git tag, GitHub Release, or email is not
sufficient.

## DOI-2 gate before result communication

After the single execution, every outcome is frozen under
`e015r-results-v1.0.0`. A Zenodo result DOI distinct from DOI-1 must be public,
must cite DOI-1 and the exact repository refs, and must pass file/checksum
verification before the result is emailed, posted, submitted, or inserted into
a public manuscript.

## Exact command order

Before DOI-1, only the validation commands in `README.md` are permitted. After
DOI-1 is verified and the receipt is committed, execute exactly once from the
repository root:

```bash
python3 experiments/015r_endogenous_standpoint_relational_c_replication/run.py \
  --phase confirmatory \
  --manifest experiments/015r_endogenous_standpoint_relational_c_replication/FROZEN_MANIFEST.sha256
```

## Claim boundary

A replicated result can establish only that the registered conjunction of
history-derived role constitution, connected predictive nonadditivity,
bilateral causal contribution, exchange sensitivity, and later relational
re-entry repeats on a fresh seed block in this frozen synthetic system. It
cannot establish unique causal specificity against every matched direction,
representation-independent nonseparability, external biological validity,
phenomenal subjectivity, or an ontological third subject.
