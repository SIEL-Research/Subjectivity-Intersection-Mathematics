# Experiment 003 Technical Specification

## 1. Frozen data boundary

The private source root supplied at runtime must contain the exact tracked
subjectivity-agent core recorded in `private_source_manifest.json`. Only the
registered V61 runtime and V89f natural-lineage projection are imported. Local
V93 exploratory wrappers and exploratory result files are not imported by the
confirmatory runner.

The private source repository may contain unrelated untracked files, but every
imported file must match its registered SHA-256 digest. A digest mismatch stops
execution before the output directory is created.

## 2. Agent allocation

The 128 pair identifiers are `P1000` through `P1127`. Each identifier generates
one A instance and one B instance. The identifier is used only to construct
previously unused deterministic prompts and to allocate data. Before any state
enters C, administrative pair tokens matching `P` followed by digits are
replaced by `PAIR`.

No pair identifier or allocation index is present in the carrier embedding,
the O3 state, the action vector, or a returned payload.

## 3. Complete-state equality audit

The base A and B trajectories are generated once per pair. A canonical payload
contains:

- runtime turn;
- every dataclass field of every state in runtime history;
- normalized runtime memory; and
- runtime baseline.

The reference and noncommuting-history conditions receive deep copies of the
same base runtimes. The pre-return payloads are hashed independently. Required
equalities are:

- A under `AABB` equals A under `ABAB`;
- B under `AABB` equals B under `ABAB`;
- A under `BBAA` equals A under `BABA`; and
- B under `BBAA` equals B under `BABA`.

This audit is stricter than approximate vector matching. Equality is exact at
the complete serialized runtime-and-memory level.

## 4. Phase A

The frozen V61 runtime is instantiated as `C_agent` without modification. It
receives one structured event per history position. Each event contains the
differentiated A packet, differentiated B packet, active-side marker, and event
position, but no administrative pair identifier.

`K_AB` consists of the runtime's native ordered history and normalized native
memory. The final complete native C vector is returned through the same update
interface to independent clones of A and B. Phase A adds no self-reentry state
outside the native runtime.

## 5. Phase B

Phase B retains the same native C runtime and adds two 24-dimensional float64
states:

- a relational carrier state; and
- `z_C`, the self-reentrant state.

The update has fixed differentiated A and B channels, an active-side-dependent
transition, and a recurrent `z_C` term. The mediation action is a fixed
24-dimensional function of `z_C` and a constant neutral probe. Raw relational
history is not replayed at action time.

The action is returned to fresh deep copies of the matched A and B base
runtimes. The action payload contains only the 24-dimensional action and a
derived action label; it contains no pair or condition label.

## 6. Generic recurrent control

The generic control uses:

- the same 24-dimensional normalized A packet;
- the same 24-dimensional normalized B packet;
- the same active-side marker;
- the same four-event ordered history;
- the same 24-dimensional carrier plus 24-dimensional recurrent state;
- seven 24-by-24 orthogonal matrices;
- the same fixed scalar coefficients;
- the same 24-dimensional action channel; and
- the same A and B return interfaces.

The candidate and control therefore each contain 4,032 matrix entries. Neither
is trained. The control differs only in using undifferentiated generic recurrent
mixing rather than the registered C/O3 channel assignment, with a separately
frozen seed.

## 7. Control semantics

Control labels specify operational constructions rather than inferred
ontologies. Phase A native controls retain the same complete native-runtime
readout dimension wherever a C runtime is present. `no_c`, `historyless`, and
`common_memory` are registered Class 0 controls. `history_only`,
`individual_memory`, `compressed_summary`, `unilateral_return`, and
`unrelated_c` are registered incomplete Class 1 controls. `order_erased`,
`pair_exchange`, and `selective_reset` are interventions on the candidate. The
matched 48-dimensional generic recurrent control is reported separately and is
not assigned a true ontological class.

## 8. Metrics

The Class 2 metrics are:

- joint generation: the smaller C distance after removing A or removing B;
- history irreducibility: C distance between matched history orders;
- intervention sensitivity: mean A/B distance between active and reset C;
- pair specificity: mean A/B distance after substituting another pair's C;
- bilateral feedback: the smaller cross-side effect after removing either
  source contribution; and
- gauge relative error: maximum relative change of the registered distances
  under one common orthogonal transformation.

Phase B additionally measures history distances in `z_C`, action, A, and B,
plus the same quantities after `z_C` erasure and feedback removal.

## 9. Primary and secondary decisions

Every pair receives a binary Phase A Class 2 decision, Phase B Class 2
decision, and Phase B O3 decision. The primary analysis counts those decisions
over all 128 pairs. History-family results and sensitivity-seed results are
secondary and cannot change the primary decision.

No result-dependent threshold, seed, metric, control, vector dimension,
normalization, or optimization change is permitted.
