# E008D derivation provenance

## Construction history

CP-159 identified the complete second-order isotope-correction ratio as an
observation map. CP-160 generated the rank-one angular coefficients. CP-161
generated the contact, spin-dipole, orbital, and electric-quadrupole electronic
coordinates from a maximum-overlap PySCF state and composed the M1-M1 and M1-E2
returns without a fitted parameter.

E008D transfers that frozen composition from lithium to potassium. Both
potassium isotopes have `I=3/2`, so the numerical distinction is driven by the
rank composition and isotope nuclear moments rather than unequal spin-sector
dimensions.

## Source separation

Construction inputs are isolated in `construction_sources.json`. Benchmark
metadata and the post-registration extraction rule are isolated in
`benchmark_sources.json`. `generate_prediction.py` does not import either the
benchmark lock or a benchmark measurement file.

The prediction file records `target_values_loaded: false` and
`free_fitted_parameters: 0`.

## Operator sources

- K. Beloy and A. Derevianko, second-order M1-M1 and M1-E2 hyperfine structure
  of alkali-metal P states, `doi:10.1103/PhysRevA.78.032519`.
- M. Puchalski and K. Pachucki, Cartesian operator normalization for lithium P
  states, `doi:10.1103/PhysRevA.79.032510`.

The first source supplies only target metadata before opening. Its potassium
correction entries are not present in this package.
