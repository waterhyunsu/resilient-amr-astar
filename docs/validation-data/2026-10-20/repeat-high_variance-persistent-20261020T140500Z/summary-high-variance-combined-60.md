# Repeated experiment summary: repeat-high_variance-20261020T111326Z, repeat-high_variance-persistent-20261020T140500Z

Complete paired replicates in manifest: 90

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 60 | 60/60 (100.0%, 94.0–100.0%) | 20.39 ± 1.06 | 4.04 ± 0.22 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 60 | 58/60 (96.7%, 88.6–99.1%) | 23.25 ± 5.71 | 4.53 ± 0.33 | 0.07 ± 0.25 | 0.07 ± 0.25 | 0.00 ± 0.00 | 60/60 |
| persistent | after_restart_reuse | A | 60 | 59/60 (98.3%, 91.1–99.7%) | 22.97 ± 5.74 | 4.58 ± 0.60 | 12.50 ± 7.83 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 60 | 59/60 (98.3%, 91.1–99.7%) | 22.55 ± 3.36 | 4.50 ± 0.27 | 10.10 ± 7.28 | 0.02 ± 0.13 | 0.00 ± 0.00 | 60/60 |
| persistent | mission | A | 60 | 60/60 (100.0%, 94.0–100.0%) | 22.12 ± 1.12 | 4.49 ± 0.23 | 10.70 ± 7.43 | 0.02 ± 0.13 | 0.00 ± 0.00 | — |
| persistent | mission | B | 60 | 60/60 (100.0%, 94.0–100.0%) | 22.11 ± 1.12 | 4.48 ± 0.23 | 12.42 ± 8.63 | 0.03 ± 0.26 | 0.00 ± 0.00 | — |
| transient | mission | A | 30 | 29/30 (96.7%, 83.3–99.4%) | 22.74 ± 2.85 | 4.44 ± 0.55 | 0.10 ± 0.31 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| transient | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.19 ± 1.15 | 4.51 ± 0.24 | 0.10 ± 0.31 | 0.03 ± 0.18 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 60 | -2.40 [-5.22, 0.42] | 0.000 [-0.050, 0.050] | extend affected cells to 60 |
| transient | mission | 30 | 0.00 [-0.13, 0.13] | 0.033 [0.000, 0.100] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 420. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
