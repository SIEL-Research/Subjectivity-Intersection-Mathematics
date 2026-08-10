# E010 technical specification

## Frozen target

`target_registry.json` fixes rectangular `H4+`, charge `+1`, spin `1`, and
three basis profiles. Centre order is bottom-left, bottom-right, top-right,
top-left. The registered single-edge intervention deletes edge `(0,1)`.

The two-dimensional grid is `a,b = 0.7, 0.8, ..., 2.5 angstrom`. The same
`(6.0, 6.0)` geometry is the dissociation reference for every profile.

## Hamiltonian construction

All one- and two-electron integrals are transformed into a symmetric
orthonormal basis. Atomic projectors are defined from basis-function centre
labels. Each isolated hydrogen Hamiltonian is calculated in the identical
basis family, orthonormalised within the isolated atom, and embedded into the
corresponding molecular atomic block.

The exact molecular-minus-isolated difference is decomposed into:

1. `one_electron_cross`;
2. `cross_eri`;
3. `other_nucleus_local`;
4. `nuclear_repulsion`; and
5. `local_deformation`.

FCI energies and one-particle density matrices are used for the three-electron
target. No experimental geometry or target energy is loaded.

## Registered modes

- `full`: all five sectors present;
- `one_electron_cross_deleted`: the entire first sector removed;
- `without_edge_01`: only the physical one-electron edge `(0,1)` removed;
- `isolated`: all five sectors removed.

## Frozen gates

All profiles must satisfy every gate for the complete positive decision:

1. exact five-sector reconstruction below `1e-10`;
2. finite full binding depth above `0.005 Eh` with a grid-interior minimum;
3. isolated energy range below `1e-10 Eh`;
4. deletion of the full one-electron cross sector removes at least 90% of the
   full binding depth;
5. edge deletion displaces the two-dimensional minimum by at least `0.20 A`;
6. edge deletion at the full minimum changes the population of every centre by
   at least `1e-4` electron;
7. transformed energies and carrier norms agree within `1e-8`;
8. in the one-electron Hamiltonian eigenbasis, the naive off-diagonal norm is
   below `1e-9` while the complete one-electron carrier norm exceeds `0.1`;
9. residual-sector Shapley values sum to the residual signal within `1e-10 Eh`.

## Outcome classes

- `COMPLETE_MOLECULAR_CARRIER_TRANSFER_SUPPORTED`: every gate passes in every
  basis profile.
- `ALGEBRAIC_CARRIER_ONLY_CAUSAL_TRANSFER_NOT_SUPPORTED`: reconstruction,
  complete deletion, and representation gates pass, but at least one binding,
  removal, geometry, population, or Shapley gate fails.
- `COMPLETE_MOLECULAR_CARRIER_TRANSFER_NOT_SUPPORTED`: an algebraic,
  complete-deletion, or representation gate fails.
- `PROVENANCE_FAILURE`: a frozen file, target registry, receipt, schema, or
  output-state check fails; scientific execution stops.

No result may be dropped, and no threshold may be changed after registration.

## Registration receipt

Scientific execution requires a JSON document outside the registered package:

```json
{
  "schema": "siel-e010-registration-receipt-v1",
  "tag": "e010-preregistration-v1.0.0",
  "commit": "40 lowercase hexadecimal characters",
  "release_url": "https://github.com/.../releases/tag/e010-preregistration-v1.0.0",
  "doi": "10.5281/zenodo.<digits>"
}
```

The runner validates and copies this receipt into the result summary. It does
not contact GitHub or Zenodo during execution.
