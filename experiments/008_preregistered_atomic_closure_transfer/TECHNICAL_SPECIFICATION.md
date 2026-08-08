# Experiment 008 Technical Specification

## Registered directory

`experiments/008_preregistered_atomic_closure_transfer`

## Runtime

- Python 3.9 or newer
- Python standard library only
- no network access during execution

## Registration mode

`run.py --validate-registration` performs only:

1. registration-manifest schema validation;
2. SHA-256 verification of registered source files;
3. confirmation that no default scientific result files exist; and
4. confirmation that the manifest status is `PREREGISTERED_NOT_EXECUTED`.

It does not call any scientific evaluator or load a measurement file.

## Scientific execution mode

`run.py --execute --measurement-file FILE [--output-dir DIR]`

Execution is invalid without the explicit `--execute` flag and an explicit
measurement path. The runner never downloads measurements.

The measurement JSON schema is:

```json
{
  "schema": "siel-e008-measurements-v1",
  "records": [
    {
      "id": "muonium_1s2s",
      "source_id": "doi:10.1103/PhysRevLett.84.1136",
      "frequency_hz": 0.0,
      "uncertainty_hz": 0.0
    },
    {
      "id": "positronium_1s2s",
      "source_id": "arxiv:2407.02443v1",
      "frequency_hz": 0.0,
      "uncertainty_hz": 0.0
    }
  ]
}
```

The zeros illustrate types only and are not valid values. Records may appear
in either order; no additional record is allowed.

## Frozen constants

- `R_infinity c = 3.2898419602508e15 Hz`
- `alpha = 7.2973525643e-3`
- `m_e/m_mu = 4.83633170e-3`
- `m_e/m_e = 1`

These are 2022 CODATA values or direct identities. Uncertainty propagation of
the constants is secondary because the registered leading correction budget is
many orders larger.

## Registered radii and numerical tolerance

- radii: `(0.5,0.75,1,1.5,2,3,4,6)`
- constant-flux relative spread tolerance: `1e-12`
- algebraic identity tolerance: `1e-12`

## Outputs

Execution writes atomically into a previously absent output directory:

- `summary.json`
- `report.md`

If the output directory already exists, execution stops. No overwrite mode is
provided.

`summary.json` contains inputs, predictions, every gate, and the primary
classification. `report.md` renders the same information. The measurement
file SHA-256 is recorded.

## Failure routing

- source hash/schema failure -> `PROVENANCE_FAILURE`, no scientific output;
- invalid measurement schema/source/value -> `PROVENANCE_FAILURE`, no
  scientific output;
- valid execution -> exactly one registered scientific classification.
