# Experiment 013 execution note

- Registration release: `e013-preregistration-v1.0.0`
- Registration commit: `312bd7180a96796f307aa2e150cac567b88a696d`
- Registration DOI: `10.5281/zenodo.21894665`
- Registered target executions: one
- Result-informed repairs or reruns: none
- Environment: PySCF 2.14.0 virtual environment previously used for E010
- All 13 fresh cc-pVTZ geometries completed in full and isolated-centre modes.
- Every floating-point value stored in `summary.json` is finite.
- The E010 matrix-construction path emitted divide-by-zero, overflow, and
  invalid-value NumPy warnings during intermediate matrix multiplication. The
  registered run completed, all stored energies were finite, and the warnings
  are retained rather than suppressed.
- Overall decision: `DOMAIN_PRIOR_O3_GENERATION_TRANSFER_NOT_SUPPORTED`.
