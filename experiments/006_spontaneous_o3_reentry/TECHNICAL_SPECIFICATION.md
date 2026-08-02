# Experiment 006 Technical Specification

## Scope

Experiment 006 tests spontaneous operational O3 re-entry in the ordinary
recurrent systems confirmed in Experiment 005. It uses the unchanged
delayed-reciprocal-recall task, equal-capacity architecture definitions, and
training procedure from the hash-frozen Experiment 005 sources.

## Frozen execution

- training seeds: `2000..2023`;
- training steps: 4,000;
- batch size: 256;
- learning rate: 0.004;
- held-out episodes: 4,096;
- random directions: 64 per architecture-seed-transition;
- transitions: `4->5`, `5->6`, `6->7`;
- task-competence threshold: 0.95.

The runner exposes no option for changing these confirmatory values.

## State update

For hidden state `h_t` and matched signal-free input `x_t`, the unchanged
recurrent update is:

`h_(t+1) = tanh(W_in x_t + W_rec h_t + b)`.

Let `C_t` be the directed receiver-preserving relation component. The
counterfactual state after removing `C_t` is:

`h_(t+1)^(-C) = tanh(W_in x_t + W_rec (h_t-C_t) + b)`.

The transported contribution is the difference between the natural next
relation component and the relation component reconstructed with
`h_(t+1)^(-C)`.

## Random rank

Each random direction preserves `||C_t||` separately in the two receiver
partitions. Sixty-four random directions and the registered direction define
65 rank positions. A percentile of at least 0.95 occupies the upper four rank
positions.

## Output files

The runner writes:

- `transition_metrics.csv`;
- `summary.json`;
- `RESULT.md`;
- `output_manifest.json`.

The output directory must not exist before execution.

## Registration check

Registration-check mode uses training seed 1900, evaluation seeds 61620001 and
61620002, 40 training steps, 128 episodes, and four random controls. It has no
confirmatory readout.
