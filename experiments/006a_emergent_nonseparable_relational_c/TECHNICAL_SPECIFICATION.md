# Experiment 006A Technical Specification

## State and task

The frozen Experiment 005 delayed reciprocal-recall system has a
24-dimensional recurrent state, 8-dimensional input, two 3-class receivers,
eight steps, and no signal after the intervention boundary. Training loss is
only the mean of the two reciprocal-recall cross-entropies.

## Nonseparable C projection

For matched trajectories `ab`, `a0`, `0b`, and `00`:

`C_t = H_t(ab) - H_t(a0) - H_t(0b) + H_t(00)`.

The two receiver blocks are retained separately for support and norm
measurements. The dual-independent-relay architecture makes the expression
zero to numerical precision because its two recurrent blocks are additive and
disconnected.

## Causal transport

`H_(t+1) = F(H_t(ab), x_t)`

`H_(t+1)^(-C) = F(H_t(ab) - C_t, x_t)`

The intervened next C is formed by replacing only the `ab` next state in the
same four-trajectory extractor. The transported contribution is

`Delta C_(t+1) = C_(t+1) - C_(t+1)^(-C)`.

The one-step reconstruction identity is audited numerically.

## Precision and reproducibility

All computation uses NumPy float64 and seeded `numpy.random.Generator` draws.
Model initialization, training batches, evaluation episodes, donor mapping,
and random controls are seed-fixed. Non-finite values fail execution.
