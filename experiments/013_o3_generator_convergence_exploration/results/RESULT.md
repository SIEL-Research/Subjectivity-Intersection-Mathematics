# Experiment 013 local exploration

Molecular diagnosis: `LOW_BASIS_RESOLUTION_HYPOTHESIS_FAVORED`.
Generator diagnosis: `E012_INTERVENTIONS_NOT_UNIFIED_BY_COMPLETE_GENERATOR_RESIDUAL`.
Leave-one-out diagnosis: `EXPLORATORY_CROSS_DOMAIN_ORDINAL_TOPOLOGY_PASSES`.

Generator-rule alignment: `2/3` domains.
Ordinal leave-one-domain-out: `True`.

## Sparse molecular convergence diagnostic

| Basis | Full rejection of mismatch basin | Edge drive toward mismatch basin |
|---|---:|---:|
| 6-31g | 0.005848900 | 0.007602560 |
| cc-pvdz | 0.017059922 | 0.015738747 |
| cc-pvtz | 0.015313685 | 0.065739157 |
| sto-3g | 0.010247728 | 0.002347193 |

The cc-pVTZ edge drive is 4.177x the cc-pVDZ value; the complete-system mismatch rejection remains positive. This favors a low-basis resolution explanation over a demonstrated persistent representation boundary, subject to the sparse-grid limitation.

The fixed generator rule aligns with atomic and cellular removal but not E012 molecular removal: E012 deleted only the one-electron cross sector rather than the complete molecule-minus-isolated-centres residual.

The independently computed ordinal leave-one-domain-out test passed four relations for every held-out domain: intact exceeds removal and mismatch, and correct return exceeds removal and mismatch.

The registered hydrogen/deuterium count remains 2/2, but its reduced-mass span is only 0.000271951. Earlier local muonium/positronium exploration covered a span of 0.495186946 and both passed; those targets are exploratory history, not unused confirmation targets.

These sparse energies diagnose local separation only; they do not reproduce the full E012 trajectories.
