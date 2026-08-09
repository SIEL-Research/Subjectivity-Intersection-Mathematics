# Experiment 009 — Constitutive Cell O3 Closure

## Public question

Experiment 009 tests a change in what is taken to constitute a living cell.
It does not begin with an already constituted cellular object and then attach
an O3 score to known mechanisms.

> A cell does not first exist and then possess a boundary, metabolism, and
> information-repair. A cell exists as one living whole when these
> differentiated perspectives intersect, generate a distributed third
> perspective, and are re-formed by its return into their next states and the
> conditions of their continued intersection.

The experiment tests this constitutive standpoint in frozen reduced stochastic
dynamics anchored to official JCVI-syn3A `Minimal_Cell` source files. No O3,
life, closure, viability, or optimization-objective state is installed.

## Registration state

`PREREGISTERED_NOT_EXECUTED`

This state becomes effective only after all of the following are public and
verified:

1. the registration commit on `main`;
2. tag and GitHub Release `e009-preregistration-v1.0.0`; and
3. the separate preregistration DOI.

The E009 confirmation seeds must not be executed before those objects are
verified. The prior LIFE-004 development and result are fully disclosed in the
preregistration; E009 uses new, disjoint seed ranges.

## Frozen test

The post-simulation analysis asks whether:

- a three-way distributed cross-mode naturally emerges without an O3 variable;
- the cross-relation adds held-out predictive information to the next change of
  every differentiated process;
- moderate damage is repaired and reproduction resumes;
- selective interaction erasure or temporal misalignment destroys closure;
- timely relation restoration rescues recovery without adding an O3 substance;
- severe damage crosses an irreversible boundary; and
- a nonliving matched control does not pass the same closure criteria.

All fourteen preregistered gates must pass for the registered positive decision.
Every negative or mixed output is retained.

## Validation before public registration

Registration validation reads hashes and official source anchors only; it does
not execute the E009 confirmation seeds.

```bash
python3 experiments/009_constitutive_cell_o3_closure/run.py \
  --validate-registration \
  --minimal-cell-root /path/to/Minimal_Cell

python3 -m unittest discover \
  -s experiments/009_constitutive_cell_o3_closure/tests -v
```

The unit tests use only diagnostic seed `42`, never a registered confirmation
seed.

## Single confirmatory execution after registration DOI

```bash
python3 experiments/009_constitutive_cell_o3_closure/run.py \
  --execute \
  --minimal-cell-root /path/to/Minimal_Cell
```

Results are then inspected and published separately as GitHub Release
`e009-results-v1.0.0` with a second, result-specific DOI.

## Source and scope

- upstream: `https://github.com/Luthey-Schulten-Lab/Minimal_Cell`;
- frozen upstream commit: `db048aca5fe85438e0129819bbf0314b037dd931`;
- numerical dependency: `numpy==2.4.4`;
- model class: reduced stochastic dynamics anchored to official JCVI-syn3A
  parameters and source hashes, not the complete hybrid CME–ODE execution.

A positive result is a prospective public confirmation of the constitutive
cell-closure realization in this frozen model. It does not by itself establish
the same O3 in the complete whole-cell implementation or in living cells.
