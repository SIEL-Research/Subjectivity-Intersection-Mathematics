# Experiment 006R Technical Specification

## Scope

Experiment 006R reuses the hash-frozen Experiment 006 computation and changes
only the result-informed hypothesis structure, new seed allocation, sample
size, scale-adjusted decision floors, registration receipt, and result schema.

## Frozen execution

- training seeds: `3000..3047`;
- evaluation seeds: `61650001`, `61650002`;
- training steps: 4,000;
- batch size: 256;
- learning rate: 0.004;
- held-out episodes: 4,096;
- random directions: 64 per architecture-seed-transition;
- transitions: `4->5`, `5->6`, `6->7`;
- task-competence threshold: 0.95.

The runner exposes no option for changing these confirmatory values.

## Primary and secondary separation

The primary checks are recalculated from the complete Experiment 006 metrics
with the 48-seed floors fixed in the preregistration. The matched individual-
history comparison remains in the CSV and architecture summaries but is moved
to a separately labelled secondary boundary test.

The runner does not edit, filter, or suppress transition rows based on either
decision.

## Output files

The runner writes:

- `transition_metrics.csv` with 720 data rows;
- `summary.json` with primary and secondary decisions;
- `RESULT.md`;
- `output_manifest.json`.

The output directory must not exist before execution.

## Registration check

Registration-check mode uses training seed `2900`, evaluation seeds `61649001`
and `61649002`, 40 training steps, 128 episodes, and four random directions. It
has no primary or secondary confirmatory readout.
