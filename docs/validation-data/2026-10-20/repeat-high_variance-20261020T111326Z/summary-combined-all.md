# Repeated experiment summary: repeat-fixed-20261020T063202Z, repeat-fixed-20261020T091155Z, repeat-high_variance-20261020T111326Z

Complete paired replicates in manifest: 150

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 90 | 89/90 (98.9%, 94.0–99.8%) | 20.56 ± 2.86 | 4.03 ± 0.15 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 90 | 89/90 (98.9%, 94.0–99.8%) | 22.46 ± 2.31 | 4.47 ± 0.17 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 90/90 |
| persistent | after_restart_reuse | A | 90 | 88/90 (97.8%, 92.3–99.4%) | 23.22 ± 5.85 | 4.61 ± 0.51 | 13.52 ± 6.59 | 0.03 ± 0.18 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 90 | 89/90 (98.9%, 94.0–99.8%) | 22.66 ± 2.66 | 4.55 ± 0.19 | 12.58 ± 10.09 | 0.01 ± 0.11 | 0.00 ± 0.00 | 90/90 |
| persistent | mission | A | 90 | 89/90 (98.9%, 94.0–99.8%) | 22.59 ± 2.65 | 4.53 ± 0.17 | 13.80 ± 7.73 | 0.09 ± 0.39 | 0.00 ± 0.00 | — |
| persistent | mission | B | 90 | 90/90 (100.0%, 95.9–100.0%) | 22.32 ± 0.79 | 4.53 ± 0.16 | 13.70 ± 7.99 | 0.09 ± 0.32 | 0.00 ± 0.00 | — |
| transient | mission | A | 60 | 59/60 (98.3%, 91.1–99.7%) | 22.53 ± 2.04 | 4.49 ± 0.40 | 0.22 ± 0.42 | 0.07 ± 0.25 | 0.00 ± 0.00 | — |
| transient | mission | B | 60 | 60/60 (100.0%, 94.0–100.0%) | 22.32 ± 0.84 | 4.54 ± 0.18 | 0.10 ± 0.30 | 0.02 ± 0.13 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 90 | -0.94 [-3.54, 1.74] | 0.011 [-0.022, 0.056] | extend affected cells to 60 |
| transient | mission | 60 | -0.12 [-0.23, 0.00] | 0.017 [0.000, 0.050] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 660. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
