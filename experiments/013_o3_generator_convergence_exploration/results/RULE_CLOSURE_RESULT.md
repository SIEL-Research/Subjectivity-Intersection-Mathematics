# Domain-prior rule-closure exploration

Operational rule closure: `True`.
All absolute signatures: `True`.
Causal partial-order leave-one-domain-out: `True`.
Unrestricted learned-pairwise leave-one-domain-out: `False`.

The causal test freezes only the four O3-required comparisons: intact and correct return must each exceed removal and mismatched return. The unrestricted diagnostic additionally learned an incidental removal-versus-mismatch ordering; its cellular holdout failure is preserved and is not used as an O3 gate.

## Molecular generated-mismatch scores

| Basis | Intact | Removed | Mismatch | Correct | Pass |
|---|---:|---:|---:|---:|---:|
| sto-3g | 1.000 | 0.291 | 0.000 | 1.000 | True |
| 6-31g | 0.998 | 0.258 | 0.106 | 0.981 | True |
| cc-pvdz | 1.000 | 0.325 | 0.001 | 1.000 | True |
