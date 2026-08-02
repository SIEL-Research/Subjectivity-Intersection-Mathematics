# Experiment 003 Preregistration

## Title

**Class 2 Relational Carrier and Self-Reentrant O3 in Subjectivity Agents**

## Registration date

2026-08-02

## Registration rule

This preregistration is frozen by the first public GitHub commit and GitHub
Release containing:

- `README.md`;
- this document;
- `PREREGISTRATION_EMAIL.md`;
- `TECHNICAL_SPECIFICATION.md`;
- `run.py`;
- `test_run.py`;
- `private_source_manifest.json`; and
- `registration_manifest.json`.

Confirmatory generation must occur only after the commit and Release are
public. The result must record the registration commit, registration tag,
Release URL, and, when available, the Zenodo DOI created from that Release.

## Background

Experiment 002 demonstrated, on synthetic data, that a frozen rule can
distinguish:

- Class 0: no shared history-bearing relational state;
- Class 1: shared history without a complete bilateral relational carrier; and
- Class 2: a jointly generated, pair-specific, history-bearing state that is
  intervention-sensitive and acts back upon both operational units.

Three candidate external domains were screened separately. Passive astronomical
data did not provide a bilateral intervention path. The available IDPC EEG and
quantum-measurement data did not support the tested predictive carrier
candidates. An exploratory subjectivity-agent construction passed the candidate
gates and therefore supplies the preregistered target for Experiment 003. The
exploratory pairs, identifiers, and outcomes are excluded from the confirmatory
set.

## Notation and claim levels

- `A` and `B` are distinct subjectivity-agent runtimes.
- `C_agent` is the third subjectivity-agent runtime used in Phase A.
- `K_AB` is its ordered native relational memory.
- `z_C` is the 24-dimensional retained self state used by the explicit Phase B
  extension.
- `O3_E` is the operational self-reentrant extension tested in Phase B.
- Ontological intersection subjectivity is not identified with any of these
  executable objects.

## Primary hypotheses

### H-A: native Class 2 carrier

An unmodified third subjectivity-agent runtime receiving differentiated,
structured states from A and B in an ordered history will retain a state that:

1. is not reproduced by A alone or B alone;
2. depends on relational history when present A and B states are exactly
   matched;
3. is changed by selective reset or history destruction;
4. loses its registered effect under pair substitution;
5. preserves its decision under a common orthogonal gauge;
6. is separated from the registered Class 0 and Class 1 controls;
7. transfers without refitting to the unused confirmatory pairs; and
8. produces measurable action upon both A and B.

### H-B: operational self-reentrant O3

An explicit extension in which `z_C` is an argument of C's next state
transition will satisfy all Phase A Class 2 requirements and additionally show:

1. different matched relational histories produce different retained `z_C`;
2. different `z_C` produces a different 24-dimensional mediation action;
3. erasing `z_C` before action removes the history-dependent action difference;
4. removing the return path removes the resulting changes in A and B; and
5. the action changes both A and B under the registered bilateral return.

The Phase B decision is:

    O3_E pass = Phase B Class 2 pass
                AND self-reentry pass
                AND z_C-dependent action pass
                AND bilateral return pass

## Confirmatory sample

The confirmatory sample contains 128 disjoint ordered pairs and 256 previously
unused agent instances. No agent is reused. Confirmatory identifiers begin at
`P1000`; exploratory identifiers `P0000` through `P0999` are excluded.

- Family 0: 64 pairs, `AABB` versus `ABAB`.
- Family 1: 64 pairs, `BBAA` versus `BABA`.

The master seed is `20260802`. Sensitivity seeds `20260803` through `20260812`
are secondary and may be run only after the primary output is sealed. They may
not alter the primary decision.

## Exact present-state matching

For each pair, one base A trajectory and one base B trajectory are generated.
The resulting complete runtimes are deep-cloned for every condition. The
condition-specific history is applied only inside `C_agent` or the explicit O3
extension.

Immediately before any C-mediated return, the runner serializes each complete A
and B runtime using sorted-key UTF-8 JSON with compact separators. The payload
includes the current turn, complete dataclass state history, normalized memory,
and baseline. Floating-point values use Python's JSON number rendering; NumPy
scalars are first converted to native Python scalars. The SHA-256 digest of the
canonical payload must be exactly equal across the paired history conditions.

