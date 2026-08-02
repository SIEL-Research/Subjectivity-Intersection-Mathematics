# Experiment 005

## Emergent Relational-Carrier Solution Class in Equal-Capacity Recurrent Systems

Experiment 005 tests whether ordinary reciprocal coordination learning,
without an explicit carrier state or carrier-specific objective, repeatedly
produces a receiver-specific relational component whose causal deletion rank
is stronger than matched random directions.

The confirmatory allocation must not be executed before the preregistration
GitHub Release and Zenodo DOI have been verified.

## Registered files

- `PREREGISTRATION.md`
- `TECHNICAL_SPECIFICATION.md`
- `run.py`
- `test_run.py`
- `registration_manifest.json`
- `support/`

## Registration check

This uses a separate nonconfirmatory seed namespace:

```bash
python3 run.py \
  --mode registration-check \
  --out-dir registration_check \
  --check
```

## Confirmatory command

Run only from the registered commit after DOI verification:

```bash
python3 run.py \
  --mode confirmatory \
  --out-dir results \
  --workers 1 \
  --check
```

The output directory must not exist before execution. Results will be
published regardless of whether the complete registered conjunction passes.
