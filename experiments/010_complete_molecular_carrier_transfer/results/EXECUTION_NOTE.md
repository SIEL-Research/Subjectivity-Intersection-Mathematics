# Experiment 010 Execution Note

Experiment 010 was executed exactly once from the registered commit after verification of the preregistration DOI.

## Registration

- Registered commit: `56f6d20a77b65e70eed7ab7ada27f6198ad62332`
- Registered tag: `e010-preregistration-v1.0.0`
- Preregistration DOI: `10.5281/zenodo.21865563`
- Target executions: one
- Reruns or result-informed repairs: none

## Command

```text
/Users/satoru/Documents/Codex/2026-08-05/github-siel-research-subjectivity-intersection-creation/.venv-pyscf/bin/python experiments/010_complete_molecular_carrier_transfer/run.py --execute --registration-receipt /Users/satoru/Documents/Codex/2026-08-09/7/e010_registration_receipt.json --output experiments/010_complete_molecular_carrier_transfer/results
```

## Environment

- NumPy: 2.0.2
- PySCF: 2.14.0

## Outcome

- Registered decision: `COMPLETE_MOLECULAR_CARRIER_TRANSFER_SUPPORTED`
- Gates passed: 27/27 (9/9 in each of three frozen basis profiles)

## Runtime warning disclosure

NumPy emitted divide-by-zero, overflow, and invalid-value warnings at `run.py:98` during some matrix multiplications. The registered finite-value guard did not raise an exception, the single run completed, and all saved result arrays and the final decision were finite. The run was not repeated or repaired after observing the result.
