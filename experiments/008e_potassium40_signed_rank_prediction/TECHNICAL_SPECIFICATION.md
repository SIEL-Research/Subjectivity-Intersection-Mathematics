# E008E technical specification

## Frozen system

- Atom: neutral potassium.
- Electronic manifold: lowest `4P_1/2` and `4P_3/2` pair.
- Target isotope: K-40 ground state, `I=4`.
- Primary quantity: complete leading `M1-M1 + M1-E2` second-order correction
  to `A(P_1/2)` in kHz.
- Secondary quantities: corrections to `A(P_3/2)` and `B(P_3/2)`, plus
  generated K-40/K-39 and K-40/K-41 ratios.

## Construction invariants

1. Rank-one `T1` and rank-two `T2` remain separate until `eta` and `zeta` are
   formed.
2. The same potassium electronic coordinates are used for all three isotopes.
3. No isotope-specific electronic coefficient is fitted.
4. K-39 and K-41 correction values are absent from the generator.
5. K-40 correction values remain absent until public registration is verified.

## Uncertainty envelope

The generator evaluates every endpoint combination of:

- printed half-unit widths for `T1`, `T2`, and the fine-structure interval;
- the quoted magnetic-moment uncertainty; and
- the quoted quadrupole-moment uncertainty.

Common electronic endpoints are correlated when isotope ratios are formed.
The envelope is a bounded input-propagation interval, not a Gaussian
confidence interval.

## Future benchmark decision

An eligible independent benchmark supplies a central value and positive
half-width for the primary correction. The preregistered prediction is
`SUPPORTED` when the two closed intervals overlap and `STRONG_MATCH` when the
benchmark central value lies inside the prediction envelope. A non-overlap is
`NOT_SUPPORTED`. Source or independence failure is `PROVENANCE_FAILURE`.

If no eligible independent benchmark exists, the correct outcome is
`OPEN_NOVEL_PREDICTION_NO_INDEPENDENT_BENCHMARK`.
