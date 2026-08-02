# Preregistration Correspondence Record

## Subject

Subjectivity-Intersection Mathematics Experiment 003: Final Preregistration Specification for a Class 2 Relational Carrier and Self-Reentrant O3 in Subjectivity Agents

## Recipients

Luke Casson Leighton, Marcel, Thomas, C.A.T., and the D12RG research group.

## Correspondence provenance

- Initial plan sent: 2026-08-02 07:16 JST.
- Final revised specification sent: 2026-08-02 22:07 JST.
- RFC Message-ID of the final revised specification:
  `<D8EF8888-A92A-4327-BB12-8AFF0B52B32C@siel.global>`.

The text below is the consolidated registered-plan record. It preserves the
substantive specification sent to the group and adds the three final technical
clarifications received after that message and before registration.

## Registered plan

Experiment 003 applies the Class 0, Class 1, and Class 2 distinction developed
in Experiment 002 to generated states from the subjectivity-agent system that
has previously been developed in a separate private collaboration.

The experiment has two independent phases. Phase A tests whether an unmodified
third agent runtime can retain an ordered, pair-specific relational state and
return it to both source agents in a manner satisfying all frozen Class 2
gates. Phase B adds an explicit self-reentry path and tests whether the retained
third state changes its own subsequent mediation action while independently
retaining the full Class 2 result.

The confirmatory sample contains 128 disjoint pairs and 256 previously unused
agents. Sixty-four pairs compare AABB with ABAB, and sixty-four compare BBAA
with BABA. Every A and B trajectory is generated once and cloned. Complete
runtime state and memory are canonically hashed immediately before C returns;
the hashes must be exactly identical across the two histories. A mismatch is a
retained technical failure and the pair is not replaced.

The Class 2 thresholds are fixed at 0.0672948624 for joint generation,
0.0551607125 for history irreducibility, 0.0868509258 for intervention
sensitivity, 0.0707154800 for pair specificity, and 0.0654685289 for bilateral
feedback. Gauge relative error must not exceed 1e-10. The O3 thresholds are
0.05 for retained-state, action, and bilateral effects, with erasure and
feedback-removal tolerances of 1e-10.

All vector distances are RMS Euclidean distances. Text-derived 24-dimensional
packet embeddings have unit L2 norm. `z_C` and the action are 24-dimensional
float64 vectors. Evaluation order, normalization, and numerical tolerances are
frozen in the public source.

The primary Wilson decision is made jointly across all 128 pairs: at least 112
positive pair-level decisions are required, and at most 6 false Class 2
declarations are allowed for each registered Class 0 or Class 1 control. The
two 64-pair history families are reported separately. If either family has
fewer than 52 raw passes, pooled success does not establish uniform transfer
across both history families.

The capacity-matched generic recurrent control uses the same differentiated A
and B inputs, ordered history, total 48-dimensional recurrent state, seven
24-by-24 matrices, action channel, return channels, and seeds allocated by the
registered rule. Its optimization budget and the candidate's optimization
budget are both zero training steps, zero hyperparameter searches, zero seed
selection, and zero result-dependent reinitializations. A matched-control pass
will be reported as implementation non-uniqueness.

The public registration contains the hypothesis, definitions, thresholds,
controls, complete public connection and scoring code, private-core commit and
source hashes, and output schema. It is frozen as a GitHub Release before the
confirmatory run. The Release is intended to trigger the repository's Zenodo
archiving integration. The confirmatory experiment is executed only after the
registration is public, and its outputs are published whether the hypotheses
pass or fail.

The claim remains operational. Success would establish a transferable Class 2
construction and, in Phase B, constructive sufficiency of the explicit O3
self-reentry architecture. It would not establish spontaneous emergence,
ontological subjectivity, or validation of Subjectivity-Intersection Ontology.

## Final methodological review incorporated

Marcel's final review found no remaining major methodological objection subject
to three clarifications. This registration incorporates all three:

1. exact complete-state and memory hashing for matched A and B states;
2. a pooled 128-pair primary Wilson decision with 64-pair family analyses kept
   secondary; and
3. frozen distance metrics, normalization, matrix dimensions, parameter count,
   and a zero optimization budget for the matched recurrent control.
