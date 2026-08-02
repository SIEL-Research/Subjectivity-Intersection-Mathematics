# Experiment 005 Public Result Report

## Emergent Relational-Carrier Solution Class in Equal-Capacity Recurrent Systems

Status: CONFIRMATORY COMPLETE
Primary readout: SUPPORTED

## 1. Principal result

Experiment 005 found that ordinary delayed reciprocal-recall learning can
repeatedly generate a receiver-specific relational component without an
explicit carrier state, carrier label, carrier target, or carrier-specific
loss. The complete preregistered conjunction passed.

The result reproduced across all four equal-capacity interaction topologies.
The extracted component ranked above at least 95% of receiver-norm-matched
random deletion directions in 84 of 96 interacting architecture-seed runs.
Its intervention effect was bilateral, and the intervention-response geometry
was shared across otherwise different recurrent topologies.

This establishes an operational emergent relational-carrier solution class
under the registered construction. The result is stronger than showing that a
single designed architecture can implement a carrier: multiple ordinary
recurrent interaction architectures converged on components with the same
registered causal and cross-architecture properties.

## 2. Preregistration and execution

The confirmatory allocation was not executed until both of the following had
been published and verified:

- GitHub Release:
  [e005-preregistration-v1.0.0](https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics/releases/tag/e005-preregistration-v1.0.0)
- Zenodo DOI:
  [10.5281/zenodo.21763898](https://doi.org/10.5281/zenodo.21763898)

The preregistration Release fixes commit
`bc00ae41c27615b01147aaf9dae01b65bd7c70d4`. The registered source-hash check
passed for all 11 frozen source files immediately before confirmatory
execution.

The confirmatory command was executed once:

```bash
python3 run.py \
  --mode confirmatory \
  --out-dir results \
  --workers 1 \
  --check
```

The run used the preregistered 24 training seeds, two held-out evaluation
seeds, 4,096 evaluation episodes, 64 receiver-matched deletion controls per
interacting architecture-seed run, and eight matched intervention-context
controls.

## 3. Architecture-level results

All interacting architectures were task competent in all 24 fixed runs.

| Architecture | Competent runs | Top-0.95 runs | Positive selectivity | Exact one-sided p | Median minimum bilateral response |
|---|---:|---:|---:|---:|---:|
| Distributed | 24 | 23 | 23 | 3.193e-27 | 0.9998 |
| Central shared | 24 | 22 | 22 | 5.616e-25 | 0.9976 |
| Directional relay | 24 | 18 | 18 | 1.504e-17 | 0.9989 |
| Four-channel crossbar | 24 | 21 | 21 | 6.301e-23 | 0.9995 |

Every architecture exceeded the registered 14-of-24 top-rank floor and the
Bonferroni-adjusted alpha of 0.0125. The pooled result was 84 top-0.95 runs out
of 96, exceeding the registered floor of 60.

## 4. Bilateral and cross-architecture structure

For every interaction architecture, all 24 competent runs exceeded the
registered 0.90 minimum-bilateral-response threshold. The registered median
threshold of 0.95 also passed for every architecture.

The new four-channel crossbar was compared with each of the other interaction
architectures through mapping-free linear CKA of the complete five-operation
response field.

| Crossbar comparison | Median relation-context CKA | Median specificity over matched random contexts |
|---|---:|---:|
| Distributed | 0.5683 | 0.4989 |
| Central shared | 0.6197 | 0.5774 |
| Directional relay | 0.6613 | 0.6087 |

All three comparisons exceeded the registered CKA floor of 0.35 and
specificity floor of 0.15. Thus the architectures did not merely perform the
same task: their extracted relation components produced measurably
corresponding intervention geometries.

## 5. Controls and complete decision

All 11 preregistered acceptance checks passed:

1. all five architectures had exactly 486 active parameters;
2. all four interaction architectures exceeded the competence floor;
3. all four interaction architectures passed the top-rank criterion;
4. the pooled top-rank criterion passed;
5. all four interaction architectures passed the positive-selectivity floor;
6. every interaction architecture passed the median bilateral-action floor;
7. every interaction architecture passed the per-run bilateral-action floor;
8. the independent control remained below the registered accuracy ceiling;
9. the independent extracted-component norm remained zero;
10. all three crossbar comparisons passed the CKA floor; and
11. all three crossbar comparisons passed the matched-context specificity
    floor.

Separately, all 11 frozen source hashes matched the preregistration manifest
before execution.

The complete machine-readable decision, all 120 architecture-seed rows, all
144 competent cross-architecture comparisons, and their SHA-256 receipt are
published in the `results/` directory.

## 6. Meaning of the result

The positive result identifies a reproducible architecture-level regularity:
when independently informed recurrent parts must later recover one another's
temporally absent information, ordinary task learning repeatedly forms a
directed internal component that is causally privileged relative to
equal-strength random directions, acts on both receivers, and has comparable
intervention geometry across different interaction topologies.

Within Subjectivity-Intersection Mathematics, this supplies a concrete bridge
from an operational relation carrier to a broader solution class. The carrier
need not be installed as a named third object in advance; under the tested
conditions, carrier-like structure can emerge as a recurrent solution to the
interaction problem.

The experiment does not identify the extracted component with subjectivity or
consciousness, and it does not establish a unique implementation of relational
state. Those are separate ontological and comparative questions. The present
finding is the narrower but positive computational result stated above.
