#!/usr/bin/env python3
"""Path B(节点4)— 准备一道 SWE-bench-lite instance 的本地隔离环境(2026-06-19）。

路 A(自给·不依赖 compass resolve env）:纯 Python repo(sympy 等）→ venv 只装依赖·
把打 candidate patch 的副本放 PYTHONPATH 首位 → import 命中副本。本脚本只做"准备 base":
  clone repo → checkout base_commit → apply test_patch(加测试定义·非解法）
  → 拷工作树(去 .git）→ git init+commit(小副本·apply_patch 用）
  → venv + pip install -e clone(拉依赖·import 仍走 PYTHONPATH 副本）
emit JSON {instance_id, repo, version, base_dir, venv_python, test_target(node ids）}。

candidate 解法 patch 由 swe_runner.run_candidate(base_dir, patch, test_target,
python_exe=venv_python, env_extra={"PYTHONPATH":""}）跑。base_dir 不污染·可复用多轮。

用法:python -m scripts.swe_prep_instance sympy__sympy-24102 [--gold]
  --gold:用数据集 gold patch 自检(base→F2P fail·gold→F2P pass）= 验证器+环境健全门。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "swe_bench")
# 🔴 老 SWE 题(requests 2.x / sympy 1.1-1.5）依赖 stdlib cgi —— Py3.13 已移除·Py3.12 还在。
# venv 默认用 3.12 让老题可装(新题 1.7+/1.12 在 3.13 也 OK·3.12 同样能装）。
PYTHON_FOR_VENV = os.environ.get("SWE_VENV_PYTHON",
                                 r"C:\Users\chunx\AppData\Local\Programs\Python\Python312\python.exe")
if not os.path.exists(PYTHON_FOR_VENV):
    PYTHON_FOR_VENV = sys.executable
REPO_URL = {
    "sympy/sympy": "https://github.com/sympy/sympy.git",
    "psf/requests": "https://github.com/psf/requests.git",
    "pallets/flask": "https://github.com/pallets/flask.git",
    "pytest-dev/pytest": "https://github.com/pytest-dev/pytest.git",
    "pylint-dev/pylint": "https://github.com/pylint-dev/pylint.git",
}


def _rmtree_robust(path):
    """Windows: .git pack/object 常只读 → rmtree 默认失败。onexc chmod 重试。"""
    import stat
    if not os.path.exists(path):
        return

    def _onerr(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass
    try:
        shutil.rmtree(path, onexc=_onerr)  # py3.12+
    except TypeError:
        shutil.rmtree(path, onerror=lambda f, p, e: _onerr(f, p, e))


def _run(cmd, cwd=None, timeout=600, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError("cmd failed: %s\n%s\n%s" % (cmd, r.stdout[-2000:], r.stderr[-2000:]))
    return r


def _load_instance(instance_id):
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    for r in ds:
        if r["instance_id"] == instance_id:
            return r
    raise SystemExit("instance not found: %s" % instance_id)


def _slug(repo):
    return repo.replace("/", "__")


def _ensure_clone(repo):
    url = REPO_URL.get(repo)
    if not url:
        raise SystemExit("no clone url for repo %s" % repo)
    d = os.path.join(CACHE, "clones", _slug(repo))
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        print("[prep] cloning %s (one-time, full history)..." % repo, file=sys.stderr)
        _run(["git", "clone", url, d], timeout=1800)
    return d


def _is_test_file(p):
    low = p.lower()
    base = low.rsplit("/", 1)[-1]
    return "/tests/" in low or "/test/" in low or base.startswith("test_") or base.endswith("_test.py")


def _test_files_from_patch(test_patch):
    """只取真正的测试文件(排除 test_patch 顺带改的非测试 helper·如 quality_unicode.py）。"""
    files = []
    for m in re.finditer(r"^\+\+\+ b/(\S+)", test_patch, re.MULTILINE):
        if _is_test_file(m.group(1)):
            files.append(m.group(1))
    return files


def _node_ids(f2p, test_files):
    """F2P 名 → pytest node id。已含 :: 或 / 则原样;否则拼到唯一测试文件。"""
    ids = []
    for name in f2p:
        if "::" in name or "/" in name:
            ids.append(name)
        elif len(test_files) == 1:
            ids.append("%s::%s" % (test_files[0], name))
        else:
            # 多测试文件 + 裸名:退回按 -k 不可靠 → 用全部文件 + 该名作 node 尝试逐个
            ids.append(name)  # 由调用方决定;lite 易题通常单文件
    return ids


def _venv_python(venv_dir):
    p = os.path.join(venv_dir, "Scripts", "python.exe")  # Windows
    return p if os.path.exists(p) else os.path.join(venv_dir, "bin", "python")


def _ensure_venv(repo, version, clone_dir):
    venv_dir = os.path.join(CACHE, "venvs", "%s__%s" % (_slug(repo), version))
    py = _venv_python(venv_dir)
    marker = os.path.join(venv_dir, ".deps_ok")
    if os.path.exists(marker):
        return py
    print("[prep] creating venv + installing deps (one-time per repo+version)...", file=sys.stderr)
    if not os.path.isdir(venv_dir):
        _run([PYTHON_FOR_VENV, "-m", "venv", venv_dir])
    py = _venv_python(venv_dir)
    _run([py, "-m", "pip", "install", "-q", "-U", "pip", "setuptools", "wheel"], timeout=600)
    _run([py, "-m", "pip", "install", "-q", "pytest"], timeout=600)
    # editable install 拉 repo 自身依赖(import 仍走 PYTHONPATH 副本·此处只为 deps）
    _run([py, "-m", "pip", "install", "-q", "-e", clone_dir], timeout=1800)
    open(marker, "w").write("ok")
    return py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("--gold", action="store_true", help="用 gold patch 自检验证器+环境")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    inst = _load_instance(args.instance_id)
    repo, version = inst["repo"], inst.get("version", "na")
    base_commit, test_patch = inst["base_commit"], inst["test_patch"]
    f2p = json.loads(inst["FAIL_TO_PASS"]) if isinstance(inst["FAIL_TO_PASS"], str) else inst["FAIL_TO_PASS"]

    clone = _ensure_clone(repo)
    _run(["git", "-C", clone, "checkout", "-f", base_commit], timeout=300)
    _run(["git", "-C", clone, "clean", "-fdx", "-q"], timeout=300, check=False)
    # apply test_patch(加测试定义）
    tp = os.path.join(clone, "_test.patch")
    open(tp, "w", encoding="utf-8", newline="\n").write(test_patch)
    _run(["git", "-C", clone, "apply", "--whitespace=nowarn", "_test.patch"], timeout=120)
    os.unlink(tp)

    # 拷工作树(去 .git）→ instance base → 小 fresh git
    base_dir = os.path.join(CACHE, "instances", args.instance_id)
    _rmtree_robust(base_dir)  # Windows .git 只读对象 → ignore_errors 会留残骸
    shutil.copytree(clone, base_dir, ignore=shutil.ignore_patterns(".git"))
    _run(["git", "-C", base_dir, "init", "-q"])
    _run(["git", "-C", base_dir, "config", "user.email", "t@t"])
    _run(["git", "-C", base_dir, "config", "user.name", "t"])
    _run(["git", "-C", base_dir, "add", "-A"])
    _run(["git", "-C", base_dir, "commit", "-qm", "base+test_patch"], timeout=300)

    test_files = _test_files_from_patch(test_patch)
    node_ids = _node_ids(f2p, test_files)
    venv_py = _ensure_venv(repo, version, clone)

    result = {
        "instance_id": args.instance_id, "repo": repo, "version": version,
        "base_dir": base_dir, "venv_python": venv_py,
        "test_files": test_files, "test_target": node_ids,
        "f2p_count": len(f2p), "n_f2p": len(f2p),
    }

    if args.gold:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from services.swe_runner import run_candidate, run_pytest
        from services.swe_verify import parse_pytest_summary
        env = {"PYTHONPATH": ""}
        # base(无解法 patch）→ F2P 应 fail
        base_out = run_pytest(base_dir, node_ids, python_exe=venv_py,
                              env_extra={"PYTHONPATH": base_dir})
        base_s = parse_pytest_summary(base_out)
        gold_out = run_candidate(base_dir, inst["patch"], node_ids,
                                 python_exe=venv_py, env_extra=env)
        gold_s = parse_pytest_summary(gold_out)
        result["selfcheck"] = {
            "base": base_s, "gold": gold_s,
            "verifier_sound": bool(base_s["parsed"] and gold_s["parsed"]
                                   and gold_s["passed"] > base_s["passed"]
                                   and gold_s["passed"] == len(f2p)),
            "base_tail": base_out[-800:], "gold_tail": gold_out[-800:],
        }

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(out)
    print(out)


if __name__ == "__main__":
    main()
