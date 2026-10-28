#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""opus 方差带预筛器 v1(2026-10-28 · 出题选题第一筛)

用途: 对候选题快测 opus 落点,判该题是否满足质检方案条件③(opus 全过轮∈[1,3]),
     避免对注定过简/过难的题盲目投入五模型满窗判分(每题20调用)。
判定:
  N/N 全过   → 过简风险(条件③✗) → SKIP
  0/N 全过   → 过难风险(条件③✗) → SKIP
  混合        → ✅方差带命中 → 投入满窗判分(补2轮确认)

用法:
  python3 opus_prescreen.py <item_dir> [--runs 2] [--model opus5.5]
前置:
  item_dir 为完整判分形态(含 environment/workspace/repo + tests + solution)
  compass ops/ali30q/tools 路径下有 v5 判分 venv 与 model_solve
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

HOME = Path.home()
V5 = HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense"
JUDGE_PY = V5 / ".venv-judge/bin/python"
UT_RUNNER = V5 / "tools/ut_runner.py"
SOLVE = V5 / "tools/model_solve.py"


def restore_ws(item: Path, backup: Path):
    ws = item / "environment/workspace/repo"
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(backup, ws)


def read_verdict(item: Path, run_n: int):
    f = item / "_s5" / f"opus5.5_run{run_n}_result.json"
    if not f.exists():
        return {"run": run_n, "all_pass": None, "score": None, "note": "result未落盘"}
    d = json.load(open(f))
    uv = d.get("ut_vector", {})
    full = all(v == 1 for v in uv.values()) if uv else None
    return {"run": run_n, "all_pass": full, "score": d.get("score"),
            "applied": d.get("applied_files"), "error": (d.get("error") or "")[:60]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("item", type=Path)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--model", default="opus5.5")
    a = ap.parse_args()
    item = a.item.resolve()
    ws = item / "environment/workspace/repo"
    if not ws.exists():
        print(f"✗ workspace 不存在: {ws}")
        return 1
    # 快照坑版(每轮前还原,防 patch 残留)
    backup = item / "_prescreen_ws_backup"
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(ws, backup)
    runs = []
    try:
        for n in range(a.runs):
            restore_ws(item, backup)
            r = subprocess.run([str(JUDGE_PY), str(SOLVE), item.name,
                                "--model", a.model, "--run", str(n)],
                               capture_output=True, text=True, timeout=1800,
                               env={**__import__("os").environ, "CS_PATH": str(V5)})
            v = read_verdict(item, n)
            runs.append(v)
            print(f"  run{n}: 全对={v['all_pass']} score={v['score']} applied={v['applied']} {v.get('note','')}")
    finally:
        restore_ws(item, backup)
        shutil.rmtree(backup, ignore_errors=True)
    full = sum(1 for x in runs if x.get("all_pass"))
    if full == a.runs:
        verdict = "过简风险(条件③✗) → SKIP"
    elif full == 0:
        verdict = "过难风险(条件③✗) → SKIP"
    else:
        verdict = "✅方差带命中 → 投入满窗判分(补2轮确认)"
    print(f"\n结论: opus 全过轮 {full}/{a.runs} → {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
