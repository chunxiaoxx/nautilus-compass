# -*- coding: utf-8 -*-
"""pytest_harness_adapter · repo pytest 燃料 → 自包含三件套(2026-08-25 交付平台)。

承诺自 640421f(燃料对接裁定):V5 全链(forge 双门/a_class_filter/distill)消费
自包含 verifier_inline:argv[1]=候选代码文件 → stdout 输出 {"passed": bool,...} JSON。

适配方式:verifier_inline 单文件自含判定逻辑(worktree@buggy + fix 版测试 + 覆盖
candidate + pytest node 级运行),repo 由环境变量 G2B1_REPO_DIR 提供(缺省用生成时
内嵌的本地路径;换机器时指向任一 clone 即可,commit 已内嵌,与工作区状态无关)。

用法:
  # 单题适配(自测双门:starter 必败 + 内嵌正解必过)
  python pytest_harness_adapter.py --item <jsonl> --repo <repo_dir> [--uid g2b1:xxxx]
  # 批量转 distill 三件套 jsonl
  python pytest_harness_adapter.py --batch <fuel.jsonl> --repos repo1=dir1,repo2=dir2 \
      --out vtf/_g2b1_distill_triples.jsonl
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VERIFIER_TMPL = '''#!/usr/bin/env python3
"""自包含 verifier(由 pytest_harness_adapter 生成)· repo pytest 题适配。
用法: python this_verifier.py <candidate_code_file>
stdout: {{"passed": bool, "reason": str, "n_pass": int, "n_total": int}}
依赖: G2B1_REPO_DIR 指向题目源 repo 的任一 git clone(默认生成机内嵌路径)。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = os.environ.get("G2B1_REPO_DIR", r"{repo_dir}")
BUGGY = "{buggy}"
FIX = "{fix}"
STARTER_PATH = {starter_path!r}
TEST_PATH = {test_path!r}
NODE_ID = {node_id!r}  # 空 = 整个测试文件


def sh(cwd, *args, timeout=300):
    return subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout,
                          text=True, encoding="utf-8", errors="replace")


