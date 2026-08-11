# Experiment 013 local exploration: generated O3 and molecular convergence

Status: `LOCAL_RESULT_INFORMED_EXPLORATION`

This directory addresses three audit questions raised after public Experiment
012 without altering E012 or treating these analyses as confirmatory evidence.

1. Does the molecular mismatch separation continue to sharpen in a sparse
   cc-pVTZ FCI calculation, or was the cc-pVDZ pass an isolated basis effect?
2. Can one rule fixed before a domain is named generate the candidate O3 from
   the domain's native generator and additive/isolated reference?
3. What does a genuinely computed leave-one-domain-out test look like when it
   transfers only ordinal intervention topology rather than a shared scalar?

The proposed generator rule is

```text
C*_D = G_native,D - G_additive/isolated,D
```

where both generators must be supplied by the domain bridge before any O3
label is assigned. An intervention counts as complete removal only when it
returns the generator to the registered additive/isolated reference.

The sparse high-basis calculation is diagnostic only. It does not reproduce
the complete E012 Metropolis surface and cannot change the registered E012
decision.

## Readiness outcome

The exploration closes the design question sufficiently to draft and register
a prospective Experiment 013. It does not itself count as E013 evidence. The
registration must freeze the local-preserving severing projection, the
candidate residual, the overlap-based mismatch rule, and the four-edge causal
partial order before any fresh target outcomes are computed. The unrestricted
all-pairwise ordering remains a reported negative diagnostic rather than a
gate.

Run with the PySCF environment used by E010:

```bash
.venv-pyscf/bin/python experiments/013_o3_generator_convergence_exploration/run.py
```
