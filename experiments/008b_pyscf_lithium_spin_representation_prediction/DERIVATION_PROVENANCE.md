# E008B Derivation Provenance

## Private exploration that generated the design

CP-157 in the private Subjectivity-Intersection Creation Principle repository
generated the E008B bridge. Its source state is frozen as:

- repository: `SIEL-Research/Subjectivity-Intersection-Creation-Principle`;
- commit: `ec39a29ebaf9da00fe8047ab60e333929d02704e`;
- experiment: `CP-157_general_spin_pyscf_factorization`;
- decision: `GENERAL_SPIN_PYSCF_FACTORISATION_OBSERVED`.

CP-157 loaded no lithium target hyperfine frequency.

## Generated representation map

For a diagonal joint rotation acting on `I tensor J`, the `I dot J`
eigenvalue in total-spin sector `F` is

`x_F=[F(F+1)-I(I+1)-J(J+1)]/2`.

With `J=1/2`, lithium-6 has `x={-1,1/2}` and lithium-7 has
`x={-5/4,3/4}`. Their interval factors are therefore `3/2` and `2`.

## Electronic bridge

CP-157 used PySCF 2.14.0 and PySCF-properties 0.1.0 at source commit
`4eee5a430fb47eca5962f36fdcaf75c2b87e7ede`. An unrestricted-Hartree-Fock Li
doublet calculation with an uncontracted cc-pCVQZ basis produced
`176.04278247339448 MHz/g_I`. The uncontracted CVTZ/CVQZ relative change was
`0.000717906156476737`.

## Independent auxiliary input

The isotope moments are frozen from Pachucki, Patkóš, and Yerokhin (2023),
DOI `10.1016/j.physletb.2023.138189`. That determination combines measured
atomic nuclear/electron `g`-factor ratios with calculated shielding. It is a
separate input route from the zero-field interval target, although it concerns
the same atomic isotopes.

## Separation from the benchmark

`benchmark_sources.json` identifies the later target extraction. No numerical
target frequency, target-derived ratio, or fitted parameter occurs in this
registration package. `prediction_before_benchmark.json` is the machine-readable
pre-benchmark prediction, and `prediction_sha256.txt` freezes its digest.
