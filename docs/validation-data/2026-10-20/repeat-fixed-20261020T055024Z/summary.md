# Repeated experiment summary: repeat-fixed-20261020T055024Z

Complete paired replicates in manifest: 2

Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.
Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.

| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | Memory restored |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| persistent | after_obstacle_removal | A | 1 | 1/1 (100.0%, 20.7–100.0%) | 20.12 ± 0.00 | 4.03 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_obstacle_removal | B | 1 | 1/1 (100.0%, 20.7–100.0%) | 21.23 ± 0.00 | 4.33 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 1/1 |
| persistent | after_restart_reuse | A | 1 | 1/1 (100.0%, 20.7–100.0%) | 21.77 ± 0.00 | 4.49 ± 0.00 | 14.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | after_restart_reuse | B | 1 | 1/1 (100.0%, 20.7–100.0%) | 22.58 ± 0.00 | 4.59 ± 0.00 | 15.00 ± 0.00 | 0.00 ± 0.00 | 1/1 |
| persistent | mission | A | 1 | 1/1 (100.0%, 20.7–100.0%) | 24.34 ± 0.00 | 4.74 ± 0.00 | 36.00 ± 0.00 | 0.00 ± 0.00 | — |
| persistent | mission | B | 1 | 1/1 (100.0%, 20.7–100.0%) | 23.70 ± 0.00 | 4.65 ± 0.00 | 29.00 ± 0.00 | 0.00 ± 0.00 | — |
| transient | mission | A | 1 | 1/1 (100.0%, 20.7–100.0%) | 23.33 ± 0.00 | 4.74 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |
| transient | mission | B | 1 | 1/1 (100.0%, 20.7–100.0%) | 23.23 ± 0.00 | 4.71 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | — |

## Paired primary comparisons

| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |
|---|---|---:|---:|---:|---|
| persistent | after_restart_reuse | 1 | 1.00 [1.00, 1.00] | 0.000 [0.000, 0.000] | precision threshold met |
| transient | mission | 1 | 0.00 [0.00, 0.00] | 0.000 [0.000, 0.000] | precision threshold met |

Setup-error stages excluded from mission denominators: 0.
Raw stage records present in this directory: 8. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.

This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.
