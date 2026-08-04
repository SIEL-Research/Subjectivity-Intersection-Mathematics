# The Third Viewpoint: Live Emergence Demo

This browser-local demonstration lets a visitor run a new miniature experiment rather than watch a fixed animation.

Two recurrent systems, A and B, receive different signals and learn only a delayed reciprocal-recall task. The model contains no C state, O3 variable, third agent, pair identifier, carrier target, or O3-specific loss. After training, the demo uses frozen counterfactual inclusion-exclusion and interventions to test for an operational trace expected of an emergent third viewpoint.

The public sequence lets the visitor:

1. see the initially separate viewpoints of A and B;
2. train their interaction locally from zero;
3. enter A, B, or the emergent O3 viewpoint;
4. erase only the O3 trace;
5. replace it with a trace from another pair;
6. observe its self-re-entry across later joint states; and
7. inspect and export the complete numerical evidence.

## Run locally

From this directory:

    npm test
    npm run serve

Then open `http://localhost:4173`.

The default live run is intentionally small. Different seeds may produce supported, partial, or unsupported outcomes; the interface preserves the computed result.

## Scientific boundary

The visual O3 is a portal into a distributed operational signature, not a third state secretly inserted into the model. The demo operationalizes a trace expected of an emergent third viewpoint. It does not by itself establish consciousness or complete the ontological identification of O3.

The implementation is adapted from the browser-local engine used to communicate the audited Experiment 006A result. See the [Experiment 006A public record](https://doi.org/10.5281/zenodo.21785748).
