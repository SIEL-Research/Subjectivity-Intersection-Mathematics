# E008C technical specification

## Measurement schema

The post-registration measurement file must contain exactly two records:

```json
{
  "schema": "siel-e008c-li-2p-hfs-measurements-v1",
  "records": [
    {
      "id": "lithium6_2p1_2_hfs_A",
      "source_id": "doi:10.1139/p65-075",
      "magnetic_dipole_constant_hz": "<post-registration extraction>",
      "uncertainty_hz": "<post-registration extraction>"
    },
    {
      "id": "lithium7_2p1_2_hfs_A",
      "source_id": "doi:10.1139/p65-075",
      "magnetic_dipole_constant_hz": "<post-registration extraction>",
      "uncertainty_hz": "<post-registration extraction>"
    }
  ]
}
```

The strings are non-numeric placeholders and are invalid for execution. Replace
them only after public registration. A magnetic dipole constant may be signed
but must be finite and nonzero. Its uncertainty must be finite and positive.

## Observation map

The runner computes

`Delta_nu_6 = abs(A_6) * 3/2`,

`Delta_nu_7 = abs(A_7) * 2`,

then `r_obs=Delta_nu_6/Delta_nu_7`. Uncertainties are propagated in log
space from the two reported `A` uncertainties.

## Execution contract

Registration validation refuses measurement input. Scientific execution
requires a measurement file and writes atomically into a new output directory.

```bash
python3 experiments/008c_lithium_2p_cross_state_transfer/run.py \
  --execute \
  --measurement-file /path/to/e008c_measurements.json \
  --output-dir /path/to/new/e008c-results
```
