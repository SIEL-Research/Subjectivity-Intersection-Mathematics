# Experiment 013 registered interpretation

## Registered decision

`DOMAIN_PRIOR_O3_GENERATION_TRANSFER_NOT_SUPPORTED`

The overall registered claim failed because the fresh molecular realization did
not pass the preregistered absolute low-score gates:

| Molecular condition | Score | Registered requirement | Pass |
|---|---:|---:|---:|
| intact | 1.00000 | at least 0.80 | yes |
| removed | 0.70875 | at most 0.50 | no |
| mismatched return | 0.80625 | at most 0.50 | no |
| correct return | 1.00000 | at least 0.80 | yes |

No threshold, target, radius, seed, mismatch rule, or outcome was changed after
execution.

## What did pass

- The domain-prior residual rule and exact reconstruction passed in all three
  domains.
- The structurally generated mismatches satisfied the registered centered
  overlap bound in all three domains.
- Both fresh atomic realizations passed all five absolute gates.
- All four fresh cellular cohorts passed all five absolute gates.
- The fresh molecular realization satisfied all four strict causal inequalities:
  intact and correct return each exceeded removal and mismatched return.
- The causal partial-order leave-one-domain-out test passed for every held-out
  domain.
- The unrestricted learned-pairwise leave-one-domain-out diagnostic also passed.
- The threshold-free cross-domain separation margin was positive at
  `0.16122249117405762`.

## Evidential meaning

The registered result supports transfer of the weaker ordinal causal topology
on the executed reduced models: generated O3 removal and mismatched return were
worse than intact and correct return in every realization. It does not support
the stronger registered claim that both molecular controls would be suppressed
below the common absolute `0.50` threshold.

Accordingly, Experiment 013 cannot be reported as confirmation of the complete
domain-prior O3 generation-transfer hypothesis. Its transparent result is a
mixed component pattern under an overall preregistered `NOT_SUPPORTED`
decision. It motivates, but does not itself authorize, later investigation of
whether absolute score calibration is domain-specific while causal ordering is
the transferable invariant.
