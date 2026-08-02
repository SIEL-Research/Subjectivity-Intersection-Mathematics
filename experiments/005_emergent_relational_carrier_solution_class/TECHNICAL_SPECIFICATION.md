# Experiment 005 Technical Specification

## 1. Scope

Experiment 005 is a confirmatory test of whether a relation-component solution
class emerges during ordinary delayed reciprocal-recall learning. The runner is
self-contained and uses only NumPy and Python standard-library modules.

## 2. State and task dimensions

- recurrent state dimension: 24;
- input dimension: 8;
- receiver count: 2;
- class count per receiver: 3;
- output-logit count: 6;
- sequence length: 8;
- intervention boundary: step 4.

Private trits are encoded as early pulses in separate A and B input channels.
The remaining channels carry fixed time, squared-time, and bias coordinates.
The task readout occurs after both private pulses have disappeared.

## 3. Training

Every architecture uses the same frozen procedure:

- optimizer: RMSProp;
- steps: 4,000;
- batch size: 256;
- learning rate: 0.004;
- gradient-norm ceiling: 5.0;
- RMSProp decay: 0.99;
- no early stopping, restart, curriculum, or seed replacement.

Training-seed index `s` fixes initialization and all minibatches. Confirmatory
indices are `1000..1023`.

## 4. Capacity match

Each architecture has:

- 288 active recurrent weights;
- 96 active input weights;
- 72 active output weights;
- 30 bias terms;
- 486 active parameters in total.

Masks and active-parameter counts are tested before endpoint analysis.

## 5. Held-out evaluation

The pair-profile generator creates 128 profiles. Even-numbered pairs are used
for training and odd-numbered pairs for held-out evaluation. Confirmatory
evaluation uses fixed seeds `51630001` and `51630002` and 4,096 episodes.

The runner evaluates task competence on noisy held-out episodes. Intervention
episodes use the same held-out pair allocation with the private signal channels
returned to their pair-specific baselines after the intervention boundary.

## 6. Directed component

Let `I_A` and `I_B` be disjoint receiver coordinate partitions covering the
24-dimensional state. The extracted component `c` is:

- `c[I_A] = h_AB[I_A] - h_A0[I_A]`;
- `c[I_B] = h_AB[I_B] - h_0B[I_B]`.

The coordinate partitions are architecture-specific but fixed before training.

## 7. Matched-null rank

For each episode and receiver partition, a Gaussian random direction is
normalized and rescaled to the corresponding norm of `c`. Deleting this
matched random component yields a null cross-entropy increase. Sixty-four
independent directions form the deletion null.

The registered component and 64 null directions define 65 exchangeable rank
positions. The `percentile >= 0.95` event occupies four positions and therefore
has null probability `4/65`.

Each architecture's exact p-value is the upper binomial tail using its number
of competent seeds and top-0.95 runs. Bonferroni alpha is `0.05/4 = 0.0125`.

## 8. Intervention context

The five operations are deletion, donor exchange, sign flip, donor
composition, and temporal reversal. Each produces a two-receiver,
three-probability response. One redundant coordinate per receiver is removed,
and the five operations are concatenated before linear CKA.

Eight independently generated receiver-matched intervention contexts provide
the CKA null for each architecture comparison.

## 9. Output files

The confirmatory runner writes:

- `rank_metrics.csv`;
- `competent_context_correspondence.csv`;
- `summary.json`;
- `RESULT.md`;
- `output_manifest.json`.

The output directory must not exist before execution. The runner refuses to
overwrite an existing directory.

## 10. Execution modes

`registration-check` uses seed index 900, separate evaluation seeds, 40
training steps, 128 episodes, four deletion controls, and two context controls.
It verifies executable integrity only and has no confirmatory readout.

`confirmatory` fixes all registered dimensions and uses seed indices
`1000..1023`. The runner exposes no command-line option that can alter
confirmatory seeds, sample sizes, learning parameters, or thresholds.

## 11. Registered claim

The primary claim concerns a population-level operational solution class:
repeated emergence of a directionally extracted, bilaterally active,
high-deletion-rank relational component across multiple equal-capacity
interaction topologies. Ontological identification is outside the registered
inference.
