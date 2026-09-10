# Public verification notes

## Frozen artifact identities

| Artifact | SHA-256 |
|---|---|
| `Braid_Quantum_Lorentz_Unification_Preprint_v0.1.pdf` | `41a93878cc063cd047148e4958d04234390c533f404ccb95ae9bd69679ea7edb` |
| `BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.1.tex` | `8c751e98df1a18d2116843fc345c6d28dcc56802a62fa306649d4ce75aea3c56` |

## Verification performed

- Title, version, open-access metadata, and CC BY 4.0 metadata agree.
- The committed PDF is 14 A4 pages, unencrypted, and contains no interactive
  form fields.
- The theorem title, working-preprint notice, peer-review boundary, direct
  pointed-braid citation, and AI-assistance disclosure are present.
- Two XeLaTeX builds from the frozen source complete successfully.
- Text extracted from the rebuilt PDF is byte-for-byte identical to text
  extracted from the reviewed PDF.

Run the integrity checks from this directory:

```text
python3 verify_release.py
```

The script requires `pdfinfo` and `pdftotext` from Poppler.

## Claim boundary

The strongest released result is a conditional, fixed-finite mathematical
construction on one regular Lorentzian patch for a nonzero short-time
interval. It does not establish an empirically validated theory of quantum
gravity, absolute semiclassical gravity, or an ontological theory of
subjectivity.
