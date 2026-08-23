# Experiment E015R — Endogenous Standpoint Constitution and Relational-C Re-entry

Status: `FROZEN_NOT_EXECUTED_AWAITING_DOI1`

E015R is a prospective public confirmatory experiment asking whether two
structurally identical interacting units can infer operational self/other roles
from their own action-consequence histories and whether those roles organize a
prediction-trained system into a nonadditive relational component `C` with
bilateral causal effects and one-step relational re-entry.

The test uses a frozen synthetic two-actor generator, a 48-dimensional
connected predictor, an equal-dimensional additive control, 48 fresh outer
seeds, nine noncompensating primary gates, and seven validity gates. The full
scientific rationale, competing hypotheses, operational definitions,
estimators, thresholds, failure rules, and claim limits are frozen in
`PREREGISTRATION.md`.

E015 is disclosed as the result-informed predecessor of this replication. No
E015R confirmatory seed, threshold, endpoint, comparator, or analysis may be
selected after outcome access.

The public preregistration Release and Zenodo DOI-1 must be published,
reopened, and checksum-verified before confirmatory execution. The runner
enforces this requirement through `registration_receipt.json`, which does not
exist in the frozen preregistration package.

Only target-free validation is permitted before DOI-1:

```bash
python3 -m py_compile \
  experiments/015r_endogenous_standpoint_relational_c_replication/run.py \
  experiments/015r_endogenous_standpoint_relational_c_replication/e015_x3_frozen_base.py \
  experiments/015r_endogenous_standpoint_relational_c_replication/tests/test_e015r.py
python3 experiments/015r_endogenous_standpoint_relational_c_replication/tests/test_e015r.py
shasum -a 256 -c experiments/015r_endogenous_standpoint_relational_c_replication/FROZEN_MANIFEST.sha256
```

The confirmatory command remains prohibited until Gate E-DOI-1 passes:

```bash
python3 experiments/015r_endogenous_standpoint_relational_c_replication/run.py \
  --phase confirmatory \
  --manifest experiments/015r_endogenous_standpoint_relational_c_replication/FROZEN_MANIFEST.sha256
```

No E015R confirmatory seed has been generated or inspected.
