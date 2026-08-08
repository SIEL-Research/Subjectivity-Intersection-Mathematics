# E008E contamination ledger

## Target kept unopened

No numerical value for the complete second-order `K-40 4P` corrections
`delta A(P_1/2)`, `delta A(P_3/2)`, or `delta B(P_3/2)` was searched, opened,
or loaded before generation of the E008E prediction.

The pre-generation searches were limited to nuclear spin, magnetic dipole
moment, and electric quadrupole moment. The exact moment-source searches are
part of the construction history, not benchmark searches.

## Values already known before E008E

- The K-39 and K-41 total corrections and their `eta/zeta` decomposition were
  opened during E008D and CP-162.
- The alkali table entries for Li, Na, K-39, K-41, Rb, and Cs were visible in
  that history.
- These entries cannot serve as a new E008E independent target.

## K-40 status in the construction paper

The construction source `doi:10.1103/PhysRevA.78.032519` supplies common K
electronic `T1`, `T2`, and fine-structure inputs. Its displayed correction
table does not contain K-40. E008E uses no K-39 or K-41 correction value to
set the K-40 prediction.

## Nuclear quadrupole source discrepancy

INDC(NDS)-0833 page 23 prints `+0.603(6)`, `-0.750(8)`, and `+0.734(7)` b for
K-39, K-40, and K-41. Its cited primary paper,
`doi:10.1080/00268976.2018.1426131`, explicitly reports `60.3(6)`, `-75.0(8)`,
and `73.4(7)` millibarns. E008E therefore freezes `+0.0603(6)`, `-0.0750(8)`,
and `+0.0734(7)` b. The tenfold secondary transcription is recorded but not
used.

## Post-registration boundary

K-40 correction searches begin only after the registration commit, public
tag, Release, and DOI all resolve to the frozen prediction hash. If no
independent benchmark is found, the prediction remains open; the target is
not replaced.
