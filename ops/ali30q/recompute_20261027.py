#!/usr/bin/env python3
"""三道落带题独立复算执行器(2026-10-27)——判据见 RECOMPUTE_PREREGISTER_20261027.md
只信判据与自测;全部在 /tmp 隔离副本上跑,不触 v5 工作区。"""
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

SCRATCH = Path("/tmp/cs_recompute_20261027/codesense")
JUDGE_PY = SCRATCH / ".venv-judge/bin/python"
UT_RUNNER = SCRATCH / "tools/ut_runner.py"
ITEMS = ["CS-507", "CS-511", "CS-513"]
report = {}


def run_ut(item: Path, runs: int = 3) -> dict:
    r = subprocess.run([str(JUDGE_PY), str(UT_RUNNER), str(item), "--runs", str(runs),
                        "--python", str(JUDGE_PY)],
                       capture_output=True, text=True, timeout=1800)
    out = item / "_judge" / "ut_results.json"
    if not out.exists():
        return {"error": r.stdout[-400:] + r.stderr[-400:]}
    return json.load(open(out))


def swap_solution(item: Path) -> list:
    """gold_check 同款: solution 文件按相对路径换入 workspace;直路不存在按 basename 定位(记录映射规则)。"""
    ws = item / "environment/workspace/repo"
    swapped, rule = [], "relpath"
    for f in sorted((item / "solution").rglob("*.py")):
        rel = f.relative_to(item / "solution")
        dst = ws / rel
        if not dst.exists():
            rule = "basename"
            hits = list(ws.rglob(rel.name))
            if len(hits) != 1:
                return swapped + [f"!! {rel}: 直路与basename定位均不唯一({len(hits)})"]
            dst = hits[0]
        shutil.copy2(f, dst)
        swapped.append(str(dst.relative_to(ws)))
    return swapped


def check_r1_r4_r5(item: Path) -> dict:
    d = {}
    d["pytest_ini"] = (item / "pytest.ini").exists()
    d["leak_scan"] = (item / "LEAK_SCAN_PASS").exists()
    try:
        idx = tomllib.load(open(item / "task.toml", "rb"))["metadata"]["ut_index"]
        gating = [e["ut_name"] for e in idx if e.get("gating")]
    except Exception as e:
        gating = []
        d["task_toml"] = f"解析失败: {e}"
    d["gating_declared"] = gating
    tests_src = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                          for p in (item / "tests").glob("*.py"))
    d["gating_missing_in_tests"] = [g for g in gating if g not in tests_src]
    return d


def check_r6(item: Path) -> list:
    rows = []
    for f in sorted((item / "_s5").glob("qwen*result*.json")):
        try:
            s = json.load(open(f)).get("score")
        except Exception:
            s = "PARSE-FAIL"
        rows.append((f.name, s, 1 if s == 1.0 else 0))
    return rows


for name in ITEMS:
    item = SCRATCH / "items" / name
    rep = {"R1R4R5": check_r1_r4_r5(item)}
    # 坑版态(R2)
    rep["R2_bugstate"] = run_ut(item)
    # 金标态(R3):先备工作区,换入 solution,跑完还原
    ws = item / "environment/workspace/repo"
    bak = item / "environment/workspace/_ws_bak"
    shutil.copytree(ws, bak)
    rep["swapped"] = swap_solution(item)
    rep["R3_goldstate"] = run_ut(item)
    shutil.rmtree(ws)
    shutil.copytree(bak, ws)
    shutil.rmtree(bak)
    rep["R6_qwen_raw"] = check_r6(item)
    report[name] = rep
    print(f"== {name} ==", flush=True)
    print(json.dumps(rep, ensure_ascii=False, indent=1, default=str)[:3000], flush=True)

json.dump(report, open("/tmp/cs_recompute_20261027/recompute_raw.json", "w"),
          ensure_ascii=False, indent=1, default=str)
print("\nraw → /tmp/cs_recompute_20261027/recompute_raw.json")
