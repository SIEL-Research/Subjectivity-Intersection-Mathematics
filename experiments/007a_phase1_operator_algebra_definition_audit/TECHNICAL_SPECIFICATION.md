# Experiment 007A Phase 1 Technical Specification

## Corrected D12RG object

The comparison target is the seven-dimensional rational regular-matrix algebra represented by the Paper 5.3 basis. The ordered basis exponents are:

`(5,1,11,7,10,2,0)`.

The character exponents are:

`(0,1,2,5,7,10,11)`.

The generator has exact order 12 and minimal polynomial, in ascending coefficient order,

`(-1,2,-1,-1,1,1,-2,1)`.

The runner treats the seven printed matrices as a basis, not as a seven-element group. It solves every ordered matrix product over exact rational arithmetic and writes its seven structure coefficients.

## Exact product reduction

For basis matrices `M_i` and `M_j`, the runner computes `M_i M_j` and solves:

`M_i M_j = sum_k c_ijk M_k`.

All coefficients are exact `fractions.Fraction` values. Closure means closure of the seven-dimensional linear span. Set closure is reported separately and is expected to fail for at least one ordered basis product.

## SIO completeness criteria

The source inventory uses the frozen Experiment 006, 006R, and 006A records. The operator-algebra definition is complete only if one source-defined finite primitive basis, typed signature, product rule, invalid-case representation, identity/inverse rule, and canonical table rule are all present.

The audit does not infer a basis from prose or assemble one from interventions after the outcome is known.

## Witness-set correction

A later empirical extraction phase must use a frozen witness set. A globally nonidentity operator may fix individual inputs, so it must not be required to change every state. This Phase 1 audit only verifies whether such a witness-set rule already exists in the frozen sources.

## Canonicalisation correction

A later comparison must canonicalise by registered structural invariants before comparison. The four automorphisms of C12 cannot be used after inspection to select between `(1,5)` and `(1,7)`.

## Failure routing

The primary classifications in `PREREGISTRATION.md` exhaust all completed audit states. Provenance failure aborts before classification. D12RG definition failure takes precedence over SIO completeness. SIO incompleteness blocks the independent comparison without modifying the published Phase 2 result.

## Outputs

- `summary.json`
- `d12_basis_product_structure.csv`
- `RESULT.md`
- `output_manifest.json`
