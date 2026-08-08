# Experiment 008D

## PySCF potassium mixed-rank prospective prediction

E008D freezes a zero-fit prediction for the ratio of the complete second-order
hyperfine corrections to the magnetic-dipole constant of the lowest neutral
potassium `4P_1/2` state:

`delta A(39K) / delta A(41K) = 1.4239826742729131`.

The M1-M1-only control is `3.319224048274411`. The large separation makes this
a direct test of the rank-one/rank-two composition generated in CP-161.

The prediction was generated from four PySCF electronic coordinates and
independently published nuclear moments. No benchmark correction value was
loaded and no coefficient was fitted.

## Registration state

`PREREGISTERED_NOT_EXECUTED`

This state becomes effective only after the registration commit, tag
`e008d-preregistration-v1.0.0`, public GitHub Release, and DOI are verified.

Validate without benchmark input:

```bash
python3 experiments/008d_pyscf_potassium_mixed_rank_prediction/run.py \
  --validate-registration
```

Reproduce the PySCF prediction with the pinned environment:

```bash
python3 experiments/008d_pyscf_potassium_mixed_rank_prediction/generate_prediction.py \
  --output /tmp/e008d-prediction.json
```

After public registration, extract the two frozen-source corrections into the
measurement schema and execute once into a new output directory.
