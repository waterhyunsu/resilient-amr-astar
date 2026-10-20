# A/B Simulation Experiment Protocol

## Purpose

Compare baseline A (A* with transient LiDAR obstacle handling) against proposal B (the same A* planner and safety behavior plus repeated-observation persistence, map updates, and mission-to-mission reuse). Keep the world, robot, navigation parameters, and controller identical except for the obstacle-information policy.

## Conditions and trial counts

There are four cells: A-transient, B-transient, A-persistent, and B-persistent. Run each cell in two phases:

1. **Fixed initial comparison:** start `(-2.0, -0.5)`, goal `(2.0, -0.5)`, obstacle `(0.0, -0.5)`, same event timing; 30 trials per cell (120 total).
2. **Higher-variation comparison:** vary start x/y by ±0.30/±0.25 m, goal x/y by ±0.30/±0.25 m, obstacle x/y by ±0.35/±0.25 m around the fixed line, obstacle spawn-to-goal delay from 0.5–2.0 s, and transient-obstacle lifetime from 0.5–1.5 s; 30 trials per cell (120 more; 240 planned total).

Use paired trials: for each replicate number and phase, A and B receive the same seed and environmental conditions. Randomize whether A or B runs first within each pair. Cold-start Gazebo and ROS/Nav2 for every mission. Do not use `/reset_world` to recycle trials: the pilot exposed stale local-costmap bounds after resets. All experimental runs share Nav2 `required_movement_radius=0.1 m`; the stock `0.5 m` threshold exceeded the final four-cell A* segment and produced observed `Failed to make progress` aborts at the goal approach. These experiments evaluate reaching a 2D position, not final heading, so both arms also share `yaw_goal_tolerance=pi`. Both overrides are applied equally to A/B, with the generated full Nav2 parameter file retained per run. Persistent trials include observing and saving the obstacle, restarting the full stack, checking restored memory and path use, then running with the obstacle absent to measure verified memory release near the former obstacle location. Transient trials include an obstacle that disappears before persistence confirmation.

The A* dynamic-obstacle inflation is 11 cells (0.55 m) to match the Nav2 global-costmap inflation radius. Earlier diagnostic runs used 5 cells while the controller costmaps used 0.55 m global/1.0 m local inflation; one A run aborted for lack of progress beside the obstacle. The aligned value is applied identically to A/B before the new inferential block.

## Predefined extension rule

Review precision after each phase has 30 complete paired replicates in every cell. Extend the affected phase/cells to 60 paired replicates (up to 480 runs overall) if either:

- the 95% confidence interval for the paired A-minus-B difference in replans per mission has a half-width greater than 0.5 replans; or
- the 95% confidence interval for the paired difference in mission success rate has a half-width greater than 10 percentage points.

Do not extend merely because a p-value is above a threshold. If precision remains inadequate at 60, report the interval and limitation instead of implying a reliable conclusion. Never stop early because a result appears favorable.

## Measures and reporting

Primary comparison: replans per mission and mission success rate. Also report exact path-signature changes (as a diagnostic only), route-side switches near the obstacle, mission duration, odometry distance, obstacle-state classification (confusion counts, precision/recall), and time to map/memory update and release. Report each cell's denominator, failures, aborted runs, missing telemetry, mean and standard deviation for continuous/count measures, and 95% confidence intervals. Retain every raw run, including failures; state any exclusions and their reasons. Analyze paired differences by replicate/seed. Record each cold-start session and stage; persistent lifecycle stages within a replicate are linked, and the paired A/B replicate is the independent comparison unit.

## Current status

The final fixed and higher-variation blocks are complete. Each transient condition has 30 paired replicates; each persistent condition was extended from 30 to 60 because the predefined precision rule was not met at 30. Persistent extensions used unique seeds 31–60. The total valid dataset is 180 paired A/B replicates (840 cold-start stage runs). The fixed persistent and higher-variation persistent primary replan confidence intervals still exceed the 0.5-replan half-width target at 60, so the authorized extension cap has been reached and those effects remain inconclusive. Do not extend these blocks or claim the persistent-condition hypothesis was established from these data.

Combined persistent summaries and raw run records are retained under `docs/validation-data/2026-10-20/`; see `VALIDATION_REPORT_2026-10-20.md` for the interval estimates, stage success counts, failures, and reproduction commands. Two interrupted higher-variation extension attempts are preserved for audit but excluded from inference because one reused seeds and the other inherited a leftover Gazebo process. The completed clean persistent extension is `repeat-high_variance-persistent-20261020T140500Z`.

The earlier pilot and pre-fix batches are also diagnostic-only and excluded from inference. Event-log review led to separating A* replan publications from route-side switches and updating the follower to compare refreshed paths against the remaining active path before replacing a FollowPath goal. These changes and the final trial configuration are documented in the report and retained with the experiment assets. All valid run failures remain in the denominators and raw data.

