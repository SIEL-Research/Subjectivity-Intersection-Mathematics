# Experiment 008C

## Lithium `2^2P_1/2` Cross-State Transfer

E008C freezes three target-free predictions for the lithium-6/lithium-7
hyperfine interval ratio in the `2^2P_1/2` state:

- factorised base: `0.28399324742025683`;
- bilateral-mass response only: `0.28400802967617617`;
- CP-158 recursive sector response: `0.2840139905285925`.

The experiment transfers a lithium isotope rule from the E008B `2S_1/2`
target to a distinct electronic state. It is a within-lithium test, not an
atomic-universal test: CP-158 failed its known H/D portability audit.

The target source is fixed by DOI, but no reported magnetic-interaction
constant or uncertainty is present in this registration package. After public
registration, the two reported `2^2P_1/2` magnetic dipole constants are
transcribed once and converted to a raw interval ratio using the frozen
angular interval factors `3/2` and `2`.

## Registration state

`PREREGISTERED_NOT_EXECUTED`

This state becomes effective only after the registration commit, tag
`e008c-preregistration-v1.0.0`, GitHub Release, and DOI are public and verified.

Validate without measurements:

```bash
python3 experiments/008c_lithium_2p_cross_state_transfer/run.py \
  --validate-registration
```

Run tests:

```bash
python3 -m unittest \
  experiments/008c_lithium_2p_cross_state_transfer/test_run.py
```

Do not execute before public registration is verified.
