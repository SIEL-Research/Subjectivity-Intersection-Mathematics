# E015R Technical Specification

## Frozen environment

- Reference platform: macOS 15.6, arm64
- Reference Python: 3.14.6
- NumPy: 2.4.4
- External service or paid compute: none
- Human, animal, clinical, or personal data: none

## Source layout

- `e015_x3_frozen_base.py`: byte-preserved E015-X3 simulator and learner.
- `run.py`: E015 decision runner adapted only for public self-contained
  packaging, E015R identifiers, fresh seeds, and DOI-1 enforcement.
- `tests/test_e015r.py`: target-free specification tests.
- `SEED_MANIFEST.json`: frozen test, confirmatory, and randomization seeds.
- `BASELINE_GATE.json`: source, split, and intervention audit state.
- `FROZEN_MANIFEST.sha256`: preregistration file hashes.

## Frozen scientific invariants

The following elements are fixed before outcome access: episode generator,
viewpoint construction, connected/additive learner dimensions, training
schedule, four-history `C` extractor, interventions, observables, estimators,
nine A-class thresholds, seven scientific validity thresholds, sign-flip
count, Holm family, TOST margin, decision ordering, no replacement, and failure
retention.

The permitted E015R deltas are:

1. self-contained public repository paths;
2. experiment and output identifiers changed from E015 to E015R;
3. fresh outer and randomization seeds;
4. an execution-blocking public DOI-1 receipt check; and
5. a clean-worktree requirement immediately before execution.

The permitted differences from the result-informed predecessor are listed to
make the replication identity auditable. No predecessor outcome is used to
retune a threshold or select an E015R confirmatory seed.

## Output behavior

The runner refuses to overwrite an existing `results/` directory. It writes a
partial raw file after every completed seed and retains its execution log on
error. The registered outcome is derived once from the complete retained rows.

## Pre-execution validation

Validation imports and exercises only specification/test data. It must never
call `evaluate_seed` on any integer in `98100..98147`.
