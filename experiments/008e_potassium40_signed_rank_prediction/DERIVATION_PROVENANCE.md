# E008E derivation provenance

CP-162 established that the magnetic rank-one and electric rank-two channels
must each be connected to their physical reduced operator before the two
second-order returns are composed. E008E applies that fixed construction to a
new nuclear standpoint, K-40.

For nuclear spin `I`, magnetic moment `mu`, quadrupole moment `Q`, electronic
matrix elements `T1,T2`, and positive fine-structure interval `Delta E`, the
construction is

`eta = [(I+1)(2I+1)/I] mu^2 T1^2 / Delta E`,

`zeta = [(I+1)(2I+1)/I] sqrt[(2I+3)/(2I-1)] mu Q T1 T2 / Delta E`.

The general-spin return coefficients used for K-40 are

`c_eta = 1/[6 I(I+1)(2I+1)]`,

`c_zeta = c_eta sqrt[3(2I-1)(2I+3)/5]`,

`delta A(P_1/2) = c_eta eta + c_zeta zeta`,

`delta A(P_3/2) = (c_eta/2) eta - (c_zeta/10) zeta`,

`delta B(P_3/2) = I(2I-1)c_eta eta + [3I/(2I+3)]c_zeta zeta`.

The formulas reproduce the published explicit coefficients for `I=1`,
`3/2`, `5/2`, and `7/2` before extension to `I=4`.

No K-40 second-order correction, `eta`, or `zeta` value occurs in the
construction inputs. All electronic and nuclear input uncertainties or
display-rounding widths are propagated by a deterministic corner envelope.
