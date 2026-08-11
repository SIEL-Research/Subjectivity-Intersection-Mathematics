# Experiment 014 execution note

The single registered execution was started only after both public provenance
conditions were satisfied:

- GitHub preregistration release:
  `e014-preregistration-v1.0.0`, commit
  `7866c2308ab9fea5bbb88aa6bbdf158b6d2ece2f`;
- Zenodo preregistration DOI: `10.5281/zenodo.21895645`.

The runner accepted the frozen registration receipt, verified all registered
source hashes, created a previously absent results directory, calculated the
reserved targets once, and returned
`STABILIZED_O3_RETURN_CROSS_DOMAIN_TRANSFER_SUPPORTED`.

No target, seed, mismatch rule, stabilization interval, grid factor, readout,
bootstrap rule, gate, or decision criterion was changed after execution.
Runtime floating-point warnings emitted inside matrix products were retained;
the registered finite-value and normalization checks did not fail, all result
JSON is strict, and every registered primary gate passed.
