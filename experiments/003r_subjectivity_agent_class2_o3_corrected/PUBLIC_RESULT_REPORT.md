# Experiment 003R: Public Confirmatory Result Report

## Status

Experiment 003R is complete. The confirmatory execution passed the registered
primary, null-control, and two-family transfer criteria. The matched generic
recurrent control also passed at the same rate as the proposed O3
implementation. The result therefore supports the operational sufficiency and
transfer of the tested construction, but not the uniqueness or necessity of
its specific O3 channel assignment.

## Corrective history

The original Experiment 003 was preregistered before execution at
[DOI 10.5281/zenodo.21760562](https://doi.org/10.5281/zenodo.21760562).
Its first execution was subsequently classified as invalid because the public
runner substituted a donor B input during carrier construction rather than
exchanging a completed donor C, and because it did not execute the complete
registered Phase B control set. The generated outputs and the audit were
published without a confirmatory inference at
[DOI 10.5281/zenodo.21760837](https://doi.org/10.5281/zenodo.21760837) and in
the [technical failure report](../003_subjectivity_agent_class2_o3/TECHNICAL_FAILURE_REPORT.md).

Experiment 003R was then preregistered as a separate corrected study at
[DOI 10.5281/zenodo.21761030](https://doi.org/10.5281/zenodo.21761030).
It used previously unused pairs and seeds, implemented completed donor-C
exchange through unchanged recipient return paths, executed all eleven
registered Phase B controls, and required an exact machine-checked match
between the registered and executed control inventories.

## Frozen execution provenance

- Public preregistration commit: `9043ce5e640d2c75586da9484a91aabd30df5fca`
- Public preregistration tag: `e003r-preregistration-v1.0.0`
- Confirmatory seed: `20260813`
- Confirmatory pairs: `P2000` through `P2127`
- Private runtime commit: `2c3587d14b51dd02f0b04042698f2410235bd833`
- Private source files verified: 21 of 21 SHA-256 digests matched
- Registered and executed Phase B controls: exact inventory match, 11 of 11
- Exact pre-intervention A/B state matching: 128 of 128 pairs
- Candidate and control optimization budget: zero

The private agent source remains undisclosed. Its repository commit and the
SHA-256 digest of each required source file were frozen before execution and
verified by the public runner. The verification receipt is published in
[`source_verification.json`](results/source_verification.json).

## Registered outcomes

| Registered decision | Observed | Registered threshold | Result |
|---|---:|---:|---|
| Phase A Class 2 | 126/128 | at least 112/128 | Supported |
| Phase B Class 2 | 126/128 | at least 112/128 | Supported |
| Phase B O3 | 126/128 | at least 112/128 | Supported |
| History family 0 transfer | 63/64 | at least 52/64 | Supported |
| History family 1 transfer | 63/64 | at least 52/64 | Supported |
| Exact Phase B control inventory | 11/11 | exact match | Passed |

All eight registered Class 0 or Class 1 controls produced zero false Class 2
declarations across 128 pairs each. This comprises 1,024 control evaluations:
`no_c`, `historyless`, `common_memory`, `history_only`, `individual_memory`,
`compressed_summary`, `unilateral_return`, and `unrelated_c`.

## Pair-level exceptions

Two pairs did not receive a Class 2 or O3 classification:

- `P2063` in history family 0;
- `P2127` in history family 1.

For both pairs, exact A/B state matching passed, as did the other relevant
positive and control conditions. Pair specificity was zero in both phases,
and the registered completed-C-exchange gate failed. The pairs were retained
in the denominator and were not replaced. Their complete measurements are
available in [`pair_metrics.csv`](results/pair_metrics.csv) and
[`phase_b_control_metrics.csv`](results/phase_b_control_metrics.csv).

## Matched generic recurrent control

The preregistration included a matched generic recurrent control with the same
differentiated inputs, event count, state dimensions, bilateral return paths,
completed-C exchange, control inventory, and zero optimization budget. It
passed Class 2 in 126 of 128 pairs and O3 in 126 of 128 pairs, exactly matching
the proposed O3 implementation.

Under the preregistered interpretation, this is evidence of implementation
non-uniqueness. The result does not show that the proposed native-memory and
self-reentry channel assignment is required for the observed operational
criteria. A subsequent experiment would need discriminatory interventions or
predictions that separate the proposed architecture from the matched generic
recurrent alternative.

## Interpretation boundary

The confirmatory result supports the following limited statement:

> Under the frozen public interfaces, controls, thresholds, and private-source
> hashes, a constructed third-runtime carrier and its explicit self-reentrant
> extension satisfied the registered operational Class 2 and O3 criteria and
> transferred to two previously unused history families.

It does not establish that the carrier arose spontaneously, that the private
agents possess subjectivity, that the carrier is subjectivity itself, that the
tested implementation is unique, or that Subjectivity-Intersection Ontology
has been empirically validated. It also does not establish ontological
irreducibility. The study evaluates an operational construction within a
specified computational system.

## Published outputs

The generated result files are published unchanged:

- [Concise generated result](results/RESULT.md)
- [Complete summary](results/summary.json)
- [Pair-level metrics](results/pair_metrics.csv)
- [Class 0 and Class 1 control metrics](results/control_metrics.csv)
- [Phase B control metrics](results/phase_b_control_metrics.csv)
- [Exact state-match receipts](results/state_match_receipts.csv)
- [Source and registration verification](results/source_verification.json)
- [Output SHA-256 manifest](results/output_manifest.json)

The output manifest permits byte-level verification of every generated result
file other than the manifest itself.
