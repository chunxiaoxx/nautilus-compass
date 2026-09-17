# -*- coding: utf-8 -*-
"""Assay 首考判分 · 门1 starter 必败(官方双门语义,承 v5 f1cb5ea 工具)。

门1 = worktree@buggy_commit + verifier 取 fix 版覆盖 → pytest 必须 FAIL。
用法: python scripts/assay_gate1.py <repo> <fix_uid> <buggy_commit> <verifier_path>
输出: 门1[uid] rc=<n> FAIL_AS_EXPECTED | PASS(题太易/门1破) | 错误码
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(repo: str, uid: str, buggy: str, verifier: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        wt = str(Path(tmp) / "wt")
        r = subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, buggy],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"门1[{uid}] WORKTREE_FAIL {r.stderr[-120:]}")
            return 2
        try:
            out = subprocess.run(["git", "-C", repo, "show", f"{uid}:{verifier}"],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                print(f"门1[{uid}] NO_TEST_AT_FIX {out.stderr[-100:]}")
                return 2
            (Path(wt) / verifier).write_text(out.stdout, encoding="utf-8")
            env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": wt}
            g = subprocess.run([os.environ.get("ASSAY_PY", sys.executable), "-m", "pytest",
                                verifier, "-x", "-q", "--no-header"],
                               cwd=wt, capture_output=True, text=True, env=env, timeout=540)
            tail = (g.stdout or g.stderr).strip().splitlines()[-1:]
            verdict = "FAIL_AS_EXPECTED" if g.returncode != 0 else "PASS_BUGGY_PASSES"
            print(f"门1[{uid}] rc={g.returncode} {verdict} | {tail[0][:80] if tail else ''}")
            return 0 if g.returncode != 0 else 1
        finally:
            subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt],
                           capture_output=True)


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
