# Experiment 006A Public Result Report

## Emergent Nonseparable Relational C

Status: CONFIRMATORY COMPLETE

Primary readout: SUPPORTED

## 1. Principal result

Experiment 006A supported all ten preregistered primary conditions on the new
48-seed confirmatory allocation. Ordinary delayed reciprocal-recall learning
amplified a distributed second-order interaction term

`C_t = H_t(ab) - H_t(a0) - H_t(0b) + H_t(00)`

in four interacting recurrent architectures. The term was extracted only
after training. Training contained no C state, third agent, carrier register,
pair identifier, carrier target, carrier-specific loss, or carrier-specific
regularizer.

The decisive control was an equal-capacity disconnected dual relay. It solved
the same reciprocal-recall task in all 48 seeds, with the same 486 active
parameters and training budget, but its maximum extracted C norm was only
`2.9323e-17`. Thus task success or two competent directed memories alone did
not produce the nonseparable term measured in the interacting systems.

## 2. What “one C” means here

The result supports operational unity as one nonseparable joint interaction
term. C was not defined as “A's memory of B plus B's memory of A.” It was the
single inclusion-exclusion residue left only when the two inputs and their
joint interaction were varied together under input-matched counterfactuals.
An additive pair of disconnected directed traces has C equal to zero by
construction, yet it remained fully task competent in the confirmation.

In the interacting systems, the same joint term had bilateral receiver
support in every evaluated episode at the architecture-level median, was
partly transported into the next joint term by the unchanged recurrent
dynamics, and changed both receivers' later output probabilities when
removed. Cross-pair substitution also had a positive median cost in every
interacting architecture.

This establishes a learned, distributed, causally active, nonseparable
relational component. It does not establish that C is a localized object,
ontological subject, consciousness, or a unique physical mechanism.

## 3. Preregistration and execution

The confirmatory allocation was not executed until both of the following had
been published and verified:

- GitHub Release:
  [e006a-preregistration-v1.0.0](https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics/releases/tag/e006a-preregistration-v1.0.0)
- Zenodo DOI:
  [10.5281/zenodo.21785602](https://doi.org/10.5281/zenodo.21785602)

The registered Release fixes commit
`2553f7eea7fb1b5818571c8c90b58809a3db1fe1`. All registered source hashes
matched before execution. The confirmatory command was executed once:

```bash
python3 -B experiments/006a_emergent_nonseparable_relational_c/run.py \
  --mode confirmatory \
  --out-dir experiments/006a_emergent_nonseparable_relational_c/results \
  --workers 4 \
  --check
```

The run used training seeds `8000..8047`, evaluation seeds `61790001` and
`61790002`, 4,096 held-out episodes, 4,000 updates, 32 receiver-wise
norm-matched random directions, and the signal-free transitions 4->5, 5->6,
and 6->7. Disclosed exploratory and development seeds were excluded.

## 4. Architecture-level results

| Architecture | Competent seeds | Median C norm | Median amplification | Median transported fraction | Median bilateral output | Median exchange CE increase |
|---|---:|---:|---:|---:|---:|---:|
| Distributed | 48/48 | 0.155501 | 1118.87x | 0.524305 | 1.000000 | 0.000343646 |
| Central shared | 48/48 | 0.130294 | 649.44x | 0.548736 | 0.998413 | 0.000125408 |
| Directional relay | 48/48 | 0.093625 | 812.26x | 0.491643 | 0.995972 | 0.000005228 |
| Four-channel crossbar | 48/48 | 0.101860 | 854.19x | 0.486321 | 0.997925 | 0.000046905 |
| Dual independent relay | 48/48 | 2.2441e-17 | 0.000022x | 0.000024 | 0.000000 | 0.000000 |

The minimum held-out both-correct accuracy across all architecture-seed units
was `0.97509765625`. The median bilateral C-support was `1.0` in every
interacting architecture and `0.0` in the disconnected dual relay.

## 5. Frozen primary decision

All ten noncompensating checks passed:

1. all five architectures had exactly 486 active parameters;
2. every architecture had at least 44/48 competent seeds;
3. the dual relay's maximum C norm was at most `1e-10`;
4. every interacting architecture had median C norm at least `0.02`;
5. every interacting architecture had median bilateral C-support at least
   `0.99`;
6. every interacting architecture passed the frozen training-amplification
   gate;
7. every interacting architecture had median transported fraction at least
   `0.40`;
8. every interacting architecture had median bilateral output response at
   least `0.95`;
9. every interacting architecture had positive median cross-pair exchange
   cross-entropy increase; and
10. the maximum one-step reconstruction error was
    `5.689893001203927e-16`, below `1e-12`.

No confirmatory seed was replaced and no registered threshold was changed.
The output contains 720 transition rows: 48 seeds x 5 architectures x 3
transitions. No NaN or Infinity was detected, and every published output hash
matched the generated manifest.

## 6. Secondary random-direction boundary

Receiver-wise norm-matched random-direction percentiles were reported in full
but were not part of the primary conjunction. Their architecture medians were
not uniformly high. This means Experiment 006A does not claim that removing C
always causes more generic damage than an arbitrary equal-norm off-manifold
direction. Its supported claim is the narrower nonseparability result:
interacting systems learned a joint inclusion-exclusion term that was absent
from a competent additive two-relay solution and that causally continued into
later joint state and bilateral action.

Experiments 005 and 006R retain their separately preregistered random-direction
claims for the full directed carrier.

## 7. Interpretation boundary

Experiment 006A supplies evidence for a single operational relational C in the
specific sense of a nonseparable joint interaction contribution distributed
across A and B. It rules out the explanation that the measured C is merely the
sum of two separately competent directed traces under this model class and
task.

It does not prove ontological unity, a third subject, consciousness, or that
every relational system must realize the same mechanism. Those remain
separate theoretical and empirical questions.
