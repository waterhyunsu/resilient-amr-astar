# Repeated experiment summary: repeat-fixed-20261020T091155Z

Complete paired replicates in manifest: 30

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 20.26 ± 0.39 | 4.02 ± 0.05 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 30 | 29/30 (96.7%, 83.3–99.4%) | 23.06 ± 3.80 | 4.47 ± 0.17 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30/30 |
| persistent | after_restart_reuse | A | 30 | 28/30 (93.3%, 78.7–98.2%) | 25.10 ± 9.84 | 4.79 ± 0.81 | 14.20 ± 5.96 | 0.07 ± 0.25 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.49 ± 0.60 | 4.57 ± 0.10 | 13.27 ± 10.07 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30/30 |
| persistent | mission | A | 30 | 29/30 (96.7%, 83.3–99.4%) | 23.19 ± 4.39 | 4.55 ± 0.11 | 12.27 ± 5.73 | 0.17 ± 0.59 | 0.00 ± 0.00 | — |
| persistent | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.48 ± 0.47 | 4.56 ± 0.07 | 13.93 ± 7.57 | 0.10 ± 0.31 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 30 | -0.93 [-5.47, 3.87] | 0.067 [0.000, 0.167] | extend affected cells to 60 |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 180. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
