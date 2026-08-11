# Execution note

- Status: local result-informed exploration; not preregistered.
- Quantum environment: the PySCF 2.14.0 virtual environment previously used by E010.
- Sparse cc-pVTZ workload: six rectangular H4+ geometries, two FCI modes per geometry, 56 orbitals.
- High-basis line workload: thirteen H4+ geometries at `b=0.9 Å`, `a=1.3...2.5 Å`, two FCI modes per geometry, 56 orbitals. Previously computed sparse points were reused and only missing points were evaluated.
- The inherited E010 `matmul_checked` path emitted NumPy runtime warnings for divide-by-zero, overflow, and invalid values during intermediate matrix multiplication. Its finite-output guard did not fail, the runner completed, and every stored sparse energy is finite. The warnings are retained here rather than omitted.
- A target-free rerun from the saved quantum checkpoint reproduced byte-identical `summary.json`, `RESULT.md`, and `sparse_energies.json` hashes.
- The line-trajectory sensitivity audit used 512 new exploratory seeds at readout radii `0.25`, `0.35`, and `0.45 Å`. It is explicitly result-informed and not a registered robustness test.
- The domain-prior rule-closure run generated the candidate in every domain as `C*_D = G_D - P_loc,D(G_D)` and verified exact removal and reconstruction before outcome scoring.
- The mismatch operator was selected by the result-informed structural rule “minimal admissible isometry with centered candidate overlap at most `0.25`”. It selected approximately `8.40` atomic spatial units, `0.5 Å` on each molecular grid, and `6 minutes` for the cellular trajectory.
- Every overlap-admissible shift in the recorded sensitivity sets passed the absolute mismatch and specific-return gates.
- The theory-fixed four-edge causal partial-order leave-one-domain-out test passed in all three domains. An unrestricted learned-pairwise variant failed in the cellular holdout because it additionally required `removed > mismatched_return`, while both cellular scores were zero. This negative result is preserved; that incidental ordering is not an O3 constitutive prediction.
- These rule choices and all reported passes remain result-informed exploration. Fresh targets, seeds, and an immutable registration are required before Experiment 013 can provide confirmatory evidence.
