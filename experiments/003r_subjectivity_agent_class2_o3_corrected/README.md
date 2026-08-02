# Experiment 003R — Corrected Class 2 Relational Carrier and Self-Reentrant O3

## Registration status

**PREREGISTERED CORRECTED DESIGN — 2026-08-03 — EXECUTION PENDING**

Experiment 003R is a new preregistration informed by the invalid confirmatory
run of Experiment 003. It does not alter the original registration, execution
artifacts, or technical-failure report.

Experiment 003 was not scientifically evaluable because its runner substituted
a donor B input while constructing a new C instead of inserting another pair's
completed C into unchanged recipient A and B return channels. It also omitted
several registered Phase B controls. Experiment 003R corrects both defects
before any new confirmatory execution.

## Corrected confirmatory boundary

- The new sample is `P2000` through `P2127`; all Experiment 003 pairs are
  excluded.
- The new primary seed is `20260813`.
- Pair specificity is tested by constructing a completed donor-pair C and
  inserting it into fixed recipient A and B return paths.
- All eleven registered Phase B controls are executed and receipted.
- The runner stops if the registered and executed Phase B control inventories
  differ.
- Distances are archived at `K_AB`, carrier, `z_C`, mediation action, A, and B.
- No confirmatory result is included in this registration package.

## Registered command

Run only after the registration commit and Release are public:

    python3 experiments/003r_subjectivity_agent_class2_o3_corrected/run.py \
      --mode confirmatory \
      --private-agent-root /absolute/path/to/minimal-agent-paper \
      --out-dir experiments/003r_subjectivity_agent_class2_o3_corrected/results \
      --check

The output directory must not exist. The runner refuses to overwrite it.

## Interpretation boundary

A successful result would establish only the operational sufficiency and
held-out transfer of the registered Class 2 and O3 constructions. It would not
establish spontaneous emergence, identify an executable carrier with
subjectivity, validate Subjectivity-Intersection Ontology, or establish
ontological irreducibility.
