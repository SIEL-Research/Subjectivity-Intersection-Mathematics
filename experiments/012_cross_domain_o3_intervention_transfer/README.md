# Experiment 012 — Cross-domain O3 intervention transfer

Experiment 012 is the public confirmatory successor to the result-informed
local E012 exploration. It executes atomic, molecular, and cellular dynamics
independently and compares only their post-execution causal intervention
signature.

The registered question is whether all held-out realizations satisfy

```text
intact O3 and correct O3 return
    > O3 removal and mismatched O3 return.
```

No shared scalar mediator, power law, or common survival variable enters the
three domain engines. The comparison is made only after each engine produces
its own whole-formation readout.

Status: `PREREGISTERED_NOT_EXECUTED`

Only target-free validation is allowed before the preregistration release and
DOI are public:

```bash
python3 experiments/012_cross_domain_o3_intervention_transfer/run.py \
  --validate-registration

python3 -m unittest discover \
  -s experiments/012_cross_domain_o3_intervention_transfer/tests -v
```

Scientific execution requires the public preregistration receipt:

```bash
python3 experiments/012_cross_domain_o3_intervention_transfer/run.py \
  --execute --registration-receipt /path/to/e012_registration_receipt.json
```

Every supported, mixed, or unsupported result is retained.
