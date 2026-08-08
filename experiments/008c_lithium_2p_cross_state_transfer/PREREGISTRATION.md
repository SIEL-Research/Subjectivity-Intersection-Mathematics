# Preregistration: Experiment 008C

## Title

Lithium `2^2P_1/2` Cross-State Test of a Recursive Sector-Reentry Isotope
Correction

## Status

PREREGISTERED — NOT EXECUTED

This status becomes effective only after the registration commit, tag,
GitHub Release, and DOI are public and verified. No target central value or
target uncertainty may be extracted before those objects are verified.

## 1. Primary question

When transferred from lithium `2S_1/2` to lithium `2^2P_1/2`, does the raw
lithium-6/lithium-7 hyperfine interval ratio support:

1. the factorised nuclear-`g` and representation base;
2. that base with the CP-153 bilateral-mass response; or
3. that base with the CP-158 recursive mass-and-sector response?

## 2. Design disclosure and scope

E008C is result-informed by E008B and CP-158. E008B's observed lithium ground
state residual was known before CP-158 was constructed. CP-158 reduced that
same lithium residual post hoc but failed transfer to the already known H/D
system. E008C therefore tests only whether the fixed lithium candidate transfers
to a distinct lithium electronic state. It is not evidence of an
atomic-universal correction law.

## 3. Frozen target and source

The primary target is the raw `2^2P_1/2` zero-field hyperfine interval ratio

`r_obs = Delta_nu(6Li)/Delta_nu(7Li)`.

The source is fixed as `doi:10.1139/p65-075`, which reports the magnetic
interaction constants for the `2^2P_1/2` level of both stable lithium isotopes
using optical-radio-frequency double resonance. No reported constant or
uncertainty is present in this package.

For `H_hfs=A I dot J` and `J=1/2`, freeze

`Delta_nu_X = abs(A_X) q_X`,

with `q_6=3/2` and `q_7=2`. If the source reports intervals directly in
addition to `A`, the registered extraction remains the reported magnetic
dipole constant `A`; do not choose whichever representation agrees better.

## 4. Frozen predictions

Using the E008B nuclear moments and spin interval factors, freeze

`r_base = 0.28399324742025683`.

Using the CP-153 bilateral coordinate `b(M)=4M/(M+1)^2`, freeze

`r_mass = r_base exp[b(M_6)-b(M_7)]`

`r_mass = 0.28400802967617617`.

Using the CP-158 sector imbalance `d=w_high-w_low` and
`z(M,d)=b(M)(1+d^2)`, freeze

`r_recursive = r_base exp[z(M_6,1/3)-z(M_7,1/4)]`

`r_recursive = 0.2840139905285925`.

No fitted coefficient is allowed.

## 5. Precision gate

The nearest registered model separation is the mass-only/recursive separation:

`d_min = 20.988103293641875 ppm` in log space.

Freeze the common acceptance half-width `tau=d_min/4`:

`tau = 5.247025823410469 ppm`.

The frozen nuclear-moment model uncertainty is `0.48293495829205574 ppm` in
log space. Let `sigma_measurement` be the propagated log uncertainty of the
two extracted constants. Before model agreement is evaluated, require

`3 sqrt(sigma_measurement^2 + sigma_moment^2) <= tau`.

Equivalently, `sigma_measurement` must not exceed
`1.681013068429318 ppm`. If it does, the primary decision is
`INSUFFICIENT_PRECISION`; no band widening, source replacement, rounding, or
central-value-based secondary classification is permitted.

## 6. Primary decision rule

When the precision gate passes, model `m` passes only if

`abs(log(r_obs/r_m)) + 3 sigma_total <= tau`.

The decisions are:

- `RECURSIVE_SECTOR_TRANSFER_SUPPORTED` when only `r_recursive` passes;
- `BILATERAL_MASS_ONLY_TRANSFER_SUPPORTED` when only `r_mass` passes;
- `FACTORISED_BASE_TRANSFER_SUPPORTED` when only `r_base` passes;
- `NO_REGISTERED_TRANSFER_MODEL_SUPPORTED` when none passes;
- `INSUFFICIENT_PRECISION` when the frozen precision gate fails; and
- `PROVENANCE_FAILURE` for any source, schema, unit, hash, or extraction failure.

The registered bands do not overlap.

## 7. Extraction and execution order

1. Commit and push this complete registration package.
2. Create and verify tag `e008c-preregistration-v1.0.0`.
3. Create the GitHub preregistration Release and verify its DOI.
4. Extract the two reported constants and uncertainties exactly once.
5. Preserve signed constants in hertz; the runner applies `abs(A)` only when
   constructing positive interval magnitudes.
6. Execute once from the registered commit into a new output directory.
7. Preserve and inspect every output before any result commit or message.
