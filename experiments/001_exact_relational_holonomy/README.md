# Experiment 001 — Exact Relational Holonomy

## Role

This is the first calibration experiment in the Relational Carrier
Discrimination Benchmark.

It asks whether a frozen finite analysis can distinguish a path-ordered,
history-bearing relational state from prespecified alternatives that observe
only current participant states, separate participant histories, shared event
counts, a static common object, or coordinate labels.

This experiment does **not** model or establish subjectivity. It establishes an
exact test fixture for deciding whether the proposed evidence gates can detect
a relational carrier when one is known to exist.

## Hypothesis

Two participants, `A` and `B`, apply involutive actions to a four-label
relational domain.

```text
A = transposition (0 1)
B = transposition (1 2)
```

Each participant acts twice. Therefore every audited history has the same:

- present individual endpoints;
- separate local histories `AA` and `BB`;
- external event counts;
- static common-object value.

The order of their joint actions nevertheless matters because the actions do
not commute.

The two histories

```text
AABB
ABAB
```

have identical registered null information, but their path-ordered carriers
are different. `AABB` returns the carrier to the identity. `ABAB` produces a
nontrivial order-three permutation that changes the subsequent readout to both
participant probes.

The experiment is falsified if this distinction disappears, if either
participant can generate the same carrier alone, if partner substitution does
not remove the effect, or if a simultaneous relabeling changes the decoded
result.

## Prespecified alternatives

The registered null signature contains:

- current state of `A`;
- current state of `B`;
- the separate local history of each participant;
- the common event counts;
- a constant pre-existing common object.

These cover exact finite versions of:

- independent endpoint dynamics;
- instantaneous coupling without relational memory;
- separate individual memory;
- a shared external driver summarized by event counts;
- reconstruction of a static common object.

A fully unrestricted model that receives the complete interleaved history can
reconstruct the carrier. The experiment therefore does not claim uniqueness
of the latent representation or separation from every possible history model.

## Seven-gate audit

- **J — Joint generation:** `ABAB` is nontrivial while `AA` and `BB` each
  return to identity.
- **H — History irreducibility:** endpoint- and null-matched histories produce
  different carrier states and future readouts.
- **I — Intervention sensitivity:** resetting the carrier or replacing
  `ABAB` by the matched order `AABB` changes the readout.
- **P — Pair specificity:** replacing `B = (1 2)` by the disjoint partner
  action `B* = (2 3)` makes the actions commute and removes the holonomy.
- **G — Gauge invariance:** all 24 simultaneous relabelings of the four-label
  domain preserve exact conjugacy, cycle type, and decoded feedback.
- **N — Null-model separation:** all six histories have one registered null
  signature but more than one relational carrier.
- **T — Frozen transfer:** the unchanged rules pass every combination of six
  histories and 24 coordinate gauges.

## Run

From the repository root:

```bash
python3 experiments/001_exact_relational_holonomy/run.py --check
```

The command writes:

```text
results/summary.json
results/history_census.csv
results/gauge_audit.csv
```

The executed result and its scientific boundary are recorded in
[RESULT.md](RESULT.md).

## Acceptance target

```text
status = ok
histories_audited = 6
distinct_null_signatures = 1
distinct_relational_carriers = 3
holonomy_order = 3
gauge_history_cases = 144
all seven evidence gates = true
```

## Interpretation boundary

A successful run proves an exact property of this finite constructed system:
ordered interaction can retain relational information that is absent from
current endpoints, separate local histories, and order-free shared counts.

It does not prove:

- that human pairs generate the same carrier;
- that noncommutativity by itself is subjectivity;
- that the carrier is ontologically exhaustive or irreducible;
- that the carrier is the unique latent explanation;
- that an unrestricted complete-history model would fail.

The next stage is to convert the exact distinctions audited here into a
synthetic noisy benchmark and then into an empirical dyadic protocol.
