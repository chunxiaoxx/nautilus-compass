# -*- coding: utf-8 -*-
"""Assay 首考判分 · 门2/门3(对被测方 produced unified diff)。

门3:diff 不得触碰 verifier/test 文件(路径判定);
门2:worktree@buggy + verifier 取 fix 版 + 应用被测 diff → run_cmd 必须通过。
用法: python scripts/assay_gate23.py <repo> <pack_single.json>
pack 单条:{task_uid,repo,buggy_commit,fix_reference_commit,verifier_path,run_cmd,produced_output{code,text}}
输出: 门23[uid] g3=CLEAN|TOUCHED g2=PASS|FAIL rc=<n> | 尾行
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def _diff_paths(diff_text: str) -> list[str]:
    return re.findall(r"^diff --git a/(.+?) b/", diff_text, re.M)


def run(repo: str, item: dict) -> None:
    uid = item["task_uid"].split(":")[-1]
    buggy = item["buggy_commit"]
    fix = item["fix_reference_commit"]
    vp = item["verifier_path"]
    run_cmd = item["run_cmd"]
    po = item["produced_output"]
    if isinstance(po, str):  # dict 的字符串形式(json 或 python repr)——双兼容
        import ast
        try:
            po = json.loads(po)
        except json.JSONDecodeError:
            po = ast.literal_eval(po)
    diff_text = po["text"]
    paths = _diff_paths(diff_text)
    g3 = "TOUCHED" if any(("test" in p or p.startswith("tests")) for p in paths) else "CLEAN"
    with tempfile.TemporaryDirectory() as tmp:
        wt = str(Path(tmp) / "wt")
        subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, buggy],
                       capture_output=True)
        try:
            out = subprocess.run(["git", "-C", repo, "show", f"{fix}:{vp}"],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                print(f"门23[{uid}] NO_TEST_AT_FIX")
                return
            (Path(wt) / vp).write_text(out.stdout, encoding="utf-8")
            pf = Path(wt) / "_produced.diff"
            pf.write_text(diff_text, encoding="utf-8", newline="\n")
            ap = subprocess.run(["git", "-C", wt, "apply", "_produced.diff"],
                                capture_output=True, text=True)
            if ap.returncode != 0:
                print(f"门23[{uid}] g3={g3} g2=APPLY_FAIL | {ap.stderr[-100:]}")
                return
            env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": wt}
            parts = run_cmd.split()
            if parts[0] == "pytest":
                cmd = [os.environ.get("ASSAY_PY", sys.executable), "-m"] + parts
            else:
                cmd = [os.environ.get("ASSAY_PY", sys.executable)] + parts
            g = subprocess.run(cmd,
                               cwd=wt, capture_output=True, text=True, env=env, timeout=540)
            tail = (g.stdout or g.stderr).strip().splitlines()[-1:]
            g2 = "PASS" if g.returncode == 0 else "FAIL"
            print(f"门23[{uid}] g3={g3} g2={g2} rc={g.returncode} | {tail[0][:70] if tail else ''}")
        finally:
            subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt],
                           capture_output=True)


if __name__ == "__main__":
    item = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    run(sys.argv[1], item)
