# Public verification notes

## Frozen artifact identities

| Artifact | SHA-256 |
|---|---|
| `Braid_Quantum_Lorentz_Unification_Preprint_v0.81.pdf` | `52af9729288e3e031cdce583ec38db33ba9ed7210265bf05483ad4c6c9358bf0` |
| `BRAID_QUANTUM_LORENTZ_UNIFICATION_PREPRINT_v0.81.tex` | `8b835e7182df5a36d4bda88e5ee2d81d5e74aff2f304d29c8a92e9b14628fe29` |

## Verification performed

- The source was built twice with XeLaTeX without fatal errors, undefined
  controls, or overfull boxes.
- The committed PDF is 29 A4 pages and is unencrypted.
- Every page was rendered to PNG and visually inspected for clipping,
  overlap, missing glyphs, tables, equations, and page numbering.
- The PDF identifies itself as public working preprint v0.81 and includes the
  evidence, peer-review, data, and AI-assistance boundaries.
- The positive result ledger and the NO-GO/blocking ledger are both present.
- The exact evidence cutoff is revision `4b0e803b9`.

Run the integrity checks from this directory:

```text
python3 verify_release.py
```

## Claim boundary

The strongest current result is an exact finite prototype of a rank-four,
metric-affine relational geometry on one registered pointed-braid source,
with a direct characteristic-zero relative polar branch. It is not a completed
or empirically validated theory of quantum gravity.
