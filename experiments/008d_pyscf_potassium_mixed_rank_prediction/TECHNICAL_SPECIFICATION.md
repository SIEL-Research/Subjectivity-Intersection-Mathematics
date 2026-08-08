# E008D technical specification

## Benchmark schema

The post-registration benchmark file must contain exactly:

```json
{
  "schema": "siel-e008d-k-second-order-corrections-v1",
  "records": [
    {
      "id": "potassium39_4p1_2_second_order_delta_A",
      "source_id": "doi:10.1103/PhysRevA.78.032519",
      "second_order_delta_A_khz": "<post-registration extraction>",
      "rounding_half_width_khz": "<half unit of last printed digit>"
    },
    {
      "id": "potassium41_4p1_2_second_order_delta_A",
      "source_id": "doi:10.1103/PhysRevA.78.032519",
      "second_order_delta_A_khz": "<post-registration extraction>",
      "rounding_half_width_khz": "<half unit of last printed digit>"
    }
  ]
}
```

The placeholders are deliberately nonnumeric and invalid for execution.

## Extraction rules

- Use the total second-order correction to `A(P_1/2)`, not an individual eta
  or zeta parameter.
- Preserve the printed sign and digits.
- Convert the printed unit to kHz exactly.
- Set the rounding half-width to half one unit of the last printed digit.
- If either isotope is absent, ambiguous, or reported only as a bound, stop
  with `PROVENANCE_FAILURE`.
- Do not replace the source or choose a different theoretical result by
  agreement with either registered model.

## Execution

```bash
python3 experiments/008d_pyscf_potassium_mixed_rank_prediction/run.py \
  --execute \
  --measurement-file /path/to/e008d_measurements.json \
  --output-dir /path/to/new/e008d-results
```

The output directory must not already exist. The runner writes `summary.json`
and `report.md` atomically.
