# Foundations for Relational-Carrier Research

## Purpose

Subjectivity-Intersection Mathematics asks whether interaction between
distinct subjects or viewpoints can generate a relational state that is not
reducible to either participant alone.

The immediate scientific target is not a complete mathematical representation
of subjectivity. It is a narrower and testable question:

> Can distinct participants jointly generate a history-bearing relational
> carrier that subsequently changes both participants and can be distinguished
> from common causes, reconstruction, shared coordinates, synchronization, and
> analytical artifacts?

This document defines that target, its evidential requirements, and the
experimental design principles that follow from it.

## 1. Internal states and observable projections

Let the internal states of two participants be \(x_A(t)\) and \(x_B(t)\).
An experiment does not have unrestricted access to those states. It observes
projections such as reports, actions, physiological measurements, or neural
signals:

\[
y_A(t)=\Pi_A(x_A(t)), \qquad
y_B(t)=\Pi_B(x_B(t)).
\]

The distinction between internal state and observable projection is essential.
Failure to reconstruct an internal state from an observation does not by
itself establish a new relational entity. Conversely, a scientifically useful
relational model need not claim to exhaust the participants' subjectivity.

## 2. Instantaneous relation and relational carrier

An instantaneous relational quantity can be written as

\[
R(t)=r\bigl(y_A(t),y_B(t)\bigr).
\]

This may measure agreement, distance, synchrony, mutual information, or
another relation between current observations. Such a quantity is not yet a
relational carrier. It may contain no state or history of its own.

A candidate relational carrier has its own dynamics:

\[
\dot c(t)=F_C\bigl(c(t),x_A(t),x_B(t),u(t)\bigr),
\]

and acts back upon the participants:

\[
\dot x_A(t)=F_A\bigl(x_A(t),c(t),u_A(t)\bigr),
\]

\[
\dot x_B(t)=F_B\bigl(x_B(t),c(t),u_B(t)\bigr).
\]

The central structure is therefore not merely

\[
C=r(A,B),
\]

but a coupled, history-dependent system:

\[
A \leftrightarrow C \leftrightarrow B.
\]

The notation \(C\) denotes a candidate until the evidential conditions below
have been met.

## 3. Epistemic carrier and ontological scope

We distinguish three objects:

\[
R_{AB}: \text{the underlying relation between } A \text{ and } B,
\]

\[
C_E=O(R_{AB}): \text{the experimentally accessible relational carrier},
\]

\[
S_{AB}: \text{a more complete ontological structure that may include
subjectivity}.
\]

The research program studies \(C_E\). It does not assume

\[
C_E=S_{AB}.
\]

This boundary is methodological rather than rhetorical. A model of \(C_E\)
may be deterministic, stochastic, or hybrid. What it may not do without
additional justification is claim that its observable state space is an
exhaustive and exclusive representation of subjectivity.

## 4. Three distinct levels of non-reduction

The following claims must not be conflated.

### 4.1 Viewpoint dependence

What is observable or reportable from viewpoint \(A\) may differ from what is
observable or reportable from viewpoint \(B\).

### 4.2 Relational irreducibility

A relational carrier \(C_E\) may fail to belong to \(A\) alone or \(B\) alone
and may not be recoverable from their separately modelled present states.

### 4.3 Ontological non-exhaustiveness

Even a joint objective model containing \(A\), \(B\), and \(C_E\) may fail to
exhaust the existence of subjectivity.

Viewpoint dependence does not prove relational irreducibility. Relational
irreducibility does not prove ontological non-exhaustiveness. Each level
requires its own argument and evidence.

## 5. Participation-indexed relational states

A relational state may depend on both participant identity and shared
history. We denote such a state by

\[
C^{AB}_{H},
\]

where \(A\) and \(B\) identify the participants and \(H\) identifies their
shared interaction history.

This gives a precise distinction:

\[
\text{objective describability}
\neq
\text{participatory access}.
\]

An external investigator may be able to describe or predict properties of
\(C^{AB}_{H}\). That does not imply that a third party, without entering the
same relation and history, can use, reproduce, or inherit the state in the
same way as \(A\) and \(B\).

The initial research claim is therefore participation-indexicality, not
external indescribability.

## 6. Evidence gates for a relational carrier

A candidate \(C_E\) is accepted only if it passes all seven gates:

\[
E_C=J \land H \land I \land P \land G \land N \land T.
\]

### J — Joint generation

The candidate arises through the interaction of \(A\) and \(B\). Models based
on \(A\) alone or \(B\) alone do not reproduce the effect.

### H — History irreducibility

When current participant states are matched as closely as the experiment
allows, different shared histories still produce different future joint
dynamics.

### I — Intervention sensitivity

Selective disruption of the physical, symbolic, or procedural realization of
the candidate changes subsequent joint dynamics. The intervention must target
an operational realization, such as a shared code or interaction history,
rather than an unobservable latent variable by name.

