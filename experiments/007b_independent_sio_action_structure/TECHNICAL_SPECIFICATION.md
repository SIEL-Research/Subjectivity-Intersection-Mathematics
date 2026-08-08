# Experiment 007B Technical Specification

## Source registry

`source_action_registry.json` is the only operation-site authority. Each site declares its source path, enclosing function, required source fragments, canonical rule, ordered input types, output type, and linearity class.

The runner parses the frozen source with Python's AST, locates the named function, reconstructs its source span, and requires every registered fragment to occur. Missing, duplicated, or altered source authorities cause provenance failure.

## Canonical primitive identity

Canonical identity is the JSON serialization of:

`canonical_rule`, `input_types`, `output_type`, `linearity`, and `direction`.

All supporting sites are retained in the output inventory. The operation label is descriptive only.

## Registered type symbols

- `TRAJECTORIES`
- `STEP`
- `STATE_BUNDLE`
- `ARCHITECTURE`
- `JOINT_STATE`
- `RELATION_COMPONENT`
- `MODEL`
- `INPUT_STEP`
- `INPUT_SEQUENCE`
- `PAIR_LABELS`
- `PERMUTATION`
- `BILATERAL_LOGITS`
- `RECEIVER_PARTITION`

## Typed compositions

For actions `f: X -> Y` and `g: U -> V`, `g after f` is marked composable when `Y` occurs in the ordered input types of `g`. The table records the matching input positions. It does not assert that unused arguments have been supplied or that the composition is an endomorphism.

## Linearity classes

- `linear`: linear on the declared real product space.
- `affine`: affine but not necessarily linear.
- `nonlinear`: contains registered nonlinear dynamics.
- `discrete_routing`: a deterministic routing operation on labels or indices.

The common-carrier algebra gate requires every primitive to be a `linear` map with exactly one input type equal to its output type and the same common type for all primitives.

## Witness construction

The runner imports the frozen Experiment 006 and 006A modules after verifying all hashes. It constructs fixed arrays with three examples and state width 24.

Two state bundles are used:

1. a receiver-separated bundle on which the two extractors can overlap; and
2. a cross-receiver bundle on which receiver-directed and inclusion-exclusion extraction differ.

The recurrent witness uses fixed small real matrices and zero input. Nonlinearity is accepted when `advance(2h) != 2 advance(h)` above `1e-10` while all values remain finite.

## Mediation route

The registered route requires at least one action for each canonical rule:

- `extract_relation` or `extract_joint_synergy`;
- `erase_relation` or `substitute_relation`;
- `advance_recurrently`;
- `replace_joint_in_bundle`; and
- a subsequent relational extraction.

The route is a typed operational cycle across time indices, not an algebraic identity and not a claim that O3 is localized.

## Robustness

Each leave-one-out variant recomputes the top-level class from the remaining primitives. The predeclared addition is:

`ordered_receiver_partition: ARCHITECTURE -> RECEIVER_PARTITION`.

It is supported by the receiver partitions used in the frozen intervention and bilateral-measurement code but is excluded from the base set because it supplies type metadata rather than constructing the relational state.

## DJS audit

The runner uses a frozen checklist. It does not implement missing DJS structure. A requirement passes only when a registered source action supplies it directly. The expected scientific outcome is not preregistered; the classification follows the observed checklist.

## Outputs

- `summary.json`
- `source_operation_sites.csv`
- `canonical_primitives.csv`
- `typed_composition_table.csv`
- `robustness_variants.csv`
- `RESULT.md`
- `output_manifest.json`
