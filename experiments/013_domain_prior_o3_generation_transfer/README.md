# Experiment 013 — Domain-prior O3 generation transfer

Experiment 013 prospectively tests whether one rule can generate an O3
candidate before any successful carrier is named, and whether the generated
candidate has the same four-edge causal topology in independently executed
atomic, molecular, and cellular reduced models.

```text
R*_D = P_loc,D(G_D)
C*_D = G_D - R*_D
```

The domain bridge supplies differentiated local terms and a native generator.
It does not supply an O3 label or shared scalar mediator.

Status: `REGISTRATION_DRAFT_NOT_RELEASED_NOT_EXECUTED`

Target-free checks only:

```bash
python3 experiments/013_domain_prior_o3_generation_transfer/run.py --validate-registration
python3 -m unittest discover -s experiments/013_domain_prior_o3_generation_transfer/tests -v
```

Scientific execution is locked until a public registration receipt is present.
Every supported, mixed, and unsupported outcome will be retained.
