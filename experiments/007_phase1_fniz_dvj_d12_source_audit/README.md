# Experiment 007, Phase 1: FNIZ-DVJ-D12 Source-Derivation Audit

This directory contains the frozen Phase 1 preregistration for Experiment 007 in Subjectivity-Intersection Mathematics.

Phase 1 asks a deliberately prior question. Before any candidate connector is searched for or tested, do the cited D12RG sources uniquely determine a rule that connects signed FNIZ operation history, the native DVJ transfer, and the moving D12 projector?

The audit is classificatory. A complete audit remains valid if the sources yield one rule, several rules, no rule, or an incomplete definition. A negative or non-unique outcome must not be converted into a constructed connector and presented as source-derived.

The primary object of the proposed later programme is the composite operational carrier candidate `K^E_FNIZ-DVJ-D12`. It is not identified with ontological O3. An operational O3 candidate would additionally require a distinct persistent self-state, its own mediation action, and bilateral return to A and B.

## Registered source authorities

- D12RG Riemann repository: `https://gitlab.com/d12rg/d12rg-riemann.git`
- Frozen Riemann commit: `12759beb5c6acb41b83597dfb77b74cd576d5066`
- D12RG CFT repository: `https://gitlab.com/d12rg/d12rg_cft.git`
- Frozen CFT branch: `papers`
- Frozen CFT commit: `375d25e834208cf9a92154be9e51d72f09175a8f`
- Advaita source path: `z12cft-cft/knowledge/paper7.5/Advaita Canonical Database Expanded Operator Form LaTeX Source.txt`
- Advaita source SHA-256: `ebb0edfc0f4533a25eaf05adeba98aa0a5f9ded32f5a246acd636c6e51481630`

## Registered execution

From the repository root:

    python3 -m venv /path/to/e007-phase1-venv
    /path/to/e007-phase1-venv/bin/pip install -r \
      experiments/007_phase1_fniz_dvj_d12_source_audit/requirements.txt
    /path/to/e007-phase1-venv/bin/python \
      experiments/007_phase1_fniz_dvj_d12_source_audit/run.py \
      --riemann-repo /path/to/d12rg-riemann \
      --advaita-file /path/to/Advaita-source.txt \
      --out-dir experiments/007_phase1_fniz_dvj_d12_source_audit/results

The source checkouts or source files may be located anywhere. Their commit identities and hashes, not their local paths, are authoritative.

## Interpretation boundary

This phase does not test Class 2, O3, or the Riemann hypothesis. It does not inspect confirmatory data. It audits provenance, executable source definitions, algebraic admissibility constraints, and whether a unique cross-layer connector is already determined by the cited sources.

## License

Use the virtual environment's Python executable for the runner. The Experiment 007 audit code in this repository is released under Apache-2.0. External D12RG sources retain their own licenses and are not copied into this directory.
