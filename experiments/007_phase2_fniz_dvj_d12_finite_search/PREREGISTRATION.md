# Preregistration: Experiment 007 Phase 2

## Title

Complete Finite Search for a Constructed FNIZ-DVJ-D12 Bridge Rule

## Registration status

Preregistered before execution of the frozen Phase 2 runner.

## Background

Experiment 007 Phase 1 audited the frozen D12RG Riemann and Advaita sources before any connector search. The audit completed with the classification `INCOMPLETE_SOURCE_DEFINITION`.

The source-defined signed-FNIZ, DVJ, and D12 components passed their registered checks. However, no executable source mapping from FNIZ operation history through DVJ holonomy to a D12 deck action was found.

The unrestricted four-operation assignment contained 20,736 rules. Treating subtraction as the inverse action of addition and division as the inverse action of multiplication reduced the conditional family to 144 rules. Lagrange's theorem did not reduce that family, and no rule was selected.

Phase 2 searches exactly those 144 rules.

## Research question

Does the complete frozen family of 144 source-compatible operation-to-deck assignments contain a unique constructed rule or a unique equivalence class that maximises a preregistered set of nondegeneracy and moving-projector criteria?

## Primary object and claim boundary

The searched object is a connector component for the composite operational candidate `K^E_FNIZ-DVJ-D12`.

Phase 2 does not establish a Class 2 relational carrier. It does not establish O3. It does not test relational temporal nonseparability, recursive self-re-entry, cross-pair specificity, or bilateral downstream effects. Those are reserved for a separately preregistered Phase 3 using untouched conditions and an equally expressive factorised null.

Any object selected here is a constructed bridge hypothesis. Search success cannot convert it into a source-derived theorem.

## Frozen candidate family and error-control family

The candidate family is the complete 144-row table published by Phase 1:

- addition is assigned `a` in C12;
- subtraction is assigned `-a mod 12`;
- multiplication is assigned `m` in C12;
- division is assigned `-m mod 12`;
- `(a,m)` ranges over every ordered pair in `C12 x C12`.

This complete family of 144 candidates is also the Phase 2 error-control family. No candidate is removed before scoring. Phase 2 uses an exhaustive deterministic ordering rather than p-values; family control is achieved by evaluating every member, publishing every score, preserving all ties, and forbidding post hoc restriction.

## Frozen source authorities

### Phase 1 public result

- commit: `61bfbb763dfd41b15264b8a7dd3f081783ce3c2d`
- DOI: `10.5281/zenodo.21794739`
- candidate table SHA-256: `a1f250c58889cc4cc200c1fe0cfa32f36111db72d9fc8d57157a6b5cbedfaf65`
- Phase 1 summary SHA-256: `d6b2b194a129cf0e7ab0688d0219aefe59221a8d12bbd54b821e1be6a3a9aa81`

### D12RG Riemann source

- repository: `https://gitlab.com/d12rg/d12rg-riemann.git`
- commit: `12759beb5c6acb41b83597dfb77b74cd576d5066`

The required source-file hashes are fixed in `registration_manifest.json`.

## Frozen operation mapping

For one candidate `(a,m)`, the four deck steps are:

- addition: `a`;
- subtraction: `-a mod 12`;
- multiplication: `m`;
- division: `-m mod 12`.

The operation labels and derived inverse relations are never permuted during scoring.

DVJ direction is calibrated but not used to break candidate ties:

- addition and multiplication use the forward DVJ transfer;
- subtraction and division use the reciprocal DVJ transfer.

This direction convention is a constructed Phase 2 convention, not a source-derived result.

## Frozen D12 source object

Each operation acts on the frozen Paper 5.3 admissible mode set through the source-defined `shift_modes` action. Candidate scores are derived from the geometry of the four translated mode sets and from cumulative paths on C12.

## Development words

The following four balanced words are fixed before execution. Each contains addition, subtraction, multiplication, and division exactly three times:

1. `+ * - / + * - / + * - /`
2. `+ + + * * * - - - / / /`
3. `+ * / - * - + / - / + *`
4. `+ / * - / + - * * - + /`

