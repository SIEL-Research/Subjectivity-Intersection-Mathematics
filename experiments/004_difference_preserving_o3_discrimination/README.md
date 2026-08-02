# Experiment 004

## Difference-Preserving Relational Carrier and Retained-History O3 Audit

Experiment 004 tests whether a recurrent relational architecture preserves
the distinction between A and B when their common content is fixed, retains an
earlier difference after the final current input is matched, and transports
that difference through carrier, self-state, and bilateral return paths.

The confirmatory allocation must not be executed before the preregistration
GitHub Release and Zenodo DOI have been verified.

## Registered documents

- `PREREGISTRATION.md`
- `TECHNICAL_SPECIFICATION.md`
- `run.py`
- `test_run.py`
- `registration_manifest.json`

## Confirmatory command

Run only from the registered commit:

```bash
python3 run.py \
  --mode confirmatory \
  --private-agent-root /absolute/path/to/minimal-agent-paper \
  --out-dir results \
  --check
```

The output directory must not exist before execution. The runner refuses to
overwrite an existing result.
