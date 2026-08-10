# Experiment 011 technical specification

## Fixed implementation

- Python 3 with NumPy 2.0.2.
- Frozen E009 reduced cellular source copied as `cell_core.py`.
- Coupling grid: `0.400:0.002:0.920` inclusive.
- 96 common-random-number lineages per coupling and target family.
- Target bridge exponents: `0.75`, `1.25`, `1.50`.
- Target ensemble seeds: `2026130100`, `2026130200`, `2026130300`.
- Damage amplitude: `0.60` during the frozen E009 damage interval.
- Bridge intervention ends at minute `50.0`.

## Endpoint

For each coupling, a lineage survives when it is not dead, every late module
recovers to at least 80% of its pre-damage level, and late damage is below
`0.10`. `lambda_90` is the first scanned coupling with at least 90% survival.

## Transformation

For family exponent `q`, `m_90=lambda_90^(2q)`. The three survival curves are
interpolated to the common mediator grid `0.20:0.002:0.85` for the registered
collapse RMSE.

## Execution lock

`--execute` requires a receipt containing the verified preregistration tag,
full commit SHA, GitHub release URL, and Zenodo DOI. It refuses to run when a
results directory already exists.
