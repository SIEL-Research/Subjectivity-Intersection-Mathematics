# Experiment 007B: Independent SIO Action Structure

This preregistered experiment constructs the typed SIO-side action structure already implemented by Experiments 006, 006R, and 006A. It does not load or compare D12RG.

## Registration check

From the repository root:

    python3 experiments/007b_independent_sio_action_structure/test_run.py

    python3 experiments/007b_independent_sio_action_structure/run.py \
      --mode registration-check \
      --out-dir /tmp/e007b-registration-check \
      --check

## Confirmatory execution

Run only after the preregistration commit and Release are public:

    python3 experiments/007b_independent_sio_action_structure/run.py \
      --mode confirmatory \
      --out-dir experiments/007b_independent_sio_action_structure/results \
      --check

The computation is deterministic and does not retrain the 006-series models.

## Boundary

The output is an operational mathematical structure extracted from frozen computational experiments. It is not a claim of subjectivity, ontological O3, D12RG agreement, or DJS-hypergroup realization.

## License

Apache-2.0.
