# Experiment 006R

## Revised Confirmation of Spontaneous Operational O3 Re-entry

Experiment 006R is a result-informed revision of Experiment 006. It tests the
O3 re-entry claim that passed in all 96 Experiment 006 interaction runs while
separating the stronger, architecture-dependent individual-history comparison
that caused the complete Experiment 006 conjunction to fail.

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
  --workers 4 \
  --check
```

Results will be published regardless of whether the complete revised primary
conjunction passes.
