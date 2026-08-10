# Experiment 010 — Complete Molecular Carrier Transfer

## Public question

Can the complete molecular carrier developed in private MOL-001 through
MOL-010 exploration transfer, without target execution during registration,
to an unseen four-centre, three-electron molecular system?

The target is rectangular `H4+`, evaluated independently in STO-3G, 6-31G,
and cc-pVDZ. It was not executed during the MOL exploration or while this
registration package was constructed.

The constitutive claim is:

> A molecule is not first an object that then possesses bonds. It is
> constituted as one molecular whole when the relation absent from matched
> isolated atoms acts back into local electronic states, forces, geometry,
> and subsequent relation formation.

## Registered carrier

For geometry `R`,

```text
C_complete(R) = H_H4+(R) - H_four_isolated_H_centres_in_the_same_basis.
```

The exact difference is decomposed into five frozen sectors: one-electron
cross-centre action, cross-centre electron repulsion, other-nucleus action in
local atomic blocks, nuclear repulsion, and local deformation relative to the
isolated-atom reference.

## Registration state

`PREREGISTERED_NOT_EXECUTED`

This state becomes effective only after the registration commit, tag and
GitHub Release `e010-preregistration-v1.0.0`, and its DOI are public and
verified. Before that event only source-hash validation, syntax checks, and
target-free unit tests are permitted.

The runner requires a post-release registration receipt for scientific
execution. The receipt is recorded with all result artifacts.

## Target-free validation

```bash
python3 experiments/010_complete_molecular_carrier_transfer/run.py \
  --validate-registration

python3 -m unittest discover \
  -s experiments/010_complete_molecular_carrier_transfer/tests -v
```

Neither command evaluates an `H4+` integral, energy, population, or geometry.

## Single execution after the first DOI

```bash
python3 experiments/010_complete_molecular_carrier_transfer/run.py \
  --execute \
  --registration-receipt /path/to/e010_registration_receipt.json
```

The complete result, including unsupported and mixed outcomes, is then
published separately as `e010-results-v1.0.0` with a second DOI.

## Boundary

E010 tests prospective transfer of a constitutive, counterfactual standpoint
inside standard finite-basis quantum chemistry. A positive result would not
discover a new force or show that conventional quantum chemistry cannot make
the same numerical predictions. The distinctive claim concerns what relation
must be removed while leaving atomic centres present for the molecule as one
whole to cease being constituted.
