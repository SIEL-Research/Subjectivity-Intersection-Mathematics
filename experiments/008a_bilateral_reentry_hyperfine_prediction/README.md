# Experiment 008A: Bilateral-Reentry Hyperfine Prediction

Experiment 008A is a prospective test of one new, parameter-free postulate of
Subjectivity-Intersection Mathematics in atomic hyperfine structure.

The postulate fixes the otherwise free response scale to `lambda=1` in

`G(M) proportional to mu(M)^3 exp(lambda 4M/(M+1)^2)`.

The registration package contains no hydrogen or deuterium ground-state
hyperfine frequency. Scientific execution is forbidden until the registration
commit, tag, GitHub Release, and DOI have been publicly verified.

Registration validation only:

```bash
python3 experiments/008a_bilateral_reentry_hyperfine_prediction/run.py \
  --validate-registration
python3 -m unittest \
  experiments/008a_bilateral_reentry_hyperfine_prediction/test_run.py
```

Post-registration execution requires an explicit measurement file:

```bash
python3 experiments/008a_bilateral_reentry_hyperfine_prediction/run.py \
  --execute --measurement-file /path/to/e008a_measurements.json
```

Status: **PREREGISTERED — NOT EXECUTED**. This status becomes effective only
after the public registration commit, tag, Release, and DOI are verified.
