# Experiment 002 — Confirmatory Result

## Publication status

**CONFIRMED RESULT — RELEASED AFTER AUTHOR REVIEW**

## Registered question

Can a frozen, ground-truth-blinded procedure distinguish:

1. systems with no shared history-bearing state;
2. systems with a shared history-bearing state that is not a complete
   relational carrier; and
3. systems with a pair-indexed, jointly generated, history-bearing carrier
   that acts back upon both operational units?

## Preregistration

- Repository:
  `https://github.com/SIEL-Research/Subjectivity-Intersection-Mathematics`
- Registration commit:
  `6737a89e98a83d1cb43b83823de7e7d1477e436f`
- Confirmatory seed: `2026072502`
- Registered source hashes: verified before generation
- Confirmatory source changes: none

The registration commit included the design, preregistration document,
collaborator email, complete executable source, unit tests, acceptance
thresholds, and source hashes.

## Executed command

    python3 experiments/002_blinded_relational_carrier_discrimination/run.py \
      --mode confirmatory \
      --out-dir experiments/002_blinded_relational_carrier_discrimination/results \
      --check

The result directory did not exist before this run. The program refuses to
overwrite an existing confirmatory directory.

## Computed result

Status: **SUPPORTED WITHIN THE REGISTERED SYNTHETIC BENCHMARK**

The run generated:

- 160 opaque datasets;
- 491,520 observed time-series rows;
- 640 observation-map-specific decisions; and
- 160 final blinded class predictions.

All registered primary acceptance conditions passed.

| Transfer | Balanced accuracy | Class 0 recall | Class 1 recall | Class 2 recall | False Class 2 rate |
|---|---:|---:|---:|---:|---:|
| T1 — unseen histories | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| T2 — unseen pairings | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| T3 — unseen operational units and pairs | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

Additional registered targets:

| Target | Required | Observed | Result |
|---|---:|---:|---|
| Overall false Class 2 rate | at most 0.10 | 0.000 | PASS |
| G2-P Class 2 recall | at least 0.80 | 1.000 | PASS |
| G2-M second-mechanism recall | at least 0.70 | 1.000 | PASS |
| Gauge consistency | at least 0.95 | 1.000 | PASS |

## Confusion audit

The blinded predictions produced no class error:

| Transfer | True 0 -> Predicted 0 | True 1 -> Predicted 1 | True 2 -> Predicted 2 |
|---|---:|---:|---:|
| T1 | 40 | 8 | 16 |
| T2 | 40 | 8 | 16 |
| T3 | 20 | 4 | 8 |

Every registered generator family was classified correctly in all 20 of its
datasets:

- `G0-I`, `G0-C`, `G0-D`, `G0-X`, and `G0-H` -> Class 0;
- `G1-F` -> Class 1;
- `G2-P` and `G2-M` -> Class 2.

## Full-adder boundary

The recurrent full-adder behaved exactly as the registered Class 1 boundary.
Across all 20 `G1-F` datasets:

- joint generation passed: 20/20;
- history dependence passed: 20/20;
- selective reset passed: 20/20;
- pair specificity passed: 0/20;
- bilateral feedback passed: 0/20; and
- final Class 2 declarations: 0/20.

The result therefore preserved the distinction between a shared
history-bearing state and a complete pair-indexed relational carrier.

## Class 2 gate audit

Across all 40 true Class 2 datasets, including the independently constructed
G2-M family:

- all seven registered evidence gates passed: 40/40;
- bilateral feedback passed: 40/40; and
- Class 2 was declared: 40/40.

The minimum observed Class 2 values remained well beyond the frozen
thresholds:

- history mismatch: at least `0.898`, threshold `0.58`;
- bilateral A/B history mismatch: at least `0.894`, threshold `0.58`;
- reset margin: at least `0.729`, threshold `0.25`;
- partner-substitution margin: at least `0.716`, threshold `0.25`;
- remove-A margin: at least `0.690`, threshold `0.25`;
- remove-B margin: at least `0.700`, threshold `0.25`; and
- gauge consistency: `1.000`, threshold `0.95`.

The classification was therefore not produced by values lying immediately on
the registered decision boundaries.

## Procedural blindness and integrity

The executable sequence was:

1. verify the registered source hashes;
2. generate the observed table and separate ground truth;
3. analyse the observed table without passing ground truth;
4. write and hash the predictions;
5. give the scorer access to ground truth; and
6. evaluate the frozen acceptance targets.

The prediction file was hashed before unblinding:

`2ec96b6c091bf21a15bdc12205b67a7e780d7878ca1708b9599646c074ad6e45`

Independent post-run hashing reproduced the same digest.

Principal output hashes:

- observed table:
  `f2c414258c3ae56209527bdee3118c16b1f7d82f78fbffa5af5d104a31e76fd8`
- sealed ground truth:
  `95d687e78ffc714cc76594f081bdc8d33f4843d58ff39822ad245f8d8e4131e0`
- predictions:
  `2ec96b6c091bf21a15bdc12205b67a7e780d7878ca1708b9599646c074ad6e45`
- gauge decisions:
  `b783137681c24e57a8b0e5a0c451511fa696ad28ef83136037103ae9b0403267`

## Interpretation

Experiment 002 passed its methodological objective. Within the registered
synthetic bank, the frozen procedure distinguished:

- ordinary unit-specific, directly coupled, common-driver, instantaneous, and
  finite-window alternatives;
- an incomplete shared history state; and
- two independently constructed complete relational-carrier mechanisms.

The G2-M transfer is the most important protection against a
single-generator lookup result: the unchanged decision rules transferred from
the permutation carrier to a finite-matrix carrier over GF(3).

The perfect score must be interpreted at the correct level. The synthetic
families were deliberately constructed to instantiate or violate the
registered carrier conditions with measurable separation. The result
validates the executable gate logic and its resistance to the registered
noise, missingness, relabelling, pair, and transfer controls. It is not an
estimate of performance on naturally occurring data.

## Claim boundary

This result does not establish:

- a relational carrier in a stellar observation system;
- a relational carrier in EEG measurements;
- a relational carrier in a quantum preparation-and-measurement context;
- a relational carrier between subjectivity agents;
- identity between an operational carrier and subjectivity;
- ontological irreducibility; or
- uniqueness beyond the registered synthetic alternatives.

It establishes that the registered discrimination method is ready to be
tested in a separately defined and preregistered external system.