These words are search objects only. They cannot be reused as Phase 3 confirmatory histories.

## Deterministic candidate metrics

For every candidate, the runner computes:

1. `full_group`: whether `a` and `m` generate all of C12;
2. `four_distinct_steps`: whether the four labelled operations have four distinct deck steps;
3. `translated_mode_union_size`: the cardinality of the union of the four translated Paper 5.3 mode sets;
4. `minimum_pairwise_mode_symmetric_difference`: the smallest symmetric-difference size among the six labelled operation pairs;
5. `minimum_development_path_coverage`: the smallest number of distinct cumulative C12 positions visited across the four frozen development words, including the initial position;
6. `minimum_primitive_order`: the smaller C12 order of `a` and `m`.

The metrics are structural. DVJ source checks are reported separately as calibration and contribute no candidate-specific score.

## Frozen lexicographic ranking

Candidates are ranked lexicographically in the following descending order:

1. `full_group`;
2. `four_distinct_steps`;
3. `translated_mode_union_size`;
4. `minimum_pairwise_mode_symmetric_difference`;
5. `minimum_development_path_coverage`;
6. `minimum_primitive_order`.

No weighted sum is used. A lower-priority metric cannot compensate for failure of a higher-priority metric.

All candidates sharing the maximum six-component score remain tied.

## Frozen equivalence relation

Two candidates `(a,m)` and `(a',m')` are equivalent when one can be obtained from the other by any combination of:

- a C12 automorphism multiplying all steps by one of the units `1, 5, 7, 11`; and
- exchange of the two primitive labels, addition and multiplication, together with exchange of their derived inverse labels.

The equivalence key is the lexicographically smallest primitive pair in that orbit.

This equivalence relation is fixed before scoring. It cannot be expanded to merge unexpected ties after execution.

## Primary classification

Exactly one classification will be emitted:

- `UNIQUE_CONSTRUCTED_RULE_SELECTED`: one candidate alone has the maximum score;
- `ONE_CONSTRUCTED_EQUIVALENCE_CLASS_SELECTED`: multiple candidates tie, but all belong to one frozen equivalence class;
- `MULTIPLE_TOP_EQUIVALENCE_CLASSES`: the maximum-score candidates occupy more than one frozen equivalence class;
- `NO_ADMISSIBLE_CANDIDATE`: no candidate passes source and provenance validation.

If one equivalence class is selected, the lexicographically smallest candidate ID in that class is recorded as a canonical computational representative. The scientific selection remains the equivalence class, not that coordinate representative.

## DVJ calibration

At the frozen spectral parameters `0.5`, `1.0`, `2.0`, and `5.0`, the runner verifies:

- nonzero forward transfer;
- reciprocal reconstruction;
- determinant-one reciprocal carrier; and
- twelve-step central-holonomy closure.

The tolerance is `1e-40`, with mpmath 1.3.0 at 80 decimal digits and DVJ roots constructed at 90 digits.

Calibration failure aborts the run. Calibration values do not rank candidates.

## Completion criteria

Phase 2 is complete only when:

1. the preregistration manifest passes;
2. the Phase 1 result files and hashes pass;
3. the Riemann source provenance and hashes pass;
4. exactly 144 Phase 1 candidates are loaded;
5. all 144 candidates receive all six metrics;
6. the frozen ranking and equivalence relation are applied without modification;
7. every candidate and score is written;
8. no tie is removed post hoc; and
9. one primary classification is emitted.

## Downstream firewall

No Phase 3 confirmatory execution may begin until the Phase 2 search result has been published as a separate immutable record.

Phase 3 must use previously untouched endpoint pairs, temporal correspondences, and histories. Confirmatory evidence must rest on consequences not guaranteed by the connector wiring: nonseparable relational residue, recursive closure, matched cross-pair substitution, bilateral downstream effects, and failure of an equally expressive factorised null and equally simple alternative mappings.

## Outputs

The runner writes:

- `summary.json`;
- `scored_candidates.csv`;
- `equivalence_classes.csv`;
- `RESULT.md`; and
- `output_manifest.json`.
