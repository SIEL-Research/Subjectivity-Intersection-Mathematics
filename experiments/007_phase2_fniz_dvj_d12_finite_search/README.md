# Experiment 007, Phase 2: FNIZ-DVJ-D12 Finite Bridge Search

This directory contains the frozen Phase 2 preregistration for Experiment 007 in Subjectivity-Intersection Mathematics.

Phase 1 established that the cited D12RG sources define the signed-FNIZ, DVJ, and D12 components but do not uniquely determine a cross-layer connector. After the primitive/derived operation constraints, 144 conditional operation-to-deck rules remained and none was source-anchored.

Phase 2 performs a complete deterministic search over those 144 rules. It may select a constructed rule, a constructed equivalence class, multiple tied equivalence classes, or no admissible candidate. It cannot reclassify a searched rule as source-derived and does not test Class 2 or O3.

## Frozen upstream record

- Phase 1 results commit: `61bfbb763dfd41b15264b8a7dd3f081783ce3c2d`
- Phase 1 results DOI: `10.5281/zenodo.21794739`
- Phase 1 candidate table SHA-256: `a1f250c58889cc4cc200c1fe0cfa32f36111db72d9fc8d57157a6b5cbedfaf65`

## Registered execution

From the repository root:

    python3 -m venv /path/to/e007-phase2-venv
    /path/to/e007-phase2-venv/bin/pip install -r \
      experiments/007_phase2_fniz_dvj_d12_finite_search/requirements.txt
    /path/to/e007-phase2-venv/bin/python \
      experiments/007_phase2_fniz_dvj_d12_finite_search/run.py \
      --riemann-repo /path/to/d12rg-riemann \
      --out-dir experiments/007_phase2_fniz_dvj_d12_finite_search/results

## Interpretation boundary

The search uses only frozen D12 action geometry and source-native DVJ calibration. It does not inspect Phase 3 confirmatory conditions. Any selected object remains a constructed bridge hypothesis.

## License

The Phase 2 audit code is released under Apache-2.0. External D12RG sources retain their own licenses.
