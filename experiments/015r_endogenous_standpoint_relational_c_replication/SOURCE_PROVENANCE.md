# E015R Source and Lineage Provenance

## Predecessor record

- Private source repository: `SIEL-Research/SIEL-Research-Agent`
- E015 registration commit:
  `caf49c165f9c75f77089b2aef8545015ba4254ac`
- E015 result commit:
  `9fbd40e63b5ca0ee6821138daef858110c2ac743`
- E015 clean result-Release target:
  `3dbaa1d7077e8c9aee36088f7b3ddee54a82af77`
- E015 runner SHA-256:
  `8fe81abf44c8375c09a8014b078010d1131ada5c3f662a5426c5c81bc1371c2b`
- E015-X3 base-runner SHA-256:
  `9c56bc3a6293e40345ed35aa1d97815228e405eda5106ae9d521a5d2684b43f1`
- E015 raw-result SHA-256:
  `5a47108a5b0294ba21628923807a0e648aebdc895e23b0fa4dd9c84a34bd6f16`
- E015 decision SHA-256:
  `ec5fa19bfd73d72d582d7bb1639f1035dcf4743803604ac163835de9bae49702`

These identifiers establish the result-informed lineage and permit exact source
comparison. They are not inputs to the E015R confirmatory data.

## E015R lineage

E015R uses an exact byte copy of the frozen E015-X3 base runner and a
lineage-derived decision runner. The only permitted deltas are enumerated in
`TECHNICAL_SPECIFICATION.md`. E015R uses a fresh, disjoint seed block and
receives its own registered decision, preregistration DOI, and result DOI.

The predecessor outcome is known, so E015R is classified as a direct,
result-informed out-of-sample replication rather than a discovery study.
Source hashes are reported to make that dependency explicit and auditable.
