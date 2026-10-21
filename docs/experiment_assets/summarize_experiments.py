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
    lines = [f"# 반복 실험 요약: {run_names}", "",
             f"manifest의 완료된 A/B 쌍: {len(pairs)}", "",
             "성공률 신뢰구간은 Wilson 방식의 95% 구간입니다. 쌍별 평균 차이의 신뢰구간은 부트스트랩 10,000회 재표집으로 계산했습니다.",
             "재계획은 최초 경로 이후 새 경로를 발행한 횟수입니다. 경로 방향 전환은 로봇 이동에 따른 정상적인 경로 단축은 제외하고 장애물 주변에서 우회 방향이 바뀐 경우를 셉니다. 차이는 B−A이며 실패 실행도 모든 분모에 포함했습니다.", ""]
    lines += ["| 조건 | 단계 | 방식 | 표본수 | 성공 | 임무 시간(s) 평균 ± 표준편차 | 이동 거리(m) 평균 ± 표준편차 | 재계획 횟수 평균 ± 표준편차 | 경로 전환 횟수 평균 ± 표준편차 | FollowPath 취소 평균 ± 표준편차 | 기억 복원 |",
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
        scenario_ko = {"persistent": "지속 장애물", "transient": "일시 장애물"}.get(scenario, scenario)
        stage_ko = {"mission": "초기 임무", "after_restart_reuse": "재시작 후 기억 재사용", "after_obstacle_removal": "장애물 제거 후"}.get(stage, stage)
        arm_ko = {"A": "기준 A", "B": "제안 B"}.get(arm, arm)
        lines.append(f"| {scenario_ko} | {stage_ko} | {arm_ko} | {s['n']} | {s['successes']}/{s['n']} ({100*s['success_rate']:.1f}%, {100*lo:.1f}–{100*hi:.1f}%) | {d[0]:.2f} ± {d[1]:.2f} | {dist[0]:.2f} ± {dist[1]:.2f} | {repl[0]:.2f} ± {repl[1]:.2f} | {switches[0]:.2f} ± {switches[1]:.2f} | {cancels[0]:.2f} ± {cancels[1]:.2f} | {restored} |")
    lines += ["", "## 쌍별 주요 비교", "",
              "| 조건 | 단계 | A/B 쌍 수 | 재계획 차이 B−A, 평균 [95% 신뢰구간] | 성공률 차이 B−A [95% 부트스트랩 신뢰구간] | 정밀도 기준 |",
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
            extend = "최소 30쌍에 미달"
        elif half_r > 0.5 or half_s > 0.10:
            extend = "extend affected cells to 60"
        else:
            extend = "정밀도 기준 충족"
        scenario_ko = {"persistent": "지속 장애물", "transient": "일시 장애물"}.get(scenario, scenario)
        stage_ko = {"mission": "초기 임무", "after_restart_reuse": "재시작 후 기억 재사용", "after_obstacle_removal": "장애물 제거 후"}.get(stage, stage)
        lines.append(f"| {scenario_ko} | {stage_ko} | {len(rows)} | {mean_r:.2f} [{rlo:.2f}, {rhi:.2f}] | {mean_s:.3f} [{slo:.3f}, {shi:.3f}] | {extend} |")
    setup_errors = sum(1 for pair in pairs for stages in pair.get("results", {}).values()
                       for stage in stages if stage.get("record", {}).get("status") == "SETUP_ERROR")
    incomplete = sum(len(list(run_dir.glob("*-1.jsonl"))) + len(list(run_dir.glob("*-2.jsonl"))) + len(list(run_dir.glob("*-3.jsonl"))) for run_dir in args.run_dir)
    lines += ["", f"설정 오류 단계 중 임무 성공률 분모에서 제외된 수: {setup_errors}.",
              f"이 폴더에 저장된 단계별 원자료 수: {incomplete}. A/B 쌍 완료 여부와 설정 실패는 `manifest.jsonl`, `setup_errors.jsonl`에서 확인하세요.",
              "", "이 요약은 통계적 유의성을 확정하지 않습니다. 쌍별 추정값은 명시된 정밀도 기준과 시나리오의 한계를 고려해 해석해야 합니다.", ""]
    output = args.output or (args.run_dir[0] / "summary.md")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite summary: {output}")
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
