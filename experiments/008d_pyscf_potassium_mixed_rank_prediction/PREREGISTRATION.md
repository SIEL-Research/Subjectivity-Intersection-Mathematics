# Preregistration: Experiment 008D

## Title

Prospective potassium-isotope test of a PySCF-generated mixed-rank reentry

## Status

PREREGISTERED — NOT EXECUTED

This status becomes effective only after the registration commit, tag, public
GitHub Release, and DOI are verified. The benchmark correction values must not
be extracted before that verification.

## 1. Primary question

Does the CP-161 composition of magnetic rank one with electric rank two predict
the independently tabulated ratio of complete second-order corrections for the
lowest `4P_1/2` states of potassium-39 and potassium-41?

## 2. Design disclosure

E008D was designed after CP-159 through CP-161 and after the lithium benchmark
was known. Those exploratory calculations established the observation map,
the rank-one angular generator, and the PySCF mixed-rank electronic generator.
No potassium correction value was used to choose the electronic method, basis,
nuclear inputs, prediction, tolerance, or decision rule.

The source metadata establishes that the fixed paper tabulates second-order
effects for alkali-metal `P` states. Its potassium numerical entries are absent
from the registration package.

## 3. Frozen target

The endpoint is

`r_obs = delta A_P1/2(39K) / delta A_P1/2(41K)`

using the complete second-order `M1-M1 + M1-E2` corrections tabulated in
`doi:10.1103/PhysRevA.78.032519`.

The source, isotope pair, state, sign handling, and extraction rule cannot be
replaced after registration.

## 4. Frozen construction

For each isotope, freeze

`D_I = -(2/9) X_I^2 + [(2I+3)/(9I)] X_I Y_I`,

where

`X_I = [mu_I/(I m_p/m_e)] X_e`,

`Y_I = Q_I [barn/lambda_C^2] Y_e`,

`X_e = g_e contact/6 + orbital/4 - g_e spin_dipole/16`,

`Y_e = -3 electric_quadrupole/5`.

The four electronic coordinates are generated from a neutral-potassium `4P`
maximum-overlap UHF state. The primary basis is uncontracted def2-QZVPP. The
uncontracted def2-TZVPP result is the frozen convergence diagnostic.

No fitted coefficient is allowed.

## 5. Frozen prediction and control

Primary mixed-rank prediction:

`r_mixed = 1.4239826742729131`.

M1-M1-only control:

`r_M1 = 3.319224048274411`.

The uncontracted TZ/QZ prediction change is `3379.765754382796 ppm` in log
space. The two registered models are separated by more than `0.8` in absolute
log space.

## 6. Primary decision rule

Let `u_round` be the propagated log half-width implied by the printed precision
of the two tabulated corrections. For registered model `m`, define

`E_m = abs(log(r_obs/r_m)) + u_round`.

The common acceptance half-width is frozen at `0.05` in log space. A strong
match is additionally recorded at `0.01`.

Decisions:

- `MIXED_RANK_PROSPECTIVE_PREDICTION_SUPPORTED` when only `r_mixed` passes;
- `M1_ONLY_CONTROL_SUPPORTED` when only `r_M1` passes;
- `BOTH_REGISTERED_MODELS_WITHIN_TOLERANCE` when both pass;
- `NO_REGISTERED_MODEL_SUPPORTED` when neither passes; and
- `PROVENANCE_FAILURE` for source, schema, sign, unit, hash, or extraction
  failure.

The registered bands cannot overlap because the model separation is much
larger than twice the acceptance half-width.

## 7. Registration and opening order

1. Commit and push this complete package without benchmark values.
2. Create and verify tag `e008d-preregistration-v1.0.0`.
3. Create the public preregistration Release and verify its DOI.
4. Extract the two potassium corrections exactly once from the frozen source.
5. Record the printed rounding half-width for each value without adding digits.
6. Execute the registered runner once into a new output directory.
7. Inspect all results before any result commit, Release, or message.
