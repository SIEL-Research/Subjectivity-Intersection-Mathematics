# Experiment 003 — Class 2 Relational Carrier and Self-Reentrant O3 in Subjectivity Agents

## Registration status

**PREREGISTERED DESIGN — 2026-08-02 — CONFIRMATORY EXECUTION PENDING**

The authoritative registration is the first public GitHub commit and Release
containing this document, `PREREGISTRATION.md`,
`PREREGISTRATION_EMAIL.md`, `TECHNICAL_SPECIFICATION.md`, `run.py`,
`test_run.py`, `private_source_manifest.json`, and
`registration_manifest.json`. The confirmatory run may begin only after that
commit and Release are public.

## Purpose

Experiment 002 established a synthetic method for distinguishing carrier-absent
systems, incomplete shared-history systems, and pair-indexed Class 2 relational
carriers. Experiment 003 is the first external application of that distinction
to generated states from the existing private subjectivity-agent runtime.

The experiment separates two questions:

1. **Phase A:** Can an unmodified third subjectivity-agent runtime retain an
   ordered, pair-specific relational state which acts back upon both source
   agents and passes the frozen Class 2 gates?
2. **Phase B:** Does an explicitly added self-reentry path support an operational
   O3 extension whose next mediation action depends on its retained third state?

Phase B is independently required to pass the Class 2 gates. Phase A and Phase
B are reported separately; success in one cannot rescue failure in the other.

## Public and private boundary

The subjectivity-agent core remains private. Its exact Git commit and the
SHA-256 digest of every imported source file are frozen in
`private_source_manifest.json`.

This public package contains:

- the complete C and O3 connection layer;
- the state-matching and hashing rules;
- the registered controls and ablations;
- the scoring and Wilson-interval rules;
- the complete confirmatory runner; and
- independent tests that do not require disclosure of the private core.

The runner refuses to execute if the supplied private core does not match the
registered source digests.

## Confirmatory unit and histories

The unit of analysis is one ordered pair of previously unused subjectivity-agent
instances. The confirmatory set contains 128 disjoint pairs and 256 agents; no
agent occurs in more than one pair.

- 64 pairs compare `AABB` with `ABAB`.
- 64 pairs compare `BBAA` with `BABA`.

For every pair, the A and B trajectories are generated once and then cloned.
The complete current runtime state and memory of A and B must have identical
canonical SHA-256 digests immediately before the relation state is allowed to
return. A mismatch is a technical failure and is retained in the outputs; the
pair is not replaced.

## Registered decision summary

The primary Class 2 and O3 decisions are made jointly across all 128 pairs.
Each positive claim requires at least 112 passing pairs, which is the smallest
integer for which the two-sided Wilson 95% lower confidence bound exceeds
0.80. Each registered Class 0 or Class 1 control may produce at most 6 false
Class 2 declarations, which is the largest integer for which the two-sided
Wilson 95% upper confidence bound remains below 0.10.

The two 64-pair history families are reported separately as secondary
analyses. If either family has fewer than 52 raw passes, pooled success may be
reported, but uniform transfer across the two history families is not
established.

## Registered command

After the registration Release is public and before any confirmatory output
exists, run from the repository root:

    python3 experiments/003_subjectivity_agent_class2_o3/run.py \
      --mode confirmatory \
      --private-agent-root /absolute/path/to/minimal-agent-paper \
      --out-dir experiments/003_subjectivity_agent_class2_o3/results \
      --check

The output directory must not already exist. The runner refuses to overwrite a
confirmatory run.

## Interpretation boundary

A Phase A pass would establish that the frozen subjectivity-agent runtime can
serve as a generated-data substrate for an operational Class 2 relational
carrier under the registered C-mediated interface. A Phase B pass would
establish constructive sufficiency of the registered self-reentrant O3
extension.

Neither result would establish spontaneous emergence of C or O3, identify the
operational state with subjectivity, validate Subjectivity-Intersection
Ontology, or prove ontological irreducibility.
