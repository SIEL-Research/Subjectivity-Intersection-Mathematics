# E008B Technical Specification

## Registered files

`registration_manifest.json` contains the SHA-256 of every frozen source file.
The runner resolves those paths from the repository root. Validation fails if
a file is absent, changed, or if the default `results` path already exists.

## Measurement schema

The post-registration JSON must have schema
`siel-e008b-li-hfs-measurements-v1` and exactly two records:

```json
{
  "schema": "siel-e008b-li-hfs-measurements-v1",
  "records": [
    {
      "id": "lithium6_2s_ground_hfs",
      "source_id": "doi:10.1103/PhysRevLett.111.243001",
      "frequency_hz": 0,
      "uncertainty_hz": 0
    },
    {
      "id": "lithium7_2s_ground_hfs",
      "source_id": "doi:10.1103/PhysRevLett.111.243001",
      "frequency_hz": 0,
      "uncertainty_hz": 0
    }
  ]
}
```

The zeros above are schema placeholders, not target values and are invalid for
execution. Each executed value must be a finite positive JSON number. Extra
fields or records are rejected.

## Execution contract

Registration validation refuses a measurement file. Scientific execution
requires one and writes `summary.json` and `report.md` atomically into a path
that does not already exist.

```bash
python3 experiments/008b_pyscf_lithium_spin_representation_prediction/run.py \
  --execute \
  --measurement-file /path/to/e008b_measurements.json \
  --output-dir /path/to/new/e008b-results
```

The standard runner has no third-party dependency. `reproduce_cp157.py` is an
optional, target-free numerical provenance check using the exact PySCF and
PySCF-properties versions in `requirements-pyscf.txt`.
