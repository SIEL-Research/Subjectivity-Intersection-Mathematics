# Experiment 013 preregistration

## Question

Can a common domain-prior residual rule generate the operational O3 candidate
in atomic, molecular, and cellular models, such that its complete removal and
structurally mismatched return impair whole-formation while correct return
restores it?

## Frozen generation rule

Before outcome execution, each domain bridge fixes its differentiated local
terms, native generator `G_D`, admissible transformations, and whole-formation
readout. The candidate is then generated, not hand-selected:

```text
R*_D = P_loc,D(G_D)
C*_D = G_D - R*_D
```

`P_loc,D` is the maximal local-preserving severing projection specified in the
technical specification. Complete removal must reconstruct `R*_D`; correct
return must reconstruct `G_D` to the frozen tolerance.

## Structurally generated mismatch

Starting from the smallest non-identity admissible isometry, the runner chooses
the first transformation whose centered O3-candidate self-overlap is at most
`0.25`. Constant coordinate or energy offsets are removed before overlap.
No whole-formation outcome is inspected when the mismatch is chosen.

## Fresh targets

- Atomic: tritium and a helium-3 hydrogenic ion, introducing both a new reduced
  mass and a new nuclear charge relative to E012.
- Molecular: a previously unexecuted `H4+` cc-pVTZ line at `b = 1.0 Å`, with
  `a = 1.3...2.5 Å`. Full and isolated-centre FCI generators are computed only
  after registration.
- Cellular: a fresh native calibration seed used only to generate the time
  isometry, followed by four disjoint 16-lineage held-out cohorts.

## Primary causal partial order

Every held-out realization must satisfy all four inequalities:

```text
intact > removed
intact > mismatched return
correct return > removed
correct return > mismatched return
```

The absolute gates remain: intact and correct-return scores at least `0.80`,
removed and mismatched-return scores at most `0.50`, and correct return at
least `0.25` above both controls. The minimum high score must strictly exceed
the maximum low score across all realizations.

The ordering between removal and mismatched return is not a primary claim. An
unrestricted all-pairwise leave-one-domain-out diagnostic is reported but
cannot change the primary decision.

## Cross-domain decision

`DOMAIN_PRIOR_O3_GENERATION_TRANSFER_SUPPORTED` requires:

1. exact reference/candidate removal and reconstruction in every domain;
2. structurally selected mismatch with overlap at most `0.25`;
3. every realization passing the five absolute gates;
4. the four-edge causal partial order passing for each held-out domain;
5. positive threshold-free separation; and
6. no shared scalar entering domain dynamics.

Any failure yields `DOMAIN_PRIOR_O3_GENERATION_TRANSFER_NOT_SUPPORTED`, with
all component outcomes preserved.

## Evidential boundary

A positive result supports prospective transfer of an O3
generation-and-intervention grammar across three reduced domain models. It does
not establish a common physical O3 substance, a microscopic atom-to-cell law,
or laboratory confirmation in natural atoms, molecules, or living cells.