def main():
    cand = Path(sys.argv[1]).read_text(encoding="utf-8")
    if not REPO or not Path(REPO).exists():
        print(json.dumps({{"passed": False, "reason": "repo missing",
                          "n_pass": 0, "n_total": 1}}))
        return
    with tempfile.TemporaryDirectory() as tmp:
        wt = str(Path(tmp) / "wt")
        r = sh(REPO, "git", "worktree", "add", "--detach", wt, BUGGY)
        if r.returncode != 0:
            print(json.dumps({{"passed": False, "reason": "worktree fail",
                              "n_pass": 0, "n_total": 1}}))
            return
        try:
            # fix 版测试(考卷=新测试)
            t = sh(REPO, "git", "show", f"{{FIX}}:{{TEST_PATH}}")
            if t.returncode != 0:
                print(json.dumps({{"passed": False, "reason": "no test at fix",
                                  "n_pass": 0, "n_total": 1}}))
                return
            tp = Path(wt) / TEST_PATH
            tp.parent.mkdir(parents=True, exist_ok=True)
            tp.write_text(t.stdout, encoding="utf-8")
            # 候选代码落到 starter 位置
            sp = Path(wt) / STARTER_PATH
            sp.parent.mkdir(parents=True, exist_ok=True)
            sp.write_text(cand, encoding="utf-8")
            target = NODE_ID if NODE_ID else TEST_PATH
            env = {{**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": wt,
                   "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}}
            g = subprocess.run(
                [sys.executable, "-m", "pytest", target, "-x", "-q",
                 "--no-header", "-p", "no:cacheprovider"],
                cwd=wt, capture_output=True, timeout=240, text=True,
                encoding="utf-8", errors="replace", env=env)
            passed = g.returncode == 0
            tail = (g.stdout or g.stderr or "").strip().splitlines()
            print(json.dumps({{"passed": passed,
                              "reason": "pass" if passed else (tail[-1] if tail else "fail")[:120],
                              "n_pass": 1 if passed else 0, "n_total": 1}}))
        finally:
            sh(REPO, "git", "worktree", "remove", "--force", wt)


main()
'''


def git_show(repo_dir, ref, path):
    r = subprocess.run(["git", "-C", repo_dir, "show", f"{ref}:{path}"],
                       capture_output=True, timeout=60, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git show {ref}:{path} 失败: {r.stderr[-120:]}")
    return r.stdout


def make_triple(item, repo_dir):
    """产 distill 三件套:prompt / starter_inline / verifier_inline。"""
    p = item["provenance"]
    starter = git_show(repo_dir, p["buggy_commit"], p["starter_path"])
    fix_tests = git_show(repo_dir, p["reference_fix_commit"], p["verifier_path"])
    # node id:平台导出暂无该字段;空 = 整文件(与自检工具同粒度)
    verifier = VERIFIER_TMPL.format(
        repo_dir=repo_dir, buggy=p["buggy_commit"], fix=p["reference_fix_commit"],
        starter_path=p["starter_path"], test_path=p["verifier_path"], node_id="")
    return {
        "uid": item["task_uid"],
        "prompt": (item.get("summary", "").strip() +
                   "\n\n任务:修复 starter 使仓库测试(已就位)全部通过。"
                   "只输出修复后的完整文件(单个 ```python 代码块)。"),
        "starter_inline": starter,
        "verifier_inline": verifier,
        "_fix_tests_for_selftest": fix_tests,
    }


def selftest(triple, repo_dir):
    """双门自测:starter 必败 + 正解(buggy→fix diff 应用后的 starter 文件)必过。"""
    p_verifier = triple["verifier_inline"]
    with tempfile.TemporaryDirectory() as d:
        vp = Path(d) / "v.py"
        vp.write_text(p_verifier, encoding="utf-8")
        sp = Path(d) / "starter.py"
        sp.write_text(triple["starter_inline"], encoding="utf-8")
        env = {**__import__("os").environ, "G2B1_REPO_DIR": repo_dir,
               "PYTHONUTF8": "1"}
        r1 = subprocess.run([sys.executable, str(vp), str(sp)],
                            capture_output=True, timeout=400, text=True,
                            encoding="utf-8", errors="replace", env=env)
        v1 = json.loads(r1.stdout or "{}")
        if v1.get("passed"):
            return "GATE1_FAIL(starter 也过)"
        return None


def gate2_with_reference(item, repo_dir, triple):
    """门2:worktree@buggy + fix 测试 + fix 版 starter 文件 → verifier 必过。"""
    p = item["provenance"]
    fixed_starter = git_show(repo_dir, p["reference_fix_commit"], p["starter_path"])
    with tempfile.TemporaryDirectory() as d:
        vp = Path(d) / "v.py"
        vp.write_text(triple["verifier_inline"], encoding="utf-8")
        fp = Path(d) / "ref.py"
        fp.write_text(fixed_starter, encoding="utf-8")
        env = {**__import__("os").environ, "G2B1_REPO_DIR": repo_dir,
               "PYTHONUTF8": "1"}
        r = subprocess.run([sys.executable, str(vp), str(fp)],
                           capture_output=True, timeout=400, text=True,
                           encoding="utf-8", errors="replace", env=env)
        v = json.loads(r.stdout or "{}")
        return v.get("passed"), v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", help="单条 fuel jsonl 文件")
    ap.add_argument("--uid", default=None, help="只适配该 task_uid")
    ap.add_argument("--repo", help="单题模式 repo 路径")
    ap.add_argument("--batch", help="批量 fuel jsonl")
    ap.add_argument("--repos", help="repo=dir 映射,逗号分隔")
    ap.add_argument("--out", default="vtf/_g2b1_distill_triples.jsonl")
    a = ap.parse_args()

    if a.item:
        items = [json.loads(l) for l in open(a.item, encoding="utf-8")]
        if a.uid:
            items = [it for it in items if it["task_uid"] == a.uid]
        it = items[0]
        repo = a.repo
        triple = make_triple(it, repo)
        g1 = selftest(triple, repo)
        g2p, g2v = gate2_with_reference(it, repo, triple)
        print(f"门1(starter 必败): {'OK' if g1 is None else g1}")
        print(f"门2(正解必过): {'OK' if g2p else json.dumps(g2v)[:200]}")
        Path(a.out).parent.mkdir(exist_ok=True)
        with open(a.out, "a", encoding="utf-8") as f:
            t = dict(triple)
            t.pop("_fix_tests_for_selftest")
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"三件套已追加 {a.out}: {triple['uid']}")
    elif a.batch:
        repos = dict(kv.split("=") for kv in a.repos.split(","))
        out = Path(a.out)
        out.parent.mkdir(exist_ok=True)
        n_ok = n_bad = 0
        with open(out, "w", encoding="utf-8") as f:
            for line in open(a.batch, encoding="utf-8"):
                it = json.loads(line)
                repo = repos[it["provenance"]["repo"]]
                try:
                    triple = make_triple(it, repo)
                except Exception as e:
                    print(f"[ADAPT_FAIL] {it['task_uid']} {str(e)[:100]}", flush=True)
                    n_bad += 1
                    continue
                t = dict(triple)
                t.pop("_fix_tests_for_selftest")
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
                n_ok += 1
        print(f"batch done: {n_ok} adapted, {n_bad} fail -> {out}")


if __name__ == "__main__":
    main()
