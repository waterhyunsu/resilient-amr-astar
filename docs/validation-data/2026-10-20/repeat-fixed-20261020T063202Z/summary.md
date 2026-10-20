# Repeated experiment summary: repeat-fixed-20261020T063202Z

Complete paired replicates in manifest: 60

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 30 | 29/30 (96.7%, 83.3–99.4%) | 21.11 ± 4.79 | 4.02 ± 0.08 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.31 ± 0.42 | 4.49 ± 0.08 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30/30 |
| persistent | after_restart_reuse | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.35 ± 0.55 | 4.55 ± 0.09 | 14.57 ± 6.45 | 0.03 ± 0.18 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.62 ± 0.44 | 4.59 ± 0.08 | 13.03 ± 11.85 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30/30 |
| persistent | mission | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.51 ± 0.43 | 4.57 ± 0.07 | 18.00 ± 7.76 | 0.07 ± 0.25 | 0.00 ± 0.00 | — |
| persistent | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.39 ± 0.41 | 4.54 ± 0.08 | 16.57 ± 7.95 | 0.10 ± 0.31 | 0.00 ± 0.00 | — |
| transient | mission | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.31 ± 0.48 | 4.54 ± 0.08 | 0.33 ± 0.48 | 0.13 ± 0.35 | 0.00 ± 0.00 | — |
| transient | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.44 ± 0.30 | 4.57 ± 0.06 | 0.10 ± 0.31 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 30 | -1.53 [-6.30, 3.73] | 0.000 [0.000, 0.000] | extend affected cells to 60 |
| transient | mission | 30 | -0.23 [-0.43, -0.03] | 0.000 [0.000, 0.000] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 240. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
