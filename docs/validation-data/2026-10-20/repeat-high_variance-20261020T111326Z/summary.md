# Repeated experiment summary: repeat-high_variance-20261020T111326Z

Complete paired replicates in manifest: 60

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 20.31 ± 1.21 | 4.04 ± 0.25 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.02 ± 1.10 | 4.46 ± 0.24 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30/30 |
| persistent | after_restart_reuse | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.21 ± 1.56 | 4.50 ± 0.28 | 11.80 ± 7.18 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 30 | 29/30 (96.7%, 83.3–99.4%) | 22.87 ± 4.60 | 4.48 ± 0.29 | 11.43 ± 8.27 | 0.03 ± 0.18 | 0.00 ± 0.00 | 30/30 |
| persistent | mission | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.07 ± 1.22 | 4.49 ± 0.26 | 11.13 ± 7.88 | 0.03 ± 0.18 | 0.00 ± 0.00 | — |
| persistent | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.10 ± 1.21 | 4.49 ± 0.25 | 10.60 ± 7.54 | 0.07 ± 0.37 | 0.00 ± 0.00 | — |
| transient | mission | A | 30 | 29/30 (96.7%, 83.3–99.4%) | 22.74 ± 2.85 | 4.44 ± 0.55 | 0.10 ± 0.31 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| transient | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.19 ± 1.15 | 4.51 ± 0.24 | 0.10 ± 0.31 | 0.03 ± 0.18 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 30 | -0.37 [-4.23, 3.57] | -0.033 [-0.100, 0.000] | extend affected cells to 60 |
| transient | mission | 30 | 0.00 [-0.13, 0.13] | 0.033 [0.000, 0.100] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 240. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
