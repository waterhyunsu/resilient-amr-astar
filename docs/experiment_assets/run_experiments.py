"""Cold-start, paired A/B Gazebo experiment runner for the documented arena."""

import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "experiment_assets"
RUN_TRIAL = ASSETS / "run_trial.py"
LAUNCH = "resilient_amr_bringup sim.launch.py"
WORLD_LAUNCH = ASSETS / "arena.launch.py"
MAP = ASSETS / "arena.yaml"


def run_stage(*, run_dir, trial_id, phase, scenario, arm, seed, geom, stage,
              memory_file, progress_radius, yaw_tolerance, preserve_memory=False,
              obstacle_present=True):
    out_file = run_dir / f"{trial_id}-{stage}.jsonl"
    logger_file = run_dir / f"{trial_id}-{stage}-ros.jsonl"
    launch_file = run_dir / f"{trial_id}-{stage}-launch.log"
    mem_enabled = arm == "B"
    env = os.environ.copy()
    env["TURTLEBOT3_MODEL"] = "waffle"
    env["RESILIENT_AMR_START_X"] = str(geom["start_x"])
    env["RESILIENT_AMR_START_Y"] = str(geom["start_y"])
    prefix = subprocess.check_output(["ros2", "pkg", "prefix", "turtlebot3_navigation2"],
                                     env=env, text=True).strip()
    stock_params = Path(prefix) / "share" / "turtlebot3_navigation2" / "param" / "humble" / "waffle.yaml"
    params_file = run_dir / "nav2_waffle_experiment.yaml"
    stock_text = stock_params.read_text(encoding="utf-8")
    old_line = "required_movement_radius: 0.5"
    new_line = f"required_movement_radius: {progress_radius:g}"
    yaw_line = "yaw_goal_tolerance: 0.25"
    new_yaw_line = f"yaw_goal_tolerance: {yaw_tolerance:g}"
    if stock_text.count(old_line) != 1 or stock_text.count(yaw_line) != 1:
        raise RuntimeError(f"Expected stock progress and yaw checker values in {stock_params}")
    custom_text = stock_text.replace(old_line, new_line).replace(yaw_line, new_yaw_line)
    if params_file.exists() and params_file.read_text(encoding="utf-8") != custom_text:
        raise FileExistsError(f"Refusing to overwrite changed Nav2 parameters: {params_file}")
    if not params_file.exists():
        params_file.write_text(custom_text, encoding="utf-8")
    launch_cmd = ["ros2", "launch", *LAUNCH.split(),
                  f"world_launch:={WORLD_LAUNCH}", f"map:={MAP}", "use_rviz:=false",
                  f"memory_enabled:={'true' if mem_enabled else 'false'}",
                  f"params_file:={params_file}",
                  f"experiment_condition:={arm}-{scenario}-{phase}-stage{stage}",
                  f"memory_path:={memory_file}", f"experiment_log_path:={logger_file}"]
    with launch_file.open("w", encoding="utf-8") as launch_stream:
        launch_proc = subprocess.Popen(launch_cmd, cwd=ROOT, env=env, stdout=launch_stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        trial_cmd = [sys.executable, str(RUN_TRIAL), "--trial-id", trial_id,
                     "--phase", phase, "--condition", f"{arm}-{scenario}",
                     "--seed", str(seed), "--output", str(out_file),
                     "--start-x", str(geom["start_x"]), "--start-y", str(geom["start_y"]),
                     "--goal-x", str(geom["goal_x"]), "--goal-y", str(geom["goal_y"]),
                     "--obstacle-x", str(geom["obstacle_x"]), "--obstacle-y", str(geom["obstacle_y"]),
                     "--progress-radius", str(progress_radius), "--timeout", "150",
                     "--yaw-tolerance", str(yaw_tolerance),
                     "--appearance-delay", str(geom["appearance_delay_sec"] if obstacle_present else 0)]
        if obstacle_present:
            trial_cmd.append("--obstacle")
        if scenario == "transient" and obstacle_present:
            trial_cmd.extend(["--transient-seconds", str(geom["transient_seconds"])])
        if mem_enabled:
            trial_cmd.append("--memory-enabled")
        if preserve_memory:
            trial_cmd.append("--preserve-memory")
        result = None
        try:
            result = subprocess.run(trial_cmd, cwd=ROOT, env=env, text=True,
                                    capture_output=True, timeout=210)
        except subprocess.TimeoutExpired as exc:
            result = subprocess.CompletedProcess(trial_cmd, 124, exc.stdout or "", exc.stderr or "")
        finally:
            try:
                os.killpg(launch_proc.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
            try:
                launch_proc.wait(timeout=25)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(launch_proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                launch_proc.wait(timeout=5)
        if result.stdout:
            print(result.stdout.rstrip(), flush=True)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr, flush=True)
        record = None
        if out_file.exists():
            rows = [json.loads(x) for x in out_file.read_text(encoding="utf-8").splitlines() if x]
            if rows:
                record = rows[-1]
        if record is None:
            record = {"trial_id": trial_id, "phase": phase, "scenario": scenario,
                      "condition": arm, "seed": seed, "status": "SETUP_ERROR",
                      "exit_code": result.returncode,
                      "stderr_tail": result.stderr[-1200:] if result.stderr else ""}
            with (run_dir / "setup_errors.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        return record, str(out_file), str(logger_file), str(launch_file)


def geometry(phase, seed):
    if phase == "fixed":
        return {"start_x": -2.0, "start_y": -0.5, "goal_x": 2.0, "goal_y": -0.5,
                "obstacle_x": 0.0, "obstacle_y": -0.5,
                "appearance_delay_sec": 0.0, "transient_seconds": 1.0}
    rng = random.Random(seed)
    return {"start_x": round(-2.0 + rng.uniform(-0.30, 0.30), 3),
            "start_y": round(-0.5 + rng.uniform(-0.25, 0.25), 3),
            "goal_x": round(2.0 + rng.uniform(-0.30, 0.30), 3),
            "goal_y": round(-0.5 + rng.uniform(-0.25, 0.25), 3),
            "obstacle_x": round(rng.uniform(-0.35, 0.35), 3),
            "obstacle_y": round(-0.5 + rng.uniform(-0.25, 0.25), 3),
            "appearance_delay_sec": round(rng.uniform(0.5, 2.0), 2),
            "transient_seconds": round(rng.uniform(0.5, 1.5), 2)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["fixed", "high_variance"], required=True)
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--scenarios", nargs="+", choices=["transient", "persistent"],
                   default=["transient", "persistent"])
    p.add_argument("--arms", nargs="+", choices=["A", "B"], default=["A", "B"])
    p.add_argument("--seed-offset", type=int, default=1)
    p.add_argument("--progress-radius", type=float, default=0.1,
                   help="shared Nav2 progress threshold, justified for short final A* segments")
    p.add_argument("--yaw-tolerance", type=float, default=3.14159,
                   help="shared terminal yaw tolerance; experiments score arrival at a 2D point")
    p.add_argument("--output-dir", type=Path)
    args = p.parse_args()
    if args.count < 1:
        p.error("--count must be positive")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_dir or (ROOT / "docs" / "validation-data" / "2026-10-20" /
                                  f"repeat-{args.phase}-{stamp}")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = run_dir / "manifest.jsonl"
    order_rng = random.Random(61724 + args.seed_offset)
    count_done = 0
    for replicate in range(args.seed_offset, args.seed_offset + args.count):
        seed = replicate
        geom = geometry(args.phase, seed if args.phase == "high_variance" else 0)
        for scenario in args.scenarios:
            arm_order = args.arms[:]
            order_rng.shuffle(arm_order)
            pair = {"phase": args.phase, "scenario": scenario, "replicate": replicate,
                    "seed": seed, "arm_order": arm_order, "geometry": geom, "results": {}}
            for arm in arm_order:
                trial_id = f"{args.phase}-{scenario}-r{replicate:03d}-{arm}"
                memory_file = run_dir / f"{trial_id}-memory.json"
                # Persistent memory is created by the observation leg and reused only
                # by its cold-start restart leg. Transient and baseline legs start clean.
                if memory_file.exists():
                    raise FileExistsError(f"Refusing to overwrite memory artifact: {memory_file}")
                first, out1, ros1, launch1 = run_stage(
                    run_dir=run_dir, trial_id=trial_id, phase=args.phase, scenario=scenario,
                    arm=arm, seed=seed, geom=geom, stage=1, memory_file=memory_file,
                    progress_radius=args.progress_radius, yaw_tolerance=args.yaw_tolerance)
                stages = [{"stage": "mission", "record": first, "output": out1,
                           "ros_log": ros1, "launch_log": launch1}]
                if scenario == "persistent":
                    second, out2, ros2, launch2 = run_stage(
                        run_dir=run_dir, trial_id=trial_id, phase=args.phase, scenario=scenario,
                        arm=arm, seed=seed, geom=geom, stage=2, memory_file=memory_file,
                        progress_radius=args.progress_radius,
                        yaw_tolerance=args.yaw_tolerance,
                        preserve_memory=(arm == "B"))
                    stages.append({"stage": "after_restart_reuse", "record": second,
                                   "output": out2, "ros_log": ros2, "launch_log": launch2})
                    third, out3, ros3, launch3 = run_stage(
                        run_dir=run_dir, trial_id=trial_id, phase=args.phase, scenario=scenario,
                        arm=arm, seed=seed, geom=geom, stage=3, memory_file=memory_file,
                        progress_radius=args.progress_radius,
                        yaw_tolerance=args.yaw_tolerance,
                        preserve_memory=(arm == "B"), obstacle_present=False)
                    stages.append({"stage": "after_obstacle_removal", "record": third,
                                   "output": out3, "ros_log": ros3, "launch_log": launch3})
                pair["results"][arm] = stages
                count_done += 1
                print(f"Progress {count_done}/{args.count * len(args.scenarios) * len(args.arms)} "
                      f"{args.phase} {scenario} replicate={replicate} arm={arm}", flush=True)
            with manifest.open("a", encoding="utf-8") as f:
                f.write(json.dumps(pair) + "\n")
    print(f"Completed data directory: {run_dir}", flush=True)


if __name__ == "__main__":
    main()
