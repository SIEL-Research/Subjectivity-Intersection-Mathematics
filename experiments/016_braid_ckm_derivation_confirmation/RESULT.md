# E016 result — Pointed-Braid CKM derivation confirmation

Decision: **PASS**

The fixed pointed-Braid source construction reproduced the registered CKM
modulus matrix exactly:

\[
|V_{\mathrm{CKM}}|=
\begin{pmatrix}
0.9739619651 & 0.2266869484 & 0.0033343545\\
0.2265269160 & 0.9731130260 & 0.0416724717\\
0.0091458642 & 0.0407929649 & 0.9991257614
\end{pmatrix}.
\]

## Registered endpoints

| Endpoint | Result |
|---|---:|
| Frozen CKM maximum absolute residual | `0.0` |
| Unitarity residual | `8.514964801164752e-16` |
| Frobenius distance to frozen measurement table | `0.002540456248697957` |
| Maximum element pull | `4.41828324170494 sigma` |
| All nine elements within `5 sigma` | `PASS` |

The source-derived cross-state was

\[
q=(0.2949454706,\ 0.3525272647,\ 0.3525272647),
\]

and the pair-star coefficients were

\[
(q_3q_1,q_3q_2,0)
=(0.1039763200,\ 0.1242754723,\ 0).
\]

## Structure-breaking controls

| Control | Frobenius distance from the Braid output |
|---|---:|
| Uniform non-Braid clock | `0.06431185326470787` |
| Broken pointing | `0.15001250606157654` |
| Pair-star removed | `0.3280220949999376` |

All ten frozen tests passed. No coefficient, phase, sign, dictionary, exponent,
threshold, or matrix entry was changed after DOI-1 publication.

## Claim

This registered execution confirms that the fixed pointed-Braid source pipeline
is computationally sufficient to reproduce the declared CKM matrix, and that
the output depends on the tested Braid-specific clock, pointing, and pair-star
structure.
