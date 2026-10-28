#!/usr/bin/env python3
"""Path B effect 层 — apply patch + 跑 pytest(2026-06-18·节点4 第二砖）。

纯核在 services.swe_verify（解析/reward/记忆）·本模块是 effect:把候选 patch 应用到 repo
副本、跑指定测试、回 pytest stdout 喂 swe_verify。在 repo 副本上做(不污染 base·SWE-bench
要复用 base instance）。apply 失败 → 回可解析的失败串(swe_reward→None·诚实不混入梯度）。

2-turn 闭环(fresh session 接 producer）:
  produce patch → run_candidate → parse_pytest_summary → swe_reward(=通过数)
  → 抽 build_swe_memory(失败测试+报错) → produce turn-2 → ... → rsi_improved(t1,t2 通过数)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile


def apply_patch(repo_dir: str, patch_text: str) -> tuple[bool, str]:
    """git apply 候选 patch 到 repo_dir。回 (ok, stderr)。"""
    pf = os.path.join(repo_dir, "_cand.patch")
    with open(pf, "w", encoding="utf-8", newline="\n") as f:
        f.write(patch_text)
    try:
        r = subprocess.run(
            ["git", "-C", repo_dir, "apply", "--whitespace=nowarn", "_cand.patch"],
            capture_output=True, text=True, timeout=60)
        return r.returncode == 0, r.stderr
    finally:
        try:
            os.unlink(pf)
        except OSError:
            pass


def run_pytest(repo_dir, test_target, timeout: int = 300,
               python_exe: str | None = None, env_extra: dict | None = None) -> str:
    """在 repo_dir 跑 pytest test_target → stdout+stderr 合并(喂解析器）。

    python_exe:跑 pytest 的解释器(默认本进程·真 SWE instance 传隔离 venv 的 python）。
    env_extra:并入子进程环境(纯 Python repo 隔离靠 PYTHONPATH=副本路径·让 import 命中打
    patch 的副本而非 venv 里 egg-link 的原 repo）。
    """
    py = python_exe or sys.executable
    env = None
    if env_extra:
        env = dict(os.environ)
        env.update({k: str(v) for k, v in env_extra.items()})
    targets = [test_target] if isinstance(test_target, str) else list(test_target)
    r = subprocess.run(
        [py, "-m", "pytest", *targets, "-q", "--no-header",
         "-p", "no:cacheprovider", "-o", "addopts="],
        cwd=repo_dir, capture_output=True, text=True, timeout=timeout, env=env)
    return (r.stdout or "") + "\n" + (r.stderr or "")


def run_candidate(repo_dir: str, patch_text: str, test_target: str,
                  timeout: int = 300, python_exe: str | None = None,
                  env_extra: dict | None = None) -> str:
    """候选完整 effect:copy base → apply patch → run pytest → 回 pytest 输出。

    在副本上做(base 不污染·可复用）。apply 失败 → 回 "patch_apply_failed: ..."
    （swe_verify.parse 该串 parsed=False → swe_reward=None·诚实计错不混梯度）。
    python_exe/env_extra 透传给 run_pytest(真 SWE instance 隔离·见其 docstring）。
    🔴 env_extra 含 PYTHONPATH 时自动把副本路径 dst 前置(否则副本 patch 不生效）。
    """
    work = tempfile.mkdtemp(prefix="swe_cand_")
    dst = os.path.join(work, "repo")
    try:
        shutil.copytree(repo_dir, dst, symlinks=True)
        ok, err = apply_patch(dst, patch_text)
        if not ok:
            return "patch_apply_failed: %s" % (err.strip()[:300] or "git apply rc!=0")
        eff_env = dict(env_extra) if env_extra else None
        if eff_env and "PYTHONPATH" in eff_env:
            # 副本路径前置:import 命中打 patch 的副本(纯 Python repo 隔离关键）
            prev = eff_env["PYTHONPATH"]
            eff_env["PYTHONPATH"] = dst + (os.pathsep + prev if prev else "")
        try:
            return run_pytest(dst, test_target, timeout=timeout,
                              python_exe=python_exe, env_extra=eff_env)
        except subprocess.TimeoutExpired:
            return "pytest_timeout after %ds" % timeout
    finally:
        shutil.rmtree(work, ignore_errors=True)
