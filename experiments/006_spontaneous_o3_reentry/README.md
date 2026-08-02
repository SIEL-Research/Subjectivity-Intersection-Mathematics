# Experiment 006

## Spontaneous Operational O3 Re-entry after Ordinary Relational Learning

Experiment 006 tests whether a relation component learned without an explicit
O3 state or objective causally generates later relation states and bilateral
action across multiple equal-capacity recurrent interaction architectures.

The confirmatory allocation must not be executed before the preregistration
GitHub Release and Zenodo DOI have both been verified.

## Registration check

```bash
python3 run.py \
  --mode registration-check \
  --out-dir registration_check \
  --workers 1 \
  --check
```

## Confirmatory command

```bash
python3 run.py \
  --mode confirmatory \
  --out-dir results \
  --workers 1 \
  --check
```

Results will be published regardless of whether the complete registered
conjunction passes.
