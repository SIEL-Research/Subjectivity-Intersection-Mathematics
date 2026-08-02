# Experiment 006 Public Result Report

## Spontaneous Operational O3 Re-entry after Ordinary Relational Learning

Status: CONFIRMATORY COMPLETE

Primary readout: NOT SUPPORTED

## 1. Principal result

Experiment 006 found strong and fully replicated evidence that the directed
relation component identified after ordinary reciprocal learning is
transported into subsequent relation states and bilateral action without an
explicit O3 state, O3 target, or O3-specific loss. All 96 interacting
architecture-seed runs placed the transported relation contribution above at
least 95% of 64 receiver-norm-matched random directions at all three registered
signal-free transitions.

The complete preregistered conjunction nevertheless did not pass. One of the
14 registered acceptance checks required the transported relation contribution
to exceed a matched individual-history contribution in at least two of three
transitions for at least 18 of 24 seeds in every interaction architecture. The
distributed architecture passed in 17 of 24 seeds. The other three
architectures passed this check in 21, 23, and 23 seeds respectively.

The registered primary readout is therefore `NOT_SUPPORTED`. The result
supports spontaneous operational O3 re-entry relative to matched random,
erasure, exchange, bilateral-action, independent-system, and reconstruction
controls, but it does not support universal separation of the relation
contribution from matched individual history across every tested
implementation topology.

## 2. Preregistration and execution

The confirmatory allocation was not executed until both of the following had
been published and verified:

- GitHub Release:
  [e006-preregistration-v1.0.0](https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics/releases/tag/e006-preregistration-v1.0.0)
- Zenodo DOI:
  [10.5281/zenodo.21764327](https://doi.org/10.5281/zenodo.21764327)

The preregistration Release fixes commit
`d6b43fc9849190d328ba66fb2d5ee1d99f22ad4c`. The registered source-hash check
passed immediately before confirmatory execution.

The confirmatory command was executed once:

```bash
python3 run.py \
  --mode confirmatory \
  --out-dir results \
  --workers 1 \
  --check
```

The run used the registered 24 training seeds, two held-out evaluation seeds,
4,096 evaluation episodes, 64 receiver-norm-matched random directions for each
transition, and three successive signal-free transitions per
architecture-seed run. The 12 local development seeds and all Experiment 005
confirmatory seeds were excluded.

## 3. Architecture-level results

All four interaction architectures were task competent in all 24 runs. The
independent control remained at chance-level performance and had zero extracted
relation component.

| Architecture | Competent seeds | Transport top-0.95 at all 3 transitions | Action effect at 2 of 3 | Relation over own history at 2 of 3 |
|---|---:|---:|---:|---:|
| Distributed | 24 | 24 | 24 | 17 |
| Central shared | 24 | 24 | 23 | 21 |
| Directional relay | 24 | 24 | 24 | 23 |
| Four-channel crossbar | 24 | 24 | 22 | 23 |

The pooled transport result was 96 of 96 seeds, exceeding the registered floor
of 75. The own-history separation check failed only for the distributed
architecture and missed its registered floor by one seed.

## 4. Transport, intervention, and exchange

The relation contribution was reconstructed as the portion of the next
relation state lost when the current directed relation component was removed
before one unchanged recurrent update. Reconstruction error remained below
`2.71e-16`, substantially below the registered `1e-12` ceiling.

Median transported fractions of the next relation state were:

- distributed: 0.7884;
- central shared: 0.9263;
- directional relay: 0.9177; and
- four-channel crossbar: 0.9234.

Median directional alignments with the next relation state were 0.6553,
0.9030, 0.9398, and 0.9260 respectively. All exceeded their registered floors.

Erasing the transported contribution changed both receivers in every
architecture at or above the registered median bilateral threshold. Exchanging
the transported contribution with one from a different pair also increased
held-out cross-entropy above the registered median threshold in every
architecture.

## 5. Registered decision

Thirteen of the 14 registered acceptance checks passed:

1. equal active capacity: passed;
2. task competence: passed;
3. all-three-transition transport rank: passed;
4. pooled transport rank: passed;
5. action-loss rank: passed;
6. action-magnitude rank: passed;
7. relation contribution over matched individual history: **failed**;
8. transported fraction: passed;
9. transport alignment: passed;
10. exchanged-state loss: passed;
11. bilateral erasure response: passed;
12. independent-control accuracy: passed;
13. independent-control relation component: passed; and
14. exact re-entry reconstruction: passed.

Because the preregistration defined the primary decision as the logical
conjunction of all checks, the primary result is `NOT_SUPPORTED`. No threshold
was changed and no confirmatory seed was rerun.

## 6. Meaning of the result

The positive operational finding is that ordinary relation learning produced
a directed component that was repeatedly carried through unchanged recurrent
dynamics into later relation states and bilateral behaviour across four
equal-capacity architectures. This supplies a computationally explicit form of
O3-like self-re-entry that does not depend on installing a named third-state
register or training objective in advance.

The failed gate identifies an implementation boundary. In the distributed
architecture, the transported relation contribution was not reliably dominant
over an equal-norm individual-history contribution at the registered seed
frequency. This is consistent with relation and individual history being more
strongly mixed in a distributed representation. The other three architectures
showed clearer separation.

Accordingly, the experiment distinguishes two claims that should be tested
separately in subsequent work: spontaneous O3 re-entry, and universal
identifiability of the re-entering relation component relative to individual
history. Experiment 006 strongly supports the first under its registered
controls but does not support the second across all tested architectures.

The result does not identify the learned component with ontological
subjectivity or establish a unique physical realization of O3. Those remain
separate interpretive and comparative questions.
