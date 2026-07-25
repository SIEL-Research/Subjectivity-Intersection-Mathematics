# Experiment 002 Preregistration

## Title

**A Blinded Test for Detecting Relational Carriers**

## Registration date

2026-07-25

## Registration rule

This preregistration is frozen by the GitHub commit that first contains:

- this document;
- `PREREGISTRATION_EMAIL.md`;
- the registered design in `README.md`;
- `run.py`;
- `test_run.py`; and
- `registration_manifest.json`.

Confirmatory generation must occur only after that commit has been pushed to
the public repository. The commit identifier and remote URL must be recorded
with the result.

## Question

Can a frozen, ground-truth-blinded analysis distinguish:

1. systems with no shared history-bearing state;
2. systems with a shared history-bearing state that is not a complete
   relational carrier; and
3. systems with a pair-indexed, jointly generated, history-bearing carrier
   that acts back upon both operational units?

## Registered classes and generators

- **Class 0:** `G0-I`, `G0-C`, `G0-D`, `G0-X`, and `G0-H`.
- **Class 1:** `G1-F`, the recurrent full-adder boundary.
- **Class 2:** `G2-P`, the path-ordered permutation carrier, and `G2-M`, the
  independently constructed finite-matrix carrier over GF(3).

The source code contains the complete transition, counterfactual, observation,
noise, split, and scoring rules.

## Blindness and sealing

The generator writes an observed table and a separate ground-truth table. The
analysis function accepts only the observed table. Predictions and gate
decisions are written and SHA-256 hashed before the scoring function is given
the ground truth.

This is procedural ground-truth blindness in an executable synthetic
benchmark. Because the generator source and seed are eventually public, it is
not described as permanent cryptographic secrecy.

## Frozen transfer levels

- **T1:** new histories for registered pairs.
- **T2:** unseen recombinations of registered operational-unit identities.
- **T3:** pairs composed only of held-out operational-unit identities.
- **Second-mechanism transfer:** `G2-M` is excluded from threshold design and
  is scored with the unchanged rules.

## Frozen analysis

The analysis uses registered, label-invariant mismatch rates and matched
counterfactual margins. It evaluates joint generation, history dependence,
selective reset, pair substitution, bilateral feedback, common-driver
separation, and gauge consistency. It contains no fitted confirmatory
classifier and receives no family labels or latent states.

The exact thresholds are recorded in `registration_manifest.json` and enforced
by `run.py`.

## Primary endpoint

Three-class balanced accuracy on each of T1, T2, and T3, together with the
false Class 2 declaration rate on the combined true Class 0 and Class 1
datasets.

## Required acceptance targets

Every condition must pass:

- balanced accuracy at least `0.80` at T1, T2, and T3;
- recall at least `0.70` for each class at each transfer level;
- false Class 2 declaration rate at most `0.10` on true Class 0 and Class 1;
- Class 2 recall at least `0.80` on `G2-P`;
- Class 2 recall at least `0.70` on `G2-M`; and
- unchanged classification in at least `0.95` of registered gauge replicas.

No secondary observation may rescue failure of a required target.

## Confirmatory seed and command

The confirmatory master seed is `2026072502`.

From the repository root, after the registration commit is visible on GitHub:

    python3 experiments/002_blinded_relational_carrier_discrimination/run.py \
      --mode confirmatory \
      --out-dir experiments/002_blinded_relational_carrier_discrimination/results \
      --check

The result directory must not already exist. The program refuses to overwrite
an existing confirmatory run.

## Falsification

The registered claim is unsupported if any required acceptance target fails,
if `G1-F` is promoted to Class 2, if gauge relabelling changes the decision
beyond the registered tolerance, if prediction hashing occurs after
unblinding, or if the registered source and manifest hashes do not match.

## Interpretation boundary

Success establishes only that the frozen method discriminates the registered
synthetic classes. It does not establish a relational carrier in an external
system, identify a carrier with subjectivity, or prove ontological
irreducibility.
