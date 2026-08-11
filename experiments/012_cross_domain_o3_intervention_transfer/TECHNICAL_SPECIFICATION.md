# Experiment 012 technical specification

## Compression ladder

```text
domain source -> domain dynamics -> domain whole readout
              -> cross-domain causal signature
```

Inference is permitted from left to right only. Scalar whole scores are not
used to infer identity of source-level objects.

## Atomic engine

A one-dimensional soft-Coulomb two-body Hamiltonian is propagated by a damped
split-operator method on 1024 grid points. Hydrogen and deuterium reduced
masses are frozen in `target_registry.json`. Whole formation is the final
probability in `|x| < 6`. The mismatched return uses the same attractive
potential translated by eight length units.

## Molecular engine

Each of the three E010 FCI surfaces is used as an independent energy landscape.
A seeded nearest-neighbour Metropolis trajectory begins at a symmetry-equivalent
full minimum. Removal uses the one-electron-cross-deleted surface. Mismatched
return switches to the single-edge-deleted surface. Correct return switches to
the complete surface. The readout is the late fraction of trajectory points
within `0.35 Å` of the complete system's symmetry-equivalent minimum set.

## Cellular engine

The frozen E009 reduced stochastic dynamics are executed on four new cohorts.
The domain readout is the surviving fraction for native, joint-erased,
time-shifted, and reinjected conditions.

## Provenance lock

`--validate-registration` verifies frozen hashes but refuses a receipt.
`--execute` requires a receipt containing the preregistration tag, commit,
GitHub Release URL, and Zenodo DOI. The result directory must not already exist.
