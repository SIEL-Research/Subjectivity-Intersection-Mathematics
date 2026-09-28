# E016 — Pointed-Braid CKM derivation confirmation

Status: **PREREGISTERED — NOT EXECUTED**

## Question

Does the fixed pointed-Braid source construction reproduce the declared CKM
modulus matrix without measured CKM values entering the construction phase?

This is a direct reproducibility confirmation of a known derivation, not a
blind discovery experiment. The expected output is frozen in advance.

## Frozen construction

The construction uses only the source records frozen in `frozen_input.json`:

1. nonidentity Braid-word order `(r1, r2, r121)`;
2. pointed axis map `(r1,r2,r121) -> (e2,e1,e3)`;
3. clock weights `(7,4,4)`;
4. matter incidence weights `(4,10,10)` in word order;
5. normalized Hellinger cross-state
   `q_i ∝ sqrt(clock_i * matter_i)`;
6. the source-derived hub-leaf pair-star response;
7. ascending left singular-vector ordering for the up/down matter operators.

Measured CKM values are loaded only after the matrix has been derived.

## Primary endpoint

The run passes only if all of the following hold:

- the source-derived cross-state and pair-star coefficients reproduce the
  frozen final law to absolute tolerance `1e-11`;
- the derived CKM modulus matrix reproduces the frozen matrix to absolute
  tolerance `1e-11`;
- the unitarity residual is below `1e-11`;
- all nine elements remain within five quoted standard deviations of the
  frozen measurement table;
- replacing the Braid clock by a uniform clock, breaking the pointing map, or
  removing the pair-star response changes the matrix by Frobenius distance
  greater than `1e-6`.

No coefficient, phase, sign, dictionary, exponent, threshold, or matrix entry
may be fitted or changed after execution begins.

## Single command

```bash
python3 run_confirmation.py
```

The command creates `RESULT.json`. No other analysis is part of this experiment.

## Claim on PASS

A PASS confirms that the fixed pointed-Braid construction is computationally
sufficient to reproduce its declared CKM matrix and its already reported
numerical agreement, and that three explicit structure-breaking controls do not
produce the same output.

Because the route was historically selected after CKM data had been inspected,
this experiment is a registered reproducibility confirmation, not a new
prospective prediction.
