"""Summarize paired JSONL manifests with bootstrap and Wilson intervals."""

import argparse
import json
import math
import random
import statistics
from pathlib import Path


def percentile(values, q):
    values = sorted(values)
    if not values:
        return float("nan")
    x = (len(values) - 1) * q
    lo, hi = math.floor(x), math.ceil(x)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (x - lo)


def wilson(successes, n, z=1.959963984540054):
    if not n:
        return float("nan"), float("nan")
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap_mean_ci(values, seed=20261020, rounds=10000):
    if not values:
        return (float("nan"), float("nan"))
    if len(values) == 1:
        return (values[0], values[0])
    rng = random.Random(seed)
    means = [statistics.mean(rng.choices(values, k=len(values))) for _ in range(rounds)]
    return percentile(means, 0.025), percentile(means, 0.975)


def load_pairs(run_dir):
    manifest = run_dir / "manifest.jsonl"
    pairs = []
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                pairs.append(json.loads(line))
    return pairs


def record_at(pair, arm, stage):
    for value in pair.get("results", {}).get(arm, []):
        if value.get("stage") == stage:
            return value.get("record")
    return None


def summarize_group(rows):
    statuses = [r.get("status") for r in rows]
    n = len(rows)
    successes = sum(s == "SUCCEEDED" for s in statuses)
    lo, hi = wilson(successes, n)
    metrics = {}
    for key in ("duration_sec", "odom_distance_m", "replans_after_initial_path", "path_changes", "route_switches", "canceled_followpath_count", "memory_cells_near_obstacle_at_start",
                "memory_cells_near_obstacle_at_end"):
        xs = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        metrics[key] = (statistics.mean(xs), statistics.stdev(xs) if len(xs) > 1 else 0.0) if xs else (float("nan"), float("nan"))
    restored = [r.get("memory_restored") for r in rows if r.get("memory_restored") is not None]
    return {"n": n, "successes": successes, "success_rate": successes / n if n else float("nan"),
            "success_ci": (lo, hi), "metrics": metrics,
            "memory_restored_n": sum(bool(x) for x in restored), "memory_restored_den": len(restored)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path, nargs="+")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    pairs = []
    for run_dir in args.run_dir:
        for pair in load_pairs(run_dir):
            pair.setdefault("source_run", run_dir.name)
            pairs.append(pair)
    grouped = {}
    paired = {}
    for pair in pairs:
        scenario = pair["scenario"]
        for arm in ("A", "B"):
            for stage in ("mission", "after_restart_reuse", "after_obstacle_removal"):
                rec = record_at(pair, arm, stage)
                if rec is not None and rec.get("status") in ("SUCCEEDED", "FAILED"):
                    grouped.setdefault((scenario, stage, arm), []).append(rec)
        primary_stage = "mission" if scenario == "transient" else "after_restart_reuse"
        a, b = record_at(pair, "A", primary_stage), record_at(pair, "B", primary_stage)
        if (a is not None and b is not None
                and a.get("status") in ("SUCCEEDED", "FAILED")
                and b.get("status") in ("SUCCEEDED", "FAILED")):
            paired.setdefault((scenario, primary_stage), []).append((pair["replicate"], a, b))

    run_names = ", ".join(run_dir.name for run_dir in args.run_dir)
    lines = [f"# Repeated experiment summary: {run_names}", "",
             f"Complete paired replicates in manifest: {len(pairs)}", "",
             "Success intervals use Wilson 95% CIs. Paired mean-difference intervals use 10,000 bootstrap resamples.",
             "Replans are path publications after the initial plan; route switches compare the detour side near the obstacle, ignoring normal path shortening as the robot advances. Differences are B minus A. Failed runs remain in all denominators.", ""]
    lines += ["| Scenario | Stage | Arm | n | Success | Duration s mean ± SD | Distance m mean ± SD | Replans mean ± SD | Route switches mean ± SD | FollowPath cancels mean ± SD | Memory restored |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key in sorted(grouped):
        scenario, stage, arm = key
        s = summarize_group(grouped[key])
        d = s["metrics"]["duration_sec"]
        dist = s["metrics"]["odom_distance_m"]
        repl = s["metrics"]["replans_after_initial_path"]
        switches = s["metrics"]["route_switches"]
        cancels = s["metrics"]["canceled_followpath_count"]
        restored = f"{s['memory_restored_n']}/{s['memory_restored_den']}" if s["memory_restored_den"] else "—"
        lo, hi = s["success_ci"]
        lines.append(f"| {scenario} | {stage} | {arm} | {s['n']} | {s['successes']}/{s['n']} ({100*s['success_rate']:.1f}%, {100*lo:.1f}–{100*hi:.1f}%) | {d[0]:.2f} ± {d[1]:.2f} | {dist[0]:.2f} ± {dist[1]:.2f} | {repl[0]:.2f} ± {repl[1]:.2f} | {switches[0]:.2f} ± {switches[1]:.2f} | {cancels[0]:.2f} ± {cancels[1]:.2f} | {restored} |")
    lines += ["", "## Paired primary comparisons", "",
              "| Scenario | Stage | n pairs | Replan difference B−A, mean [95% CI] | Success difference B−A [95% bootstrap CI] | Precision rule |",
              "|---|---|---:|---:|---:|---|"]
    for (scenario, stage), rows in sorted(paired.items()):
        replan_diffs = [b.get("replans_after_initial_path", max(0, b["path_messages"] - 1)) - a.get("replans_after_initial_path", max(0, a["path_messages"] - 1)) for _, a, b in rows]
        success_diffs = [int(b["status"] == "SUCCEEDED") - int(a["status"] == "SUCCEEDED") for _, a, b in rows]
        seed = sum(ord(c) for c in scenario + stage) + 20261020
        rlo, rhi = bootstrap_mean_ci(replan_diffs, seed)
        slo, shi = bootstrap_mean_ci(success_diffs, seed + 1)
        mean_r = statistics.mean(replan_diffs)
        half_r = max(mean_r - rlo, rhi - mean_r)
        mean_s = statistics.mean(success_diffs)
        half_s = max(mean_s - slo, shi - mean_s)
        if len(rows) < 30:
            extend = "minimum 30 paired replicates not reached"
        elif half_r > 0.5 or half_s > 0.10:
            extend = "extend affected cells to 60"
        else:
            extend = "precision threshold met"
        lines.append(f"| {scenario} | {stage} | {len(rows)} | {mean_r:.2f} [{rlo:.2f}, {rhi:.2f}] | {mean_s:.3f} [{slo:.3f}, {shi:.3f}] | {extend} |")
    setup_errors = sum(1 for pair in pairs for stages in pair.get("results", {}).values()
                       for stage in stages if stage.get("record", {}).get("status") == "SETUP_ERROR")
    incomplete = sum(len(list(run_dir.glob("*-1.jsonl"))) + len(list(run_dir.glob("*-2.jsonl"))) + len(list(run_dir.glob("*-3.jsonl"))) for run_dir in args.run_dir)
    lines += ["", f"Setup-error stages excluded from mission denominators: {setup_errors}.",
              f"Raw stage records present in this directory: {incomplete}. Consult `manifest.jsonl` and `setup_errors.jsonl` for paired completion and setup failures.",
              "", "This summary does not certify statistical significance. Interpret paired estimates with the stated precision rule and scenario limitations.", ""]
    output = args.output or (args.run_dir[0] / "summary.md")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite summary: {output}")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
