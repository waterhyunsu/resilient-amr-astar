# Repeated experiment summary: repeat-fixed-20261020T063202Z, repeat-fixed-20261020T091155Z

Complete paired replicates in manifest: 90

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 60 | 59/60 (98.3%, 91.1–99.7%) | 20.69 ± 3.40 | 4.02 ± 0.06 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 60 | 59/60 (98.3%, 91.1–99.7%) | 22.68 ± 2.70 | 4.48 ± 0.13 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 60/60 |
| persistent | after_restart_reuse | A | 60 | 58/60 (96.7%, 88.6–99.1%) | 23.72 ± 7.05 | 4.67 ± 0.58 | 14.38 ± 6.16 | 0.05 ± 0.22 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 60 | 60/60 (100.0%, 94.0–100.0%) | 22.55 ± 0.52 | 4.58 ± 0.09 | 13.15 ± 10.90 | 0.00 ± 0.00 | 0.00 ± 0.00 | 60/60 |
| persistent | mission | A | 60 | 59/60 (98.3%, 91.1–99.7%) | 22.85 ± 3.11 | 4.56 ± 0.09 | 15.13 ± 7.35 | 0.12 ± 0.45 | 0.00 ± 0.00 | — |
| persistent | mission | B | 60 | 60/60 (100.0%, 94.0–100.0%) | 22.44 ± 0.44 | 4.55 ± 0.08 | 15.25 ± 7.81 | 0.10 ± 0.30 | 0.00 ± 0.00 | — |
| transient | mission | A | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.31 ± 0.48 | 4.54 ± 0.08 | 0.33 ± 0.48 | 0.13 ± 0.35 | 0.00 ± 0.00 | — |
| transient | mission | B | 30 | 30/30 (100.0%, 88.6–100.0%) | 22.44 ± 0.30 | 4.57 ± 0.06 | 0.10 ± 0.31 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 60 | -1.23 [-4.57, 2.25] | 0.033 [0.000, 0.083] | extend affected cells to 60 |
| transient | mission | 30 | -0.23 [-0.43, -0.03] | 0.000 [0.000, 0.000] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 420. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
