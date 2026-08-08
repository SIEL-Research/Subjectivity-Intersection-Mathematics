# Preregistration: Experiment 008A

## Title

Bilateral-Reentry Prediction of the Channel-Normalized Hydrogen-Deuterium
Ground-State Hyperfine Ratio

## Status

PREREGISTERED — NOT EXECUTED

This status becomes effective only after the public registration commit, tag,
GitHub Release, and DOI are verified.

Registration validation and unit tests may run. No target hyperfine frequency
may be loaded and scientific execution may not run until the registration
commit, tag, GitHub Release, and DOI are publicly verified.

## 1. Primary question

Does the new unit-response postulate of Subjectivity-Intersection Mathematics,

`R'(0)=1`, equivalently `lambda=1`,

predict the channel-normalized deuterium-to-hydrogen 1S hyperfine coefficient
ratio more accurately than the registered standard Coulomb-contact control?

## 2. Design disclosure

The model and numerical prediction were generated during unpublished
exploratory work CP-151 through CP-155. That work established:

1. joint rotation selects the `S_A dot S_B` interaction direction;
2. Coulomb contact gives cubic reduced-mass scaling;
3. minimal bilateral participation gives `b=4p_Ap_B`;
4. continuous composition gives the family `exp(lambda b)`; and
5. prior conditions do not identify `lambda`.

E008A therefore does **not** describe `lambda=1` as derived from the earlier
conditions. It tests `lambda=1` as a new, parameter-free, pre-benchmark
postulate. The target measurements already exist publicly, so E008A is not
cognitively blind. It is prospectively frozen: target values are absent from
this package and no formula, threshold, source, or decision may change after
registration.

## 3. Frozen model

For nuclear mass `M` in electron-mass units,

`mu(M)=M/(M+1)`,

`b(M)=4M/(M+1)^2`.

The registered Subjectivity-Intersection postulate is

`G_SI(M) proportional to mu(M)^3 exp[b(M)]`.

Using the frozen 2022 CODATA mass ratios,

- `M_H=1836.152673426`;
- `M_D=3670.482967655`;

the primary SI prediction is

`r_SI=G_SI(D)/G_SI(H)=0.9997293072637635`.

The registered standard contact control is

`G_0(M) proportional to mu(M)^3`,

with

`r_0=1.0008165196710828`.

The signed SI departure relative to the control is approximately
`-0.00108632540125986`.

## 4. Frozen observation map

For electronic `J=1/2`, use

`H_hfs=A I dot J`.

The interval between `F=I+1/2` and `F=I-1/2` is

`Delta nu=(I+1/2)|A|/h`.

Define the channel-normalized observable, up to factors common to H and D,

`G_X=[Delta nu_X/(I_X+1/2)]/|g_I,X|`,

where `g_I=(mu_I/mu_N)/I`. Freeze:

- `I_H=1/2`;
- `I_D=1`;
- `mu_H/mu_N=2.79284734463`;
- `mu_D/mu_N=0.8574382335`.

The observed primary ratio is therefore

`r_obs=(nu_D/nu_H)*(1/1.5)*abs(g_I,H/g_I,D)`.

The auxiliary magnetic moments come from measurement routes separate from the
atomic zero-field target intervals: direct proton Penning-trap measurement and
HD molecular NMR ratios with shielding corrections. The deuteron input remains
theory-assisted through molecular shielding.

## 5. Frozen target sources

The two target frequencies must be extracted from the critical experimental
compilation fixed in `benchmark_sources.json`:

- atomic hydrogen ground-state 1S hyperfine interval;
- atomic deuterium ground-state 1S hyperfine interval.

Both source identifiers, extraction instructions, record identifiers, units,
and uncertainty rules are frozen. The post-registration measurement file must
contain exactly the registered records and no others.

## 6. Primary decision rule

Let

`d=abs(log(r_SI/r_0))`

and freeze the acceptance half-width

`tau=d/4`.

Propagate the one-standard-deviation frequency uncertainties and the frozen
magnetic-moment uncertainties in log-ratio space. Let `sigma_log` be the
resulting uncertainty.

### `SI_LAMBDA_ONE_SUPPORTED`

`abs(log(r_obs/r_SI))+3 sigma_log <= tau`.

### `STANDARD_CONTACT_SUPPORTED`

`abs(log(r_obs/r_0))+3 sigma_log <= tau`.

### `NEITHER_MINIMAL_MODEL_SUPPORTED`

Neither registered band contains the full three-standard-deviation interval.

### `PROVENANCE_FAILURE`

Any registration hash, schema, source identifier, record set, unit, positivity,
or required-field check fails. Scientific classification stops.

The two support bands cannot overlap because each has quarter-separation
half-width.

## 7. Registered full-theory control

The primary contrast is intentionally between the new SI postulate and the
standard leading contact law. It is not represented as a complete contest with
QED and nuclear theory.

As a mandatory secondary control, the report must state that conventional
hyperfine theory contains recoil, radiative, finite-size, magnetization, and
nuclear-polarization terms. The frozen source reports sub-ppm QED uncertainty
and system-dependent nuclear corrections at tens to hundreds of ppm. A
conservative `500 ppm` log-ratio nuisance scale is registered for interpretation.

The SI-control separation is about `1086 ppm`. The runner reports whether the
observed departure from each minimal model lies inside or outside the nuisance
scale, but this diagnostic cannot override the primary classification.

## 8. Secondary diagnostics

The runner reports, without affecting the primary decision:

1. the lambda implied by the central observed ratio,
   `lambda_hat=log(r_obs/r_0)/(b_D-b_H)`;
2. central and three-sigma log errors for both registered models;
3. whether each error is within the 500 ppm full-theory nuisance scale; and
4. the measurement-file SHA-256.

## 9. Interpretation boundary

Support would establish that the pre-registered `lambda=1` bilateral-reentry
postulate predicts this channel-normalized isotope ratio better than the
leading contact control under the frozen observation map. It would not prove
Subjectivity Intersection as an ontology and would not replace full bound-state
QED or nuclear-structure calculations.

Failure would reject the registered `lambda=1` atomic bridge. It would not
invalidate the CP-151 joint-rotation algebra, the CP-152 contact scaling, or the
general exponential family identified in CP-154.

## 10. Publication order

1. Commit and push this preregistration, specification, runner, tests, source
   lock, derivation provenance, and manifest.
2. Create and verify tag `e008a-preregistration-v1.0.0`.
3. Create the GitHub preregistration Release and obtain/verify its DOI.
4. Do not execute E008A before the pushed commit, tag, Release, and DOI are
   verified.
5. Extract the two target frequencies from the frozen source into the exact
   registered schema.
6. Execute once from the registered commit.
7. Preserve and inspect all outputs before any result commit, tag, Release,
   DOI, manuscript change, or external result message.
