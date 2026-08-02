# Experiment 003 Technical Failure Report

## Status

**INVALID CONFIRMATORY RUN — IMPLEMENTATION/PROTOCOL MISMATCH**

The Experiment 003 confirmatory command completed successfully against the
public preregistration commit. Subsequent audit identified material differences
between the intervention and control procedures stated in the preregistration
documents and those implemented in the registered runner.

The generated outputs are published unchanged as an execution receipt. They do
not constitute a valid negative test of the registered Class 2 or operational
O3 hypotheses.

## Frozen registration provenance

- Registration commit:
  `0c559e7c9de613b2d6575b58ea3201add8882bc8`
- Registration tag: `e003-preregistration-v1.0.0`
- Registration DOI: `10.5281/zenodo.21760562`
- Confirmatory seed: `20260802`
- Registered sample: 128 disjoint pairs, `P1000` through `P1127`

The registration tag and DOI remain unchanged. This report does not revise the
registered source retrospectively.

## Execution integrity

The registered command exited successfully and wrote all seven registered
output artifacts. Source verification passed for the public registration files
and for all 21 hash-frozen private V61/V89f source files. Complete pre-return A
and B runtime-and-memory hashes matched for all 128 pairs. The six artifacts
covered by `output_manifest.json` retain their original SHA-256 digests.

No threshold, seed, pair, output, or generated value was changed after result
inspection. The confirmatory command was not rerun.

## Material protocol deviations

### 1. The registered C-exchange intervention was not implemented

The technical specification defines pair specificity as the downstream A/B
distance after substituting another pair's completed C state. The runner did
not perform that intervention.

Instead, for the `partner_substitution` condition, it substituted the donor
pair's B input while constructing a new C for the recipient pair. This occurred
in both Phase A and Phase B. Substituting one source input during C formation is
not equivalent to constructing `C_XY` from pair X-Y and inserting that completed
state into the fixed A-B return pathway.

Consequently, the reported pair-specificity value of zero in 128 of 128 pairs
is a result of the implemented donor-B substitution procedure. It cannot be
interpreted as evidence that the registered completed-C exchange has no effect.

### 2. Several registered Phase B controls were not executed

The preregistration requires Phase B controls for:

- removal of self-reentry while preserving the carrier;
- carrier reset immediately before action;
- native episodic-archive reset immediately before action;
- interaction-order erasure;
- current-input-only presentation;
- direct carrier output without passage through the self state; and
- unilateral return.

The primary `run_experiment` path evaluated self-state erasure and bilateral
feedback removal, but it did not invoke the complete registered Phase B control
set. Although the runner contains parameters for order erasure and
current-input-only presentation, those paths were not called by the
confirmatory execution. Other listed controls were not implemented as
registered Phase B interventions.

The Phase B O3 decision therefore lacks required control evidence independently
of the pair-specificity defect.

## Observed but non-confirmatory diagnostics

Under the procedures that were actually implemented:

- exact A/B pre-return state matching passed in 128 of 128 pairs;
- joint generation passed its frozen threshold in 128 of 128 pairs in both
  phases;
- history irreducibility passed in 128 of 128 pairs in both phases;
- intervention sensitivity passed in 128 of 128 pairs in both phases;
- bilateral feedback passed in 128 of 128 pairs in both phases;
- gauge tolerance passed in 128 of 128 pairs in both phases;
- the measured self-state, continuous-action, and bilateral return effects
  passed their thresholds in 128 of 128 Phase B pairs;
- the two executed erasure controls passed in 128 of 128 pairs; and
- every implemented registered Class 0 and Class 1 null remained below the
  false-Class-2 bound.

These observations may guide debugging, but they cannot rescue or replace the
missing registered interventions. They are not confirmatory evidence for Class
2 or O3.

## Scientific conclusion

The appropriate confirmatory conclusion is:

> The Class 2 relational-carrier and operational O3 hypotheses were not validly
> evaluated because the registered runner did not implement the completed-C
> exchange and did not execute the full registered Phase B control set.

The status is therefore `NOT EVALUABLE`, not `SUPPORTED` and not `FALSIFIED`.

## Corrective action

A corrected study must be preregistered as a new version, provisionally
Experiment 003R. It must:

1. construct and freeze the recipient pair's native C or O3 state;
2. independently construct a completed donor-pair C state;
3. insert the completed donor C into unchanged recipient A/B return channels;
4. archive stage-level distances at `K_AB`, `z_C`, action, A, and B;
5. implement and receipt every registered Phase B control;
6. include a machine-enforced equality check between the registered control
   inventory and the executed control inventory;
7. use new subjectivity-agent instances, pair identifiers, and confirmatory
   seeds; and
8. exclude all 128 pairs used in this invalid run from new confirmatory
   evidence.

The corrected preregistration must explicitly cite this technical failure and
must not describe Experiment 003R as independent of the information obtained
from the present run.

## Published execution artifacts

- [Generated result summary](results/RESULT.md)
- [Complete JSON summary](results/summary.json)
- [Pair-level metrics](results/pair_metrics.csv)
- [Control-level metrics](results/control_metrics.csv)
- [State-match receipts](results/state_match_receipts.csv)
- [Source-verification receipt](results/source_verification.json)
- [Output manifest](results/output_manifest.json)

The generated `RESULT.md` is preserved as emitted by the registered runner. Its
boolean output must be read together with this audit report and must not be
cited as a valid hypothesis test.
