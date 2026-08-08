# Preregistration: Experiment 008

## Title

Preregistered Atomic-Closure Transfer of Subjectivity-Intersection Mathematics

## Status

PREREGISTERED RESULT-INFORMED DESIGN — NOT EXECUTED

No scientific output from the E008 runner exists at registration. Registration
validation and unit tests may run; scientific execution may not run until the
registration commit and tag are publicly verified.

## 1. Primary question

Can the formation grammar supported by the 006-series,

`(O_A, O_B) -> O_3 -> (O_A', O_B', O_3')`,

transfer to an atomic domain as one fixed chain connecting finite-mass
relational closure, boundary-independent closure identity, an additive closure
coordinate, inverse-square spatial distribution, three-dimensional stable
binding, Coulomb scaling, and composition-compatible continuous reentry?

## 2. Result-informed firewall

The E008 hypotheses and decision structure were informed by prior unpublished
exploratory computational work. Those exploratory outputs are excluded from
the confirmatory evidence reported by E008.

The hydrogen-deuterium 1S-2S isotope shift and every atomic system used during
private development are excluded from the E008 empirical holdout. E008 instead
freezes two transfer systems not used in that development:

1. muonium `(mu+ e-)` 1S-2S; and
2. positronium `(e+ e-)` 1S-2S.

The public measurements already exist in the literature, so this is not a
cognitively blind prediction. It is a prospective, publicly frozen transfer
test: the source identifiers, extraction rules, leading-order prediction,
omitted-correction budget, controls, and decisions are fixed before E008
execution. Measurement values are not included in the registration package and
must be supplied after registration in the exact registered schema.

No threshold, candidate, source, or decision rule may change after public
registration.

## 3. Fixed atomic map

For a two-body charged closure with constituent coordinates `r_1, r_2` and
masses `m_1, m_2`, define

`r = r_1 - r_2`

and remove center-of-mass translation. The relative coordinate and its bound
spectral subspace are the registered operational carrier of atomic closure.
Changes in `r` update both constituents with nonzero mass-weighted fractions.

The map does not introduce a third particle or state register. The atomic
whole is represented by a relational bound closure whose state constrains both
constituents' subsequent states.

## 4. Frozen structural bridge audits

### S1. Boundary identity

The registered total-scaling exponents are

`{-4,-3,-2,-3/2,-1,-1/2,0,1/2,1,3/2,2,3,4}`.

If every enclosing source-free boundary reconstructs the same closure
identity, only exponent zero may survive.

### S2. Regular compositional coordinate

The registered regular composition families are power sums with

`q in {1/3,1/2,2/3,3/2,2,3,4}`

and deformed sums with

`k in {1/4,1/2,1,2,4}`.

Every regular family must admit its frozen monotone additive generator. The
maximum operation is the registered non-strict control and must fail the
strict-order gate.

### S3. Spatial distribution

The registered radial-force candidates are pure inverse powers with exponents
`1, 3/2, 2, 5/2, 3`, Yukawa-modified inverse square, logarithmically modified
inverse square, and short-range modified inverse square. Across the registered
radii `{1/2,3/4,1,3/2,2,3,4,6}`, only the unmodified inverse-square candidate
may have constant spherical total `r^2 F(r)` to numerical tolerance `1e-12`.

### S4. Dimensional stable closure

Dimensions `d=1,...,12` are evaluated under the same three frozen conditions:

1. asymptotic separation of distinct closures;
2. no ultraviolet fall to the center without an external cutoff; and
3. a cutoff-free discrete bound scale.

Exactly `d=3` must satisfy all three.

### S5. Continuous reentry

Continuous, reversible, norm-preserving reentry is tested against linear
unitary/orthogonal, dissipative, amplifying, shear, state-dependent phase, and
projectively normalized controls. Minimal closure persistence may retain
nonlinear controls. After imposing compatibility with state composition, only
linear norm-preserving groups may remain, and their generators must satisfy

`G^dagger = -G`, `H=iG`, and `H^dagger=H`.

The complex field, Hilbert norm, and state-composition law are bridge
conditions in this experiment; they are not outcomes silently inferred after
execution.

## 5. Frozen empirical holdout

The leading relational gross-structure prediction is

`nu_1S-2S = (3/4) R_infinity c / (1 + m_e/m_partner)`.

For positronium, `m_partner=m_e`. For muonium, the 2022 CODATA
electron-muon mass ratio is frozen in the runner. No fitted parameter is used.

The infinite-partner-mass control is

`nu_infinite = (3/4) R_infinity c`.

For each holdout, both conditions must pass:

1. relative error of the relational prediction is at most `2 alpha^2`; and
2. its absolute error is at least 100 times smaller than the infinite-mass
   control error.

The `2 alpha^2` budget is fixed as a leading omitted relativistic/QED scale,
not fitted to either measurement.

The frozen measurement sources and extraction rules are in
`benchmark_sources.json`. A post-registration measurement file must include
exactly the two registered records, source identifiers, frequencies in Hz, and
one-standard-deviation uncertainties in Hz. No replacement source is allowed.

## 6. Primary conjunction and classifications

The five structural gates are:

1. boundary identity selects only constant total;
2. every regular composition admits its additive coordinate and max fails;
3. only inverse square conserves spherical total;
4. only three dimensions satisfy the stable-closure conjunction; and
5. composition-compatible continuous reentry leaves the registered linear
   norm-preserving generator class.

The two empirical gates are the muonium and positronium conjunctions defined
above.

Exactly one classification is emitted:

### `SUPPORTED_ATOMIC_CLOSURE_TRANSFER`

All five structural gates and both empirical holdouts pass.

### `STRUCTURAL_TRANSFER_ONLY`

All five structural gates pass and at least one empirical holdout fails.

### `EMPIRICAL_GROSS_STRUCTURE_ONLY`

Both empirical holdouts pass and at least one structural gate fails.

### `NOT_SUPPORTED`

At least one structural gate and at least one empirical holdout fail.

### `PROVENANCE_FAILURE`

The registration hashes, measurement schema, record set, source identifiers,
units, or required fields fail validation. Scientific classification stops.

No composite score compensates for a failed gate.

## 7. Interpretation boundary

A supported result establishes that one fixed Subjectivity-Intersection
formation grammar supplies a reproducible cross-domain reconstruction of the
registered atomic-closure chain and transfers its finite-mass gross-spectrum
prediction to two held-out two-body atoms.

The structural layers identify every bridge condition explicitly. The
empirical layer tests the leading relational mass dependence rather than
higher-order QED, spin, annihilation, nuclear-size, or radiative corrections.

## 8. Publication order

1. Commit and push this preregistration, specification, runner, tests,
   benchmark-source lock, and manifest.
2. Create and verify tag `e008-preregistration-v1.0.0`.
3. Do not execute E008 before the pushed commit and tag are verified.
4. Prepare the measurement file from the frozen sources after registration.
5. Execute once from the registered commit.
6. Preserve every output regardless of classification.
7. Inspect the complete result before any result commit, tag, Release, DOI, or
   manuscript change.
