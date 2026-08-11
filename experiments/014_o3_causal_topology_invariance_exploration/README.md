# Experiment 014 local exploration — O3 dynamic re-entry across domains

Status: `LOCAL_RESULT_INFORMED_EXPLORATION`

This exploration follows the registered E012 and E013 results without changing
them. E012 and E013 supported a threshold-free cross-domain four-edge causal
order but failed common absolute molecular score gates. The present work asks
what survives when the readout, representation, mismatch, intervention duration,
and return duration are varied explicitly.

The common object of comparison is not a shared scalar mediator. Each domain
executes its own dynamics and produces its own whole fingerprint:

```text
domain source
  -> domain O3 generation
  -> O3 removal / physical mismatch / correct return
  -> domain-native whole fingerprint
  -> causal order only
```

No scalar agreement is inverted into source-level identity.

## Preserved exploratory sequence

1. A fixed coordinate-radius molecular readout was not invariant. Across 4,350
   configurations it passed only `0.772644` of the four-edge tests.
2. Native-energy rank passed `4,176/4,176` stress configurations and a global
   randomized-readout null (`0/4,096` exceedances; conservative
   `p = 1/4,097`), but it could not distinguish carriers sharing the same
   minimum.
3. Full distributional fingerprints replaced minimum-centred occupancy. A
   carrier-level alternative was admitted as a specificity null only when it
   was also distinguishable under the registered whole readout.
4. Nonperiodic physical alternatives replaced periodic array rolls. Among
   alternatives separated by at least one pooled-observation resolution unit,
   the distributional four-edge order passed `1,347/1,347` comparisons.
5. Exact transition-matrix propagation separated causal classification from
   finite-seed noise. Molecular grid factors `1`, `2`, and `4` passed
   `522/522` exact covariance tests.
6. Exact molecular removal-return mapping passed `14,210/14,210` four-edge
   comparisons. Atomic full-density mapping passed `50/50` comparisons.
7. The frozen E009 cellular model produced a damage-dependent reinjection
   window: the latest successful reinjection moved from 50 to 45 to 43 minutes
   as damage amplitude increased from `0.60` to `0.75` to `0.90`; at `1.05`,
   even the earliest tested reinjection failed.
8. Six domain-level recovery axes had the predicted order exactly. A
   65,536-replicate label-permutation null produced zero exceedances
   (`p = 1/65,537`). This is exploratory because the axes and statistic were
   selected after E012/E013.
9. Two stronger simplifications failed and are retained:
   - molecular recovery was not locally monotone in removal duration in
     `76/2,030` strata, despite the population mean being monotone;
   - scalar pre-return dislocation ordered recovery in only `1,097/2,030`
   strata (`0.540394`), so a single distance is not a sufficient history
   variable.
10. A new cross-domain interaction audit then separated return identity from
    elapsed recovery time. Under the initially selected domain readouts, correct
    O3 return closed more of the remaining recovery gap than mismatch or removal
    in `2,043/2,043` groups, and all three leave-one-domain-out transfers passed.
11. Stronger versions were deliberately attacked and did not survive:
    - molecular correct-return gain was not greater than mismatch gain in every
      adjacent time interval (`1,527/12,180` interval reversals);
    - a rate-interaction claim was not invariant across JS, Hellinger, total
      variation, and Wasserstein readouts;
    - Wasserstein retained one geometry-transport counterexample across all
      three grid factors, showing that it answers a different observable
      question from distributional identity.
12. The surviving structural result is stabilized return specificity. For the
    molecular Hellinger fingerprint, correct return remained closer than both
    nulls across four removal durations, five later horizons, three grid
    factors, and all profile-temperature pairs (`10,440/10,440` specificity
    comparisons). Atomic density specificity held at every tested return
    horizon. Cellular trajectories showed genuine early crossings, but correct
    return was superior in all explored conditions from 40 minutes after
    reinjection onward.
13. Cellular boundary-neighbour stress preserved damage amplitudes `0.675` and
    `0.825` as unexecuted candidates. On both sides of each reserved value,
    four independent 32-lineage cohorts reproduced the same discrete boundary:
    45-minute reinjection passed and 50-minute reinjection failed in all
    `32/32` amplitude-time-cohort cells.
14. An unnamed atomic stress grid spanning mass ratios `1`–`10,000`, charges
    `0.5`–`3.0`, and four return horizons passed `120/120`; its stabilized
    200-step-or-later subset passed `90/90` with minimum specificity margin
    `0.130416065`. No reserved named isotope target was executed.

## Exploratory conclusion

The supported cross-domain candidate is a structural dynamic order:

```text
differentiated local state
  -> generated O3
  -> O3 interruption
  -> physically specific O3 return
  -> history-dependent re-entry toward the domain-native whole
```

The strongest surviving cross-domain candidate is therefore not universal
instantaneous recovery speed. It is the persistent causal advantage of the
correct O3 relation after a domain-native stabilization interval. Interruption
history cannot be reduced to elapsed time or a single displacement magnitude;
direction, basin, distributional form, and the registered domain readout remain
relevant.

## Candidate prospective E014 commitments

A public successor should preregister new held-out targets and freeze:

- domain-prior O3 generation before outcome inspection;
- domain-native full fingerprints rather than common absolute scores;
- nonperiodic physical mismatches with a pre-outcome discriminability gate;
- the threshold-free four-edge causal order;
- the direction of recovery with additional correct-return opportunity;
- a domain-native stabilization interval fixed without inspecting the held-out
  outcome;
- post-stabilization specificity: correct O3 return must remain closer to the
  registered domain state than removal and a physically distinguishable
  mismatch at every registered late checkpoint;
- three leave-one-domain-out predictions in which the interaction direction
  fixed from two domains is applied unchanged to a new target in the third;
- exact propagation where the finite-state engine permits it and registered
  uncertainty handling where it does not;
- molecular grid covariance and new cellular reinjection-window predictions;
- a compression boundary forbidding inference of a common substance,
  microscopic law, or source identity from the common causal order.

It should not preregister universal monotonic worsening with interruption time,
instantaneous correct-return speed dominance, readout-independent rate
dominance, scalar-dislocation sufficiency, a common absolute threshold, or a
universal cross-domain numerical law.

## Reproduction

The scripts are intentionally staged because later stages preserve failures
found by earlier stages. Key final audits are:

```bash
python3 experiments/014_o3_causal_topology_invariance_exploration/run_global_readout_null.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_distributional_fingerprint.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_exact_grid_covariance.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_molecular_reentry_phase_map.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_atomic_reentry_phase_map.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cellular_reentry_window.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cross_domain_dynamic_order.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_scalar_dislocation_audit.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cellular_return_identity_interaction.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cross_domain_return_identity_interaction.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_interaction_representation_covariance.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_hellinger_horizon_stress.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cellular_boundary_neighbour_stress.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cellular_boundary_cohort_stability.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_cross_domain_stabilized_specificity.py
python3 experiments/014_o3_causal_topology_invariance_exploration/run_atomic_parameter_stress.py
```

Nothing in this directory is registered, confirmatory, committed, pushed, or
released merely by running these scripts.
