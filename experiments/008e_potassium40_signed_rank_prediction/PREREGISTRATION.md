# Preregistration: Experiment 008E

## Title

K-40 prediction from a signed rank-separated potassium connection

## Status

PREREGISTERED - NOT SEARCHED FOR BENCHMARK - NOT EXECUTED

This status becomes effective only after the registration commit, tag, public
GitHub Release, and DOI are verified against the frozen prediction hash.

## 1. Primary question

Does the rank-separated electronic connection recovered in CP-162 generate a
correct numerical second-order hyperfine correction for the previously unused
K-40 nuclear standpoint?

## 2. Frozen target

The primary endpoint is the complete leading `M1-M1 + M1-E2` correction

`delta A(P_1/2; K-40)`

for the lowest neutral-potassium `4P` fine-structure pair, in kHz.

Secondary endpoints are `delta A(P_3/2; K-40)`,
`delta B(P_3/2; K-40)`, and the corresponding generated ratios to K-39 and
K-41.

## 3. Construction disclosure

E008D opened the K-39 and K-41 correction values. CP-162 used those values only
after deriving an electronic rank map and localized the E008D residual. E008E
therefore does not reuse K-39 or K-41 as a nominally new target.

K-40 was selected because it shares the potassium electronic relation while
introducing an unused nuclear readout with `I=4`, negative magnetic moment,
and negative quadrupole moment. No numerical K-40 second-order correction was
searched or opened before this prediction.

## 4. Frozen inputs

- `I = 4`.
- `mu = -1.29797(3) mu_N`.
- `Q = -0.0750(8) b`.
- `T1 = -12.6 MHz/mu_N`.
- `T2 = -103 MHz/b`.
- `Delta E_fs = 57.600 cm^-1`.

The K-40 quadrupole moment follows the cited primary paper's explicit
`-75.0(8) mb`. The tenfold larger secondary-table transcription is recorded
and rejected in the contamination ledger.

## 5. Frozen prediction

The exact numerical prediction, propagated input envelope, secondary
predictions, and generated isotope ratios are frozen in
`prediction_before_benchmark.json`. That file's SHA-256 is the registration
identity.

Primary prediction:

`delta A(P_1/2; K-40) = 0.008107082333170607 kHz`,

with the bounded input envelope

`[0.007968190838682242, 0.008247506485579788] kHz`.

Secondary central predictions:

- `delta A(P_3/2; K-40) = 0.00015736281192138904 kHz`;
- `delta B(P_3/2; K-40) = 0.05226060942263781 kHz`;
- `delta A(P_1/2; K-40) / delta A(P_1/2; K-39) = 1.13365063363239`;
- `delta A(P_1/2; K-40) / delta A(P_1/2; K-41) = 1.8445646656413626`.

No free fitted parameter is allowed.

## 6. Benchmark search and decision rule

The benchmark search is forbidden until the public registration DOI resolves.
After registration, follow `benchmark_search_protocol.json` exactly.

For an eligible independent benchmark interval `B` and registered prediction
envelope `P`:

- `K40_PRIMARY_PREDICTION_SUPPORTED` if `P` and `B` overlap;
- `K40_PRIMARY_PREDICTION_STRONG_MATCH` is additionally recorded if the
  benchmark central value lies inside `P`;
- `K40_PRIMARY_PREDICTION_NOT_SUPPORTED` if they do not overlap;
- `OPEN_NOVEL_PREDICTION_NO_INDEPENDENT_BENCHMARK` if no eligible source
  exists; and
- `PROVENANCE_FAILURE` for source, independence, schema, unit, target, or hash
  failure.

No replacement isotope, state, observable, or same-source reconstruction is
allowed after registration.

## 7. Registration order

1. Validate the target-free package and deterministic regeneration.
2. Commit and push the complete package without benchmark values.
3. Create and verify tag `e008e-preregistration-v1.0.0`.
4. Create the public GitHub Release and DOI.
5. Verify commit, tag, Release, DOI, manifest hashes, and prediction hash.
6. Only then execute the frozen benchmark search protocol.
7. Record all candidates and exclusions before extracting a value.
8. Execute the registered evaluator once if an eligible benchmark exists.
