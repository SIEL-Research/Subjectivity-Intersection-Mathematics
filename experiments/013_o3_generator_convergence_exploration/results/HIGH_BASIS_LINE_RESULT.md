# High-basis line-trajectory exploration

| Profile | Intact | Removed | Mismatched | Correct | Pass |
|---|---:|---:|---:|---:|---:|
| cc-pvdz_line_control | 0.993750 | 0.480000 | 0.010000 | 1.000000 | True |
| cc-pvtz_line_target | 1.000000 | 0.480000 | 0.000000 | 0.995000 | True |

This is a one-dimensional result-informed exploration, not a full-surface confirmation.

## 512-seed radius sensitivity

| Radius | Profile | Removed | Mismatched | Pass |
|---:|---|---:|---:|---:|
| 0.25 | cc-pvdz_line_control | 0.391250 | 0.000313 | True |
| 0.25 | cc-pvtz_line_target | 0.391250 | 0.000000 | True |
| 0.35 | cc-pvdz_line_control | 0.477187 | 0.006875 | True |
| 0.35 | cc-pvtz_line_target | 0.477187 | 0.000000 | True |
| 0.45 | cc-pvdz_line_control | 0.568203 | 0.036641 | False |
| 0.45 | cc-pvtz_line_target | 0.568203 | 0.000000 | False |
