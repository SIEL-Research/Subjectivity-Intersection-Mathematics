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

## Confirmatory result

The revised primary conjunction was supported: all 13 primary checks passed,
and 190 of 192 interaction architecture-seed units passed the all-three-
transition transport criterion. The separately registered implementation-
boundary prediction was also supported. The distributed architecture had 29
of 48 relation-over-individual-history passes, compared with 41, 46, and 47 in
the three more structurally partitioned architectures.

- [Public result report](PUBLIC_RESULT_REPORT.md)
- [Complete machine-readable outputs](results/)
- [Preregistration DOI](https://doi.org/10.5281/zenodo.21764531)
