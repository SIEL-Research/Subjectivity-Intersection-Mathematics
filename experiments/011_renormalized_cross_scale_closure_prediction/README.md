# Experiment 011 — Renormalized Cross-Scale Closure Prediction

E011 is the public confirmatory experiment following private integration
exploration across atomic, molecular, and cellular third-term models.

The exploratory result did not support `0.72`, GMR, or a pentagonal constant as
a universal raw threshold. It instead produced a sharper prediction: when the
bridge representation changes, the raw threshold should move according to

```text
m = lambda^(2q),
```

while the effective mediator threshold remains near the frozen value
`m_90=0.506944`.

E011 preregisters three previously unexecuted bridge exponents and new seed
ranges. Before the first public DOI, only the following target-free commands
are permitted:

```bash
python3 experiments/011_renormalized_cross_scale_closure_prediction/run.py \
  --validate-registration

python3 -m unittest discover \
  -s experiments/011_renormalized_cross_scale_closure_prediction/tests -v
```

After the registration commit, GitHub Release, and DOI are verified, the
single registered execution is:

```bash
python3 experiments/011_renormalized_cross_scale_closure_prediction/run.py \
  --execute \
  --registration-receipt /path/to/e011_registration_receipt.json
```

The result is published separately under `e011-results-v1.0.0` with a second
DOI. Supported, partial, and unsupported outcomes are all frozen in the source.

## Boundary

E011 tests held-out transformation covariance inside a frozen reduced bridge.
It is not a complete physical coupling of an atom, molecule, and living cell,
and it does not establish an ontological O3 or a universal biological constant.
