# Experiment 007A Phase 1: Operator-Algebra Definition Audit

This registered audit resolves the seven-versus-twelve composition problem identified after the Experiment 007A proposal.

It tests whether the frozen D12RG seven-operator object is a seven-element closed set, a typed partial action system, or a basis of a seven-dimensional algebra. It separately audits whether the frozen SIO 006-series sources already define the operator algebra required for a leakage-resistant independent comparison.

## Run

From the repository root:

    python3 experiments/007a_phase1_operator_algebra_definition_audit/test_run.py

    python3 experiments/007a_phase1_operator_algebra_definition_audit/run.py \
      --riemann-repo /path/to/d12rg-riemann \
      --out-dir experiments/007a_phase1_operator_algebra_definition_audit/results

The Riemann checkout must be at commit `12759beb5c6acb41b83597dfb77b74cd576d5066` with the registered origin and source hashes.

## Claim boundary

This is a source-boundary and algebraic-object audit. A complete run may conclude that a later constructed SIO extraction rule is required. Such a result is not a failed seven-operator experiment; it identifies the exact missing definition that must be registered before the independent comparison can be valid.

## License

Experiment code in this directory is Apache-2.0. External D12RG sources retain their original license and are loaded from a separate frozen checkout.
