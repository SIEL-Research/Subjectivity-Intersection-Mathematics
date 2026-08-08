# Experiment 008A Technical Specification

## Runtime

- Python 3.9 or newer
- Python standard library only
- no network access during execution

## Registration mode

`run.py --validate-registration` validates the manifest and registered source
hashes and refuses registration validation if the default result directory
exists. It cannot accept a measurement file and does not evaluate the models.

## Scientific execution mode

`run.py --execute --measurement-file FILE [--output-dir DIR]`

Execution requires both explicit flags. The runner never downloads data and
never overwrites an output directory.

Measurement schema:

```json
{
  "schema": "siel-e008a-hfs-measurements-v1",
  "records": [
    {
      "id": "hydrogen_1s_hfs",
      "source_id": "doi:10.1016/j.adt.2010.05.001",
      "frequency_hz": 0.0,
      "uncertainty_hz": 0.0
    },
    {
      "id": "deuterium_1s_hfs",
      "source_id": "doi:10.1016/j.adt.2010.05.001",
      "frequency_hz": 0.0,
      "uncertainty_hz": 0.0
    }
  ]
}
```

Zeros illustrate types and are invalid. Records may appear in either order;
additional records are forbidden.

## Frozen numerical inputs

- `M_H=1836.152673426`
- `M_D=3670.482967655`
- `I_H=0.5`
- `I_D=1.0`
- `mu_H/mu_N=2.79284734463`, standard uncertainty `0.00000000082`
- `mu_D/mu_N=0.8574382335`, standard uncertainty `0.0000000022`
- `lambda=1`
- primary band half-width `abs(log(r_SI/r_0))/4`
- full-theory interpretive nuisance scale `500e-6`

## Outputs

- `summary.json`
- `report.md`

The output directory is created atomically only after provenance checks pass.