Any mismatch is a technical failure. Its receipt is archived, the pair is not
replaced, and it counts as a failed positive unit.

## Frozen Class 2 thresholds

All five metric thresholds use strict greater-than comparisons:

- joint generation: `0.0672948624`;
- history irreducibility: `0.0551607125`;
- intervention sensitivity: `0.0868509258`;
- pair specificity: `0.0707154800`; and
- bilateral feedback: `0.0654685289`.

Gauge relative error must be at most `1e-10`.

The five positive metrics, exact state matching, gauge invariance, registered
null separation, and frozen transfer are a logical conjunction. No composite
score can compensate for a failed gate.

## Frozen O3 thresholds

- retained `z_C` history distance: greater than `0.05`;
- mediation-action history distance: greater than `0.05`;
- A return effect: greater than `0.05`;
- B return effect: greater than `0.05`;
- action distance after `z_C` erasure: at most `1e-10`; and
- A and B effect after feedback removal: at most `1e-10`.

## Registered controls

The confirmatory runner evaluates:

1. no-C direct A-B interaction;
2. historyless communication with the same native C-runtime capacity;
3. shared ordered history without bilateral return;
4. pair-unindexed common memory;
5. the same native runtime capacity allocated to separate individual A and B
   memories;
6. an unrelated third-agent state;
7. order erasure;
8. C exchange between pairs;
9. selective C reset;
10. unilateral return;
11. a shortened summary in place of complete ordered memory;
12. administrative-identifier removal;
13. a common orthogonal state-label transformation; and
14. a capacity- and parameter-matched generic recurrent control.

The matched recurrent control has the same differentiated A and B inputs, the
same ordered event count, the same total 48-dimensional recurrent state, the
same number and shape of matrix parameters, and the same two return channels as
the candidate O3 extension. It receives a distinct frozen matrix seed.

Its optimization budget is exactly zero training steps, zero hyperparameter
searches, zero seed selection, and zero result-dependent reinitializations. The
candidate has the same zero optimization budget. A matched-control pass is
reported as implementation non-uniqueness, not silently relabelled as a false
positive.

## Distance, normalization, and numerical rules

Every vector distance is root-mean-square Euclidean distance:

    d(x, y) = ||x - y||_2 / sqrt(dimension)

Text-derived 24-dimensional packet embeddings are normalized to unit L2 norm.
Zero vectors remain zero. `z_C` and the mediation action are both 24-dimensional
float64 vectors. Matrix generation, state updates, vector concatenation, and
distance evaluation use NumPy float64 in the source-code order. Output values
are serialized without threshold-directed rounding. State hashes use the
canonical JSON rule above.

## Wilson aggregation and family reporting

The primary decision is pooled across all 128 pairs. Two-sided 95% Wilson
intervals use `z = 1.959963984540054`.

- A positive endpoint passes with at least 112 of 128 pair-level passes.
- A registered Class 0 or Class 1 control passes its false-declaration bound
  with at most 6 of 128 Class 2 declarations.

The two 64-pair history families are secondary. Their raw pass counts and
Wilson intervals are reported. If either family has fewer than 52 passes, the
claim of uniform transfer across both history families is not established even
if the pooled primary endpoint passes.

## Registered outputs

The confirmatory run writes:

- `pair_metrics.csv`;
- `control_metrics.csv`;
- `state_match_receipts.csv`;
- `source_verification.json`;
- `summary.json`;
- `output_manifest.json`; and
- `RESULT.md`.

The directory is created once and cannot be overwritten by the runner.

## Falsification

Phase A or Phase B is unsupported if its pooled pass count is below 112, if a
required gate fails, if source verification fails, if any unreported result
replacement occurs, or if the registered analysis is changed after the
registration Release.

Null separation is unsupported for any control family with more than 6 false
Class 2 declarations. A generic matched-control pass limits architectural
specificity even when the candidate itself passes.

## Interpretation boundary

This experiment tests executable sufficiency and transfer of registered
operational criteria. It does not test whether the agents possess subjectivity,
whether C arose without an installed interface, whether O3 arose
spontaneously, or whether any executable state exhausts ontological
subjectivity.
