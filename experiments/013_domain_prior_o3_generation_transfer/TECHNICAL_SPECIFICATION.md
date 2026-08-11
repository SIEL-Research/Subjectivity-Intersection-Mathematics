# Experiment 013 technical specification

## Compression ladder

```text
domain source -> native/reference generators -> generated residual O3
              -> domain dynamics -> whole readout -> causal partial order
```

Inference is not reversed from matching scalar readouts to source identity.

## Atomic bridge

The native generator is a one-dimensional soft-Coulomb Hamiltonian with the
registered nuclear charge and reduced mass. The severing projection retains
kinetic propagation and removes the attractive relational potential. The
candidate is exactly that native-minus-reference potential. Its mismatch is
the first periodic grid translation satisfying the overlap rule. Whole
formation is final probability within the registered local window.

## Molecular bridge

At each fresh cc-pVTZ geometry, E010 constructs the complete `H4+` Hamiltonian
and the direct sum of four matched isolated-centre Hamiltonians. Separate FCI
energies define the native and reference landscapes; their pointwise residual
is the generated O3 candidate. The mismatch is the first cyclic translation of
the centered residual along the `a` grid satisfying the overlap rule. Seeded
Metropolis dynamics use native, reference, mismatched, or reconstructed
landscapes. Distance is measured to the complete set of symmetry-equivalent
native minima.

## Cellular bridge

The native bilinear joint gates and their pointwise-minimal local-preserving
inclusion-exclusion gates define native and reference operators. Their
difference is the generated distributed candidate. A separate preregistered
native calibration lineage selects the first time translation satisfying the
overlap rule without using survival. Held-out cohorts then execute native,
joint-erased, time-shifted, and timely-reinjected conditions.

## Provenance and execution lock

`--validate-registration` checks schemas and registered hashes without running
any target engine. `--execute` requires a receipt containing the registration
tag, full commit, GitHub release URL, and Zenodo DOI. The result directory must
not already exist. Molecular energies are checkpointed only inside the new
result directory after the lock is satisfied; interrupted execution may resume
from that checkpoint, but decision code and target definitions cannot change.
