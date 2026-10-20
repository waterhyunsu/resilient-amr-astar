# Controlled Gazebo arena

This arena isolates planner and persistent-memory behavior from the static cylinders in the stock TurtleBot3 world. The four perimeter walls are present in both Gazebo and `arena.pgm`; the interior is open. All conditions use this same world, map, Waffle model, Nav2 parameters, and start/goal unless a high-variance block explicitly jitters the test geometry.

Default fixed trial: spawn at `(-2, -0.5)`, goal `(2, -0.5)`, and place the 0.45 m test obstacle at `(0, -0.5)`. The square obstacle is on the direct path, while the arena provides room to route around it. This horizontal route replaces the diagonal pilot route, which produced inconsistent goal-approach results in the baseline condition.

`arena.launch.py` is passed as the `world_launch` argument to the project `sim.launch.py`; `arena.yaml` is passed as `map:=...`. It starts gzserver without gzclient/RViz for repeatable headless trials.
