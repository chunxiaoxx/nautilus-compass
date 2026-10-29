#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CS-GS-005 判分入口(缺口档排期第 2 项,移植 CS-GS-001 双模式): 逐 UT 矩阵输出。

沙盒内(harbor): python score.py → /logs/verifier/reward.txt(全过=1)
                + /logs/artifacts/ut_matrix.json(逐UT通过矩阵, 供区分度三指标)
本地审查:      python score.py --local --tests <tests目录> --repo <repo目录>
                [--out ut_matrix.json] → stdout JSON

本题契约差异(对 GS-001): 题侧 UT 按 <包根>/workspace/repo 相对回退定位 repo
(单一候选,无 environment 中间层),故 staging 布局 = 容器同构
(staging/tests + staging/workspace/repo,与 selfcheck R202 双向实跑同构),
使副本被测,否则永远打回原包坑版(金标自检假阳性的根因)。
判分语义: 全过=1 否则=0(需求 line 612),逐 UT 矩阵落 JSON。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TASK_ID = "CS-GS-005"


def run_pytest(tests_dir: Path, repo: Path, python: str) -> dict:
    """跑全部判分 UT, 解析 -v 输出为逐 UT 矩阵。"""
    import shutil as _sh
    import tempfile as _tf
    pytest_dir = tests_dir
    staging = None
    if not str(tests_dir).startswith("/tests"):
        staging = Path(_tf.mkdtemp(prefix="score_staging_"))
        _sh.copytree(tests_dir, staging / "tests",
                     ignore=_sh.ignore_patterns("__pycache__", "*.pyc", "calibration"))
        _sh.copytree(repo, staging / "workspace" / "repo",
                     ignore=_sh.ignore_patterns("__pycache__", "*.pyc", ".git"))
        pytest_dir = staging / "tests"
    try:
        cmd = [python, "-m", "pytest", str(pytest_dir), "-v", "--tb=no",
               "--rootdir", str(pytest_dir), "-p", "no:cacheprovider", "--no-header"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    finally:
        if staging:
            _sh.rmtree(staging, ignore_errors=True)
    out = r.stdout + r.stderr
    per_ut = {}
    for m in re.finditer(r"::([\w]+) (PASSED|FAILED|ERROR|SKIPPED|XFAIL)", out):
        per_ut[m.group(1)] = {"PASSED": 1, "FAILED": 0, "ERROR": 0,
                              "SKIPPED": 0, "XFAIL": 1}[m.group(2)]
    failed = sorted(k for k, v in per_ut.items() if v == 0)
    passed = sum(1 for v in per_ut.values() if v == 1)
    return {
        "passed": passed, "total": len(per_ut),
        "passrate": round(passed / len(per_ut), 4) if per_ut else 0.0,
        "all_pass": bool(per_ut) and not failed,
        "failed_ut": failed,
        "signature": failed,              # 失败签名(区分度三指标的UT粒度数据)
        "per_ut": per_ut,
        "pytest_returncode": r.returncode,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--tests", help="tests 目录(含 test_*.py)")
    ap.add_argument("--repo", help="workspace/repo 目录")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--out", default="", help="矩阵JSON落盘路径(沙盒=/logs/artifacts/ut_matrix.json)")
    a = ap.parse_args()
    if a.local:
        tests_dir, repo = Path(a.tests), Path(a.repo)
    else:
        tests_dir = Path("/tests")
        repo = next((p for p in [Path("/workspace/repo"), Path("/workspace"),
                                 Path("/testbed"), Path("/app")] if p.exists()), Path.cwd())
    result = run_pytest(tests_dir, repo, a.python)
    result["task"] = TASK_ID
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    if a.local:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        # harbor 沙盒: reward 语义与 test.sh 一致(全过=1)
        logs = Path("/logs/verifier")
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "reward.txt").write_text("1" if result["all_pass"] else "0")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
