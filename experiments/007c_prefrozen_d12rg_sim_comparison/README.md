# Experiment 007C

## Pre-frozen D12RG--SIM structural comparison

Experiment 007C compares two objects that were fixed independently and in a documented order:

- the seven-dimensional `4+2+1` Paper 5.3 D12RG operator algebra frozen by Experiment 007A before Experiment 007B; and
- the eleven-operation typed nonlinear Subjectivity-Intersection Mathematics action structure independently extracted by Experiment 007B.

The experiment does not search all occurrences of the number seven in D12RG. It excludes the distinct `3+3+1` decomposition, Paper 5.3 `E7`, Paper 5 `X7`, and every other seven-labelled object. It also does not alter the Experiment 007B primitive set.

The comparison is source-bound, hash-separated, and generated mechanically from `comparison_contract.json`. Semantic name matching and post-result remapping are prohibited.

## Registered order

1. Publish the preregistration package and create the preregistration Release.
2. Run the frozen registration checks.
3. Execute the confirmatory comparison against the registered D12RG checkout.
4. Preserve every output, including a null or obstruction result.
5. Publish the result in a separate commit and Release.

## Commands

Registration check:

    python3 experiments/007c_prefrozen_d12rg_sim_comparison/run.py \
      --mode registration-check \
      --d12rg-repo /Users/satoru/Documents/Codex/2026-08-04/d12rg-riemann-readonly \
      --out-dir /tmp/e007c-registration-check \
      --check

Confirmatory run:

    python3 experiments/007c_prefrozen_d12rg_sim_comparison/run.py \
      --mode confirmatory \
      --d12rg-repo /Users/satoru/Documents/Codex/2026-08-04/d12rg-riemann-readonly \
      --out-dir experiments/007c_prefrozen_d12rg_sim_comparison/results \
      --check

The code is released under Apache-2.0. The imported D12RG source remains under its own stated license.
