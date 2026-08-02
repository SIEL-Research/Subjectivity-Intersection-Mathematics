# Experiment 006R Result

## Revised Confirmation of Spontaneous Operational O3 Re-entry

Status: CONFIRMATORY_COMPLETE
Primary readout: SUPPORTED
Secondary boundary readout: SUPPORTED

| Architecture | Competent | Transport all 3 | Action 2 of 3 | Own-history 2 of 3 |
|---|---:|---:|---:|---:|
| distributed | 48 | 47 | 45 | 29 |
| central_shared | 48 | 48 | 48 | 46 |
| directional_relay | 48 | 48 | 46 | 47 |
| four_channel_crossbar | 47 | 47 | 44 | 41 |

## Revised primary acceptance checks

- capacity_exact_486: PASS
- competence_at_least_44_of_48_each_interacting_architecture: PASS
- transport_all_three_at_least_40_of_48_each_architecture: PASS
- pooled_transport_at_least_168_of_192: PASS
- action_loss_two_of_three_at_least_36_of_48_each: PASS
- action_magnitude_two_of_three_at_least_36_of_48_each: PASS
- median_transport_fraction_at_least_0_75_each: PASS
- median_transport_alignment_at_least_0_60_each: PASS
- median_exchange_loss_at_least_0_25_each: PASS
- median_bilateral_erasure_at_least_0_95_each: PASS
- independent_accuracy_at_most_0_20: PASS
- independent_component_at_most_1e_10: PASS
- reentry_reconstruction_error_at_most_1e_12: PASS

## Secondary boundary checks

- partitioned_architectures_at_least_40_of_48: PASS
- distributed_fewer_than_40_of_48: PASS
- distributed_gap_at_least_6: PASS

## Interpretation boundary

A supported primary result confirms transfer of spontaneous operational O3 re-entry across a new 48-seed allocation. The secondary readout tests whether relation-versus-individual-history identifiability depends on implementation topology. Neither decision identifies the learned component with ontological subjectivity or proves a unique physical mechanism.
