# Preregistration: Experiment 008B

## Title

PySCF Lithium Spin-Representation Prediction of the Lithium-6/Lithium-7
Ground-State Hyperfine Interval Ratio

## Status

PREREGISTERED — NOT EXECUTED

This status becomes effective only after the public registration commit, tag,
GitHub Release, and DOI are verified. Registration validation and unit tests
may run before then. Target frequency values may not be loaded and scientific
execution may not run before public registration is verified.

## 1. Primary question

Does the factorised generator formed from a shared electronic contact scalar,
the isotope nuclear `g` factor, and the diagonal-rotation interval factor
predict the raw lithium-6/lithium-7 `2S1/2` ground-state hyperfine interval
ratio more accurately than either registered one-factor control?

## 2. Design disclosure

The design is result-informed by private CP-157 exploration. CP-157 computed a
Li `2S` electronic coefficient with PySCF and generated the lithium-6 and
lithium-7 spin-sector geometries before either target hyperfine frequency was
loaded. E008B prospectively freezes the resulting prediction, auxiliary
inputs, controls, thresholds, source, extraction rules, and runner. The target
values are absent from this package.

## 3. Frozen factorised generator

For isotope `X`, freeze the clamped-nucleus interval model

`nu_X = C_e * g_X * q_X`,

where

- `C_e = 176.04278247339448 MHz/g` is the CP-157 uncontracted cc-pCVQZ
  unrestricted-Hartree-Fock PySCF coefficient;
- `g_X = (mu_X/mu_N)/I_X`; and
- `q_X` is the difference between the two `I dot J` eigenvalues for `J=1/2`.

Freeze the independent nuclear inputs:

- lithium-6: `I_6=1`, `mu_6/mu_N=0.82204463(37)`, hence `g_6=0.82204463`;
- lithium-7: `I_7=3/2`, `mu_7/mu_N=3.25641619(57)`, hence
  `g_7=2.1709441266666665`.

The generated representations give:

- lithium-6 sectors `F={1/2,3/2}`, ranks `{2,4}`, `q_6=3/2`;
- lithium-7 sectors `F={1,2}`, ranks `{3,5}`, `q_7=2`.

## 4. Frozen predictions

The primary prediction is

`r_full = nu_6/nu_7 = (g_6 q_6)/(g_7 q_7)`

`r_full = 0.28399324742025683`.

The two registered controls are:

- nuclear-`g` only, omitting the representation interval factor:
  `r_g=0.3786576632270091`;
- representation only, omitting the nuclear-`g` factor:
  `r_q=0.75`.

The PySCF absolute predictions are frozen as secondary diagnostics:

- lithium-6: `217.07253597376808 MHz`;
- lithium-7: `764.3580893053467 MHz`.

The common PySCF coefficient cancels exactly from the primary isotope ratio.
Its numerical use remains explicit and testable in the absolute predictions.

## 5. Frozen target source and observation map

After registration, extract the reported experimental ground-state hyperfine
intervals for lithium-6 and lithium-7 from the fixed critical comparison
source identified in `benchmark_sources.json`. Store frequencies and their
reported standard uncertainties in hertz without rounding beyond the source.

The observed primary quantity is simply

`r_obs = nu_6/nu_7`.

Propagate the frequency uncertainties in log space. Propagate the independent
magnetic-moment uncertainties into models that use `g_6/g_7`.

## 6. Primary decision rule

The nearest log separation between the full prediction and either control is

`d_min=0.2876820724517809`.

Freeze a common acceptance half-width

`tau=d_min/4=0.07192051811294523`.

For each model `m`, let `sigma_m` be the quadrature sum of the measurement
log-ratio uncertainty and that model's frozen auxiliary-input uncertainty.
The model passes only if

`abs(log(r_obs/r_m)) + 3 sigma_m <= tau`.

The primary decisions are:

- `FULL_FACTORISED_GENERATOR_SUPPORTED` when only `r_full` passes;
- `NUCLEAR_G_ONLY_CONTROL_SUPPORTED` when only `r_g` passes;
- `REPRESENTATION_ONLY_CONTROL_SUPPORTED` when only `r_q` passes;
- `NEITHER_REGISTERED_MODEL_SUPPORTED` when no single registered model passes;
- `PROVENANCE_FAILURE` when any frozen hash, schema, record, unit, source, or
  positivity check fails, in which case scientific classification stops.

The registered bands cannot overlap.

## 7. Mandatory secondary diagnostics

The runner reports the two observed frequencies, both clamped PySCF absolute
predictions, their signed relative and absolute log errors, and the
measurement-file SHA-256. These diagnostics cannot override the primary ratio
classification.

The absolute predictions use unrestricted Hartree-Fock with a clamped nucleus.
The registered `0.000717906156476737` CVTZ/CVQZ relative coefficient change is
reported as a numerical electronic-scale proxy, not as a complete physical
uncertainty.

## 8. Interpretation

Support for the full generator establishes a prospective, no-target-value
prediction of the lithium isotope interval ratio from the combined electronic,
nuclear, and representation factors. The comparison with both one-factor
controls identifies whether the joint factorisation, rather than either factor
alone, carries the observed isotope structure.

The absolute diagnostics separately show how far the CP-157 PySCF electronic
scale reaches before correlated, recoil, relativistic, radiative, and nuclear
structure refinements.

## 9. Publication order

1. Commit and push this preregistration package.
2. Create and verify tag `e008b-preregistration-v1.0.0`.
3. Create the GitHub preregistration Release and obtain and verify its DOI.
4. Extract no target value before all three public registration objects are
   verified.
5. Create the exact two-record measurement file from the frozen source.
6. Execute once from the registered commit into a new output directory.
7. Inspect and preserve all outputs before any result commit, release,
   manuscript change, or external result message.
