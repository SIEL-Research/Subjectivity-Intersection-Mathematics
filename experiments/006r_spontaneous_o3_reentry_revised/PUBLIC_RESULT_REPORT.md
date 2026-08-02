# Experiment 006R Public Result Report

## Revised Confirmation of Spontaneous Operational O3 Re-entry

Status: CONFIRMATORY COMPLETE

Primary readout: SUPPORTED

Secondary implementation-boundary readout: SUPPORTED

## 1. Principal result

Experiment 006R confirmed spontaneous operational O3 re-entry on a new
48-seed allocation. All 13 conditions in the revised primary conjunction
passed. Ordinary delayed reciprocal-recall learning generated a directed
relation component whose causal contribution was transported through unchanged
recurrent dynamics into subsequent relation states and bilateral action,
without an explicit C state, O3 state, O3 target, or O3-specific loss.

The all-three-transition transport criterion passed in 190 of 192 interaction
architecture-seed units, exceeding the preregistered floor of 168. The effect
reproduced in four equal-capacity interaction architectures and was absent in
the independent control.

The separately preregistered implementation-boundary prediction also passed.
The relation contribution exceeded the matched individual-history contribution
in at least two of three transitions for 46 of 48 central-shared seeds, 47 of
48 directional-relay seeds, 41 of 48 crossbar seeds, but only 29 of 48
distributed seeds. Thus O3 re-entry remained stable in the distributed system
while its relation contribution was less cleanly separable from individual
history.

## 2. Relation to Experiment 006

Experiment 006 remains `NOT_SUPPORTED`. It combined spontaneous O3 re-entry
with universal relation-over-individual-history dominance in one primary
conjunction. Its transport criterion passed in all 96 interaction runs, but
the distributed architecture missed the individual-history floor by one seed.

Experiment 006R was explicitly registered as a result-informed revision. It
did not lower the failed Experiment 006 threshold or reinterpret the original
decision. Instead, it separated two empirically distinct claims:

1. whether a learned relation contribution re-enters later relation and action
   dynamics; and
2. whether that contribution is universally identifiable as dominant over a
   matched individual-history direction in every topology.

The first became the revised primary conjunction. The second remained frozen
as a noncompensating secondary architecture-boundary prediction. Both were
tested on previously unused data.

## 3. Preregistration and execution

The confirmatory allocation was not executed until both of the following had
been published and verified:

- GitHub Release:
  [e006r-preregistration-v1.0.0](https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics/releases/tag/e006r-preregistration-v1.0.0)
- Zenodo DOI:
  [10.5281/zenodo.21764531](https://doi.org/10.5281/zenodo.21764531)

The preregistration Release fixes commit
`e73374cf9e754c0c744f737d3624c84129581b3c`. All 12 registered source hashes
matched before execution.

The confirmatory command was executed once:

```bash
python3 run.py \
  --mode confirmatory \
  --out-dir results \
  --workers 4 \
  --check
```

The run used training seeds `3000..3047`, evaluation seeds `61650001` and
`61650002`, 4,096 held-out episodes, 64 receiver-norm-matched random directions
per transition, and three signal-free transitions. Local development seeds and
all Experiment 005 and Experiment 006 confirmatory seeds were excluded.

## 4. Architecture-level results

| Architecture | Competent seeds | Transport at all 3 transitions | Action effect at 2 of 3 | Relation over own history at 2 of 3 |
|---|---:|---:|---:|---:|
| Distributed | 48 | 47 | 45 | 29 |
| Central shared | 48 | 48 | 48 | 46 |
| Directional relay | 48 | 48 | 46 | 47 |
| Four-channel crossbar | 47 | 47 | 44 | 41 |

Every architecture exceeded the registered competence, transport, action-loss,
and action-magnitude floors. The pooled transport result was 190 of 192.

The independent control had maximum held-out both-correct accuracy 0.1208 and
zero extracted relation-component norm, satisfying both null conditions.

## 5. Transport and causal continuation

The median fraction of the next relation state attributable to the transported
contribution was:

- distributed: 0.7941;
- central shared: 0.9336;
- directional relay: 0.9207; and
- four-channel crossbar: 0.9419.

Median transport alignments were 0.6487, 0.9039, 0.9209, and 0.9253
respectively. All exceeded the registered primary thresholds.

Erasing the transported contribution changed both receivers with median
bilateral fraction 1.0 in every interaction architecture. Exchanging the
transported contribution across held-out pairs increased cross-entropy with
architecture medians between 2.2789 and 5.8468, exceeding the registered 0.25
floor.

The exact one-step reconstruction check also passed. This verifies that the
measured transported contribution connects deletion of `C_t` before the
unchanged recurrent update to the missing part of `C_(t+1)`, rather than being
inferred only from final behaviour.

## 6. Complete decisions

All 13 revised primary checks passed:

1. exact equal capacity;
2. competence in at least 44 of 48 seeds per interaction architecture;
3. all-three-transition transport in at least 40 of 48 seeds per architecture;
4. pooled transport in at least 168 of 192 units;
5. action-loss rank in at least 36 of 48 seeds per architecture;
6. action-magnitude rank in at least 36 of 48 seeds per architecture;
7. median transported fraction;
8. median transport alignment;
9. median exchanged-state loss;
10. median bilateral erasure response;
11. independent-control accuracy;
12. independent-control relation-component norm; and
13. exact re-entry reconstruction.

All three secondary boundary checks also passed:

1. each structurally partitioned architecture had at least 40 of 48
   relation-over-individual-history passes;
2. the distributed architecture had fewer than 40 of 48; and
3. the distributed count was at least six below the minimum of the other three.

No confirmatory seed was replaced and no registered threshold was changed.

## 7. Meaning of the result

The supported primary result provides a reproducible computational
operationalization of O3 re-entry. A relation-generated component can
participate causally in producing its later relational continuation and in
changing both participating receivers, even when no named third-state register
or O3 objective is installed in advance.

The supported secondary result shows that recurrence and identifiability are
not the same property. A relation contribution may reliably re-enter the
dynamics while remaining mixed with individual-history representation in a
distributed implementation. More structurally partitioned implementations
made the two contributions easier to distinguish.

Within Subjectivity-Intersection Mathematics, this supplies a formal and
executable bridge between a learned relational carrier and self-reentrant O3
closure. It also specifies an experimentally observed architecture boundary
that a general account of relation carriers must accommodate.

The experiment does not identify the learned component with ontological
subjectivity, establish consciousness, or prove a unique physical realization.
Those claims require separate arguments and external-domain tests.
