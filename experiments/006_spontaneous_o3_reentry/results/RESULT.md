# Experiment 006 Result

## Spontaneous Operational O3 Re-entry

Status: CONFIRMATORY_COMPLETE
Primary readout: NOT_SUPPORTED

| Architecture | Competent | Transport all 3 | Action 2 of 3 | Own-history 2 of 3 |
|---|---:|---:|---:|---:|
| distributed | 24 | 24 | 24 | 17 |
| central_shared | 24 | 24 | 23 | 21 |
| directional_relay | 24 | 24 | 24 | 23 |
| four_channel_crossbar | 24 | 24 | 22 | 23 |

## Registered acceptance checks

- capacity_exact_486: PASS
- competence_at_least_22_of_24_each_interacting_architecture: PASS
- transport_all_three_at_least_18_of_24_each_architecture: PASS
- pooled_transport_seed_passes_at_least_75_of_96: PASS
- action_loss_two_of_three_at_least_18_of_24_each_architecture: PASS
- action_magnitude_two_of_three_at_least_18_of_24_each_architecture: PASS
- relation_over_own_history_two_of_three_at_least_18_of_24_each: FAIL
- median_transport_fraction_at_least_0_75_each_architecture: PASS
- median_transport_alignment_at_least_0_60_each_architecture: PASS
- median_exchange_loss_at_least_0_25_each_architecture: PASS
- median_bilateral_erasure_at_least_0_95_each_architecture: PASS
- independent_accuracy_at_most_0_20: PASS
- independent_component_zero: PASS
- reentry_reconstruction_error_at_most_1e_12: PASS

## Interpretation boundary

A supported result establishes an operational spontaneous O3 re-entry solution class: a learned directed relation component is causally transported into later relation states and bilateral action without an explicit O3 state, target, or loss. It does not identify the learned state with ontological subjectivity or prove a unique physical mechanism.
