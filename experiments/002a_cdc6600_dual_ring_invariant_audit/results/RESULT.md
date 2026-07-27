# Experiment 002A Result

## Status

**PASS**

## Primary result

The preserved implementation reproduced its registered Boolean
invariant and reset behaviour. The independent classification audit
assigned the registered `CIT` readout to **Class 0 — local-complementarity/common-control null**.

## Exact readout

- source self-test: PASS
- operational paired cases: `128/128` invariant passes
- local-adder cases: `4/4` invariant passes
- single-ring cases: `16/16` invariant passes
- partner-substitution changes: `0/128`
- one-bit intervention changes: `0/768`
- double-high resets: `64/64`
- feedback equals constant control: `true`

## Evidence gates

- `J_joint_generation`: FAIL
- `H_history`: FAIL
- `I_intervention`: FAIL
- `P_pair_specificity`: FAIL
- `G_gauge_invariance`: PASS
- `N_null_separation`: FAIL
- `T_frozen_transfer`: PASS
- `bilateral_feedback`: FAIL

## Interpretation

The two oriented rings and matched buffers do produce the stated
readout. However, the same invariant is already forced at each local
full adder by `S XOR K = 1` in single-high mode. The final dual-ring
comparison therefore combines two constant words and contains no
registered pair or history information.

The `H = Z = 1` transition to `000` is verified as a common reset.
It is not a selective intervention on a relation-generated state.

This result classifies only the registered `CIT` readout. It does not
exclude other uses of the dual-ring architecture or a revised
history-bearing coupling that would require a separate registration.

## Reproducibility receipt

- registration commit: `b8563cf173e2415983f83f997b3075231a5b4bbf`
- remote: `https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics.git`
- schema: `siel-experiment-002a-cdc6600-dual-ring-audit-v1`