### P — Pair specificity

The effect depends on the particular pairing. Partner substitution,
cross-pair transfer, or history reassignment weakens or removes it under
appropriately matched conditions.

### G — Gauge invariance

The claimed relational effect survives admissible changes of coordinates,
labels, common reference frames, or representational conventions. A
coordinate-dependent statistic alone is insufficient.

### N — Null-model separation

The candidate outperforms a prespecified family of strong alternative models,
including common drivers, reconstruction of a pre-existing object, ordinary
synchronization, shared-coordinate transformations, individual memory, and
analytical artifacts.

This gate does not require the impossible claim that every conceivable common
cause has been eliminated. It requires separation from the strongest
realistic alternatives specified for the experiment.

### T — Frozen transfer

The definitions, analysis pipeline, thresholds, and decision rules are frozen
before transfer to new pairs, tasks, or systems. Success after silent
redefinition does not count as transfer.

The gates are evaluated separately. They are not compressed into one
scale-dependent composite score.

## 7. Relational holonomy

A history-bearing carrier suggests a path-dependence test. Suppose two
experimental paths return the observable individual and environmental
variables to approximately the same endpoint:

\[
(A_t,B_t,U_t)\approx(A'_t,B'_t,U'_t),
\]

while their relational histories differ:

\[
H_{AB}\neq H'_{AB}.
\]

Relational holonomy is present when the future joint dynamics remain
distinguishable:

\[
P(Y_{\mathrm{future}}\mid A_t,B_t,U_t,H_{AB})
\neq
P(Y_{\mathrm{future}}\mid A'_t,B'_t,U'_t,H'_{AB}).
\]

This result becomes evidence for a relational carrier only if it also passes
the pair-specificity, intervention, gauge, and null-model gates. Path
dependence by itself may be explained by unmeasured individual memory or
environmental state.

## 8. Dyadic experiment architecture

The first experimental program should use the following sequence:

1. **Individual baseline:** Measure each participant performing the task
   separately and estimate
   individual memory, strategy, and response variability.

2. **Joint generation:** Ask the pair to create a shared code, classification,
   strategy, convention, or predictive procedure that neither participant
   possessed beforehand.

3. **Stabilization:** Continue interaction until the shared construction
   supports reproducible performance and identifiable relational dynamics.

4. **Endpoint matching:** Construct trials in which present individual
   observables and external conditions are matched as closely as possible
   while shared histories differ.

5. **Selective perturbation:** Apply partner substitution, history
   reassignment, interaction-order reversal, shared-code disruption, or
   another intervention aimed at the relation rather than at general task
   performance.

6. **Return and readout:** Restore matched external conditions and measure
   whether the pair returns to the same joint dynamics, recovers its prior
   state, or reorganizes.

7. **Frozen transfer:** Apply the unchanged protocol and decision rules to new
   pairs and, later, to a different task or physical realization.

The decisive comparison is not whether two people synchronize. It is whether
participant- and history-specific joint dynamics survive present-state
matching, defeat strong alternatives, and respond selectively to relational
intervention.

## 9. Interpretation ladder

Results will be reported at four separate levels:

1. **Computed result** — what the registered analysis directly returns.
2. **System interpretation** — what the result implies for the tested dynamical
   model.
3. **Relational-carrier inference** — whether all seven evidence gates are
   passed.
4. **Ontological hypothesis** — how the carrier may relate to subjectivity,
   without treating the experimental inference as an exhaustive ontology.

A successful experiment would first establish evidence for \(C_E\). It would
not by itself prove a complete ontology of subjectivity.

## 10. Research provenance

These foundations were sharpened through discussions with Luke, Marcel, and
Pasquale.

- Pasquale clarified the separation between internal state, observable
  projection, instantaneous relation, and a relational carrier with its own
  dynamics, and proposed a perturbation-based experimental sequence.
- Marcel clarified the boundary between an experimentally accessible carrier
  and ontological subjectivity, and consolidated the evidence requirements
  into a strict set of independent gates.
- Luke emphasized triadic closure, participant-specific knowledge, and the
  inseparability of generated knowledge from the participants and history
  through which it was formed.

The formulation presented here, including its remaining limitations and
errors, is the responsibility of the author.

## 11. Next implementation target

The next public experiment will be a **Relational Carrier Discrimination
Benchmark**. It will compare a stateful relational-carrier model against
prespecified alternatives representing:

- independent individual dynamics;
- a shared external driver;
- reconstruction of a pre-existing common object;
- a common-coordinate or gauge transformation;
- instantaneous coupling without relational memory;
- individual memory without a relational state;
- analytical artifacts introduced by the observation or fitting procedure.

The benchmark will publish its hypotheses, executable code, inputs, outputs,
acceptance checks, and interpretation boundaries together.
