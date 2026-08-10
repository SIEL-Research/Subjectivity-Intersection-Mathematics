# Preregistration: Experiment 010

## Title

Prospective Four-Centre Transfer of the Complete Molecular Carrier

## Status

PREREGISTERED — TARGET NOT EXECUTED

This status becomes effective only after the public registration commit, tag,
GitHub Release `e010-preregistration-v1.0.0`, and preregistration DOI are
verified. Source validation and target-free unit tests may run before then.
No `H4+` target integral, energy, density, population, geometry surface, or
decision may be evaluated before public registration is complete.

## 1. Primary question

Does the complete molecular carrier derived in MOL-001 through MOL-010
prospectively transfer from explored two- and three-centre molecules to an
unexecuted four-centre, three-electron system across three basis families?

## 2. Design disclosure

E010 is result-informed by private MOL-001 through MOL-010 exploration. Those
experiments used `H2`, `H2+`, `HeH+`, `LiH`, `BeH+`, `He2`, and `H3+`. They
established the operational decomposition, thresholds, intervention logic,
and expected qualitative direction before E010 was constructed.

The registered target, rectangular `H4+`, was not executed in those
experiments and has not been executed while this package was prepared. E010 is
a prospective transfer test of the frozen operational claim. It is not an
independent derivation of quantum chemistry and is not blind to the positive
results of the development systems.

## 3. Frozen target and computation

The target contains four hydrogen centres in a rectangle, total charge `+1`,
three electrons, and spin `1`. The width `a` and height `b` each range from
`0.7` to `2.5 angstrom` in `0.1 angstrom` steps. The fixed dissociation
reference is `(a,b)=(6.0,6.0) angstrom`.

The same target is calculated using STO-3G, 6-31G, and cc-pVDZ. FCI is used for
all registered energies and one-particle density matrices.

## 4. Frozen complete carrier

For each basis and geometry,

```text
C_complete(R) = H_H4+(R) - H_four_isolated_H_centres_in_matched_basis.
```

The isolated reference retains four physical atomic basis subspaces but
removes every molecule-induced sector. The difference is exactly reconstructed
from the five sectors fixed in `TECHNICAL_SPECIFICATION.md`.

## 5. Frozen causal interventions

1. Remove the complete carrier and test whether the energy landscape becomes
   flat.
2. Remove the entire one-electron cross-centre sector and measure the fraction
   of full binding lost.
3. Remove only one physical edge, `(0,1)`, and measure displacement of the
   two-dimensional minimum.
4. At the full minimum, compare all four local centre populations before and
   after edge deletion.
5. Rotate the full Hamiltonian, isolated reference, and physical carrier
   together into the one-electron eigenbasis and three frozen random orbital
   bases.
6. Attribute the residual binding signal after one-electron-cross deletion to
   the four remaining sectors using exact order-independent Shapley values.

## 6. Frozen decision rule

The nine numerical gates and three outcome classes are fixed in
`TECHNICAL_SPECIFICATION.md` and `target_registry.json`. The primary positive
decision requires all nine gates in all three basis profiles. A mixed causal
outcome and a full negative outcome are distinct and must both be published.

No gate can be removed, weakened, reinterpreted, or replaced after target
execution. Boundary minima, nonbinding surfaces, numerical failures, and every
profile-specific negative result remain part of the result record.

## 7. Interpretation

A positive result would support prospective transfer of the constitutive
molecular-carrier operation: the matched isolated atomic centres do not form
the registered molecular whole until the complete relation is restored, and a
single relation edge causally reorganises the whole.

It would not show that the Hamiltonian sectors are unknown to quantum
chemistry, that only Subjectivity-Intersection Mathematics can predict the
numbers, or that a new physical force exists. MOL-007 already showed that the
explored scalar closure-gain proxy is algebraically reducible to standard
features.

## 8. Two-release publication order

1. Validate source hashes and target-free unit tests only.
2. Commit and push the exact registration package to public `main`.
3. Publish and verify `e010-preregistration-v1.0.0` as the first GitHub
   Release.
4. Obtain and verify the preregistration DOI.
5. Create the registration receipt from those verified public objects.
6. Execute the registered target once into a new results directory.
7. Inspect and retain every output before interpretation or publication.
8. Commit and push the complete result artifacts separately.
9. Publish and verify `e010-results-v1.0.0` as the second GitHub Release.
10. Obtain and verify the separate result DOI.

## 9. Claim boundary

E010 tests the physical and mathematical standpoint introduced by the
Creation Principle: a molecule is constituted when the relation absent from
isolated atoms returns into and reforms its components. The computation is an
operational realization inside standard nonrelativistic finite-basis quantum
chemistry. Ontological O3, a beyond-quantum interaction, and empirical
laboratory confirmation are not established by this experiment alone.
