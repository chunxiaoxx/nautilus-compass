# -*- coding: utf-8 -*-
"""86 题正解一致性自检(抽样版)。

双门(对每题,git worktree 隔离):
  门1 starter 必败:worktree@buggy_commit + 测试@fix_commit → pytest 必须 FAIL
  门2 正解必过:再把 starter_path 换成 @reference_fix_commit 版 → pytest 必须 PASS
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPOS = {
    "nautilus-v5": r"C:\Users\chunx\nautilus-v5",
    "nautilus-core": r"C:\Users\chunx\Projects\nautilus-core",
    "nautilus-compass": r"C:\Users\chunx\Projects\nautilus-compass",
    "nautilus-fde-phase3": r"C:\Users\chunx\Projects\nautilus-fde-phase3",
}
SRC = (r"C:\Users\chunx\Projects\nautilus-core\phase3\backend\docs"
       r"\evidence\g2b1_fuel_nautilus-v5.jsonl")


def sh(cwd, *args, timeout=300):
    r = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def check(item, tmp):
    repo = item["provenance"]["repo"]
    repo_dir = REPOS[repo]
    buggy = item["provenance"]["buggy_commit"]
    fix = item["provenance"]["reference_fix_commit"]
    sp = item["provenance"]["starter_path"]
    vp = item["provenance"]["verifier_path"]
    uid = item["task_uid"]
    wt = str(Path(tmp) / "wt")
    rc, _, err = sh(repo_dir, "git", "worktree", "add", "--detach", wt, buggy)
    if rc != 0:
        return uid, "WORKTREE_FAIL", err[-150:]
    try:
        # 测试文件取 fix 版(考卷=新测试)
        rc, out, err = sh(repo_dir, "git", "show", f"{fix}:{vp}")
        if rc != 0:
            return uid, "NO_TEST_AT_FIX", err[-120:]
        (Path(wt) / vp).write_text(out, encoding="utf-8")
        env_py = {**__import__("os").environ, "PYTHONUTF8": "1", "PYTHONPATH": wt}
        def run_pytest():
            return subprocess.run(
                [sys.executable, "-m", "pytest", vp, "-x", "-q", "--no-header",
                 "-p", "no:cacheprovider"],
                cwd=wt, capture_output=True, timeout=240, text=True,
                encoding="utf-8", errors="replace", env=env_py)
        # 门1:starter 状态必败
        try:
            g1 = run_pytest()
        except subprocess.TimeoutExpired:
            return uid, "TIMEOUT_G1", "pytest 240s 超时(starter)"
        gate1_fail = g1.returncode != 0
        # 门2:应用正解(fix 完整 diff,排除任意层级 tests;多文件 fix 单替换会假阴性)
        rc, patch, err = sh(repo_dir, "git", "diff", buggy, fix, "--",
                            ":(exclude)tests", ":(exclude)**/tests",
                            ":(exclude)**/tests/**")
        if rc != 0 or not patch.strip():
            return uid, "NO_DIFF", (err or "empty")[-120:]
        pf = Path(wt) / "_fix.patch"
        pf.write_text(patch, encoding="utf-8", newline="\n")
        rc2, _, err2 = sh(wt, "git", "apply", "_fix.patch")
        if rc2 != 0:
            return uid, "APPLY_FAIL", err2[-150:]
        try:
            g2 = run_pytest()
        except subprocess.TimeoutExpired:
            return uid, "TIMEOUT_G2", "pytest 240s 超时(正解)"
        gate2_pass = g2.returncode == 0
        verdict = "OK" if (gate1_fail and gate2_pass) else (
            "GATE1_FAIL_MISSING(starter 也过=题太易)" if not gate1_fail else
            "GATE2_PASS_MISSING(正解也不过=verifier坏)")
        tail = (g2.stdout or g2.stderr or "").strip().splitlines()[-1:] or [""]
        return uid, verdict, f"g1rc={g1.returncode} g2rc={g2.returncode} | {tail[0][:80]}"
    finally:
        sh(repo_dir, "git", "worktree", "remove", "--force", wt)


def main():
    src = sys.argv[2] if len(sys.argv) > 2 else SRC
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    off = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    items = [json.loads(l) for l in open(src, encoding="utf-8")][off:off + n]
    stats = {}
    with tempfile.TemporaryDirectory() as tmp:
        for it in items:
            try:
                uid, verdict, detail = check(it, tmp)
            except Exception as e:
                uid, verdict, detail = it["task_uid"], "CRASH", repr(e)[:150]
            stats[verdict] = stats.get(verdict, 0) + 1
            print(f"[{verdict}] {uid[:50]} | {detail}", flush=True)
    print("SUMMARY:", stats)


if __name__ == "__main__":
    main()
