# Experiment 007C Technical Specification

## Inputs

The runner consumes only:

- the frozen Experiment 007A preregistration and result summary;
- the frozen Experiment 007B preregistration, registry, canonical primitive table, typed-composition table, and result summary;
- four exact D12RG files at commit `12759beb5c6acb41b83597dfb77b74cd576d5066`; and
- the preregistered `comparison_contract.json`.

Every input is checked against a registered SHA-256 digest before comparison.

## Native signatures

The D12RG native signature is a total unital rational algebra of linear endomorphisms on one seven-dimensional carrier, with an order-12 generator, reciprocal involution, cyclotomic projectors, invariant character, and marked two-way readout identities.

The SIM native signature is the heterogeneous typed action category printed by Experiment 007B. Composition is permitted exactly where one primitive output type occurs in the next primitive input signature. Auxiliary inputs are not silently frozen into constants.

## Role eligibility

A primitive is a parameter-free unary endomorphism only when it has exactly one input and its output type equals that input type. This condition is required for global generator, involution, and projector roles.

Normalization and reconstruction roles require parameter-free unary maps with the exact registered source and target types. A valid pair must satisfy both registered composition identities. String similarity between operation names is never inspected.

## Enumerated maps

For each D12RG marked role, the runner filters all SIM primitives by the role constraints. It then takes the Cartesian product of eligible sets, rejects non-injective assignments where the contract requires distinct roles, and tests the exact registered identities.

The resulting counts and surviving assignments are written to `admissible_maps.csv` and `summary.json`.

## Complete algebra test

The test requires all of the following:

- one common scalar carrier;
- all compared actions are linear endomorphisms of that carrier;
- a total closed product;
- identity;
- associativity and commutativity;
- one generator of exact order 12;
- reciprocal involution; and
- seven-dimensional algebra rank.

Failure of any condition rejects complete algebra isomorphism.

## Marked-readout test

The test requires eligible mappings for `Pi_adm`, `N`, and `R`, both readout identities, and a commuting typed route to the SIM mediation/self-re-entry structure. Missing roles are failures, not open slots for interpretation.

## Generic test

The generic level requires either:

- a source-defined global involution acting on the compared carrier; or
- one source-defined scalar or row invariant under all compared SIM actions.

Pair-specific permutations, cross-pair substitution, erasure, and counterfactual differences are not global involutions or traces.

## Controls

Count/dimension controls enumerate combinatorial injections after markings are removed. Direction and marking ablations repeat role filtering after deleting only the registered constraint named by the control. They cannot change the primary decision.

## Outputs

- `summary.json`
- `admissible_maps.csv`
- `signature_comparison.csv`
- `controls.csv`
- `RESULT.md`
- `output_manifest.json`

All outputs are deterministic for the frozen inputs.
