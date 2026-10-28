"""_distill_runtime SWE 分支单测(2026-06-26·同质料 held-out eval 使能)。

torch/docker 是 GPU effect(lazy import)·此处只测可本地化的:diff 提取 + score_solution
按 kind 分派 + SWE 走 subprocess docker(mock subprocess.run)。generate_solution/load_models
的真推理在 GPU 侧·不在此测。
"""
from __future__ import annotations

import os
import sys
import types

import pytest

# scripts/ 无 __init__.py(namespace 包·本地可能被别处 scripts 遮蔽)→ 直接加 path 导入。
# 生产路径 `from scripts._distill_runtime`(distill_eval·cwd=scripts)在 GPU 盒已跑过 LOO 证可用。
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _distill_runtime as rt   # noqa: E402
from _distill_runtime import _extract_diff, score_solution   # noqa: E402
from services.distill_fuel import instruction_for, INSTRUCTION_SWE   # noqa: E402


# ── diff 提取(模型输出可能 fence 包裹或裸吐) ──────────────────────────────

def test_extract_diff_from_fence():
    text = "Here is the fix:\n```diff\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n```\ndone"
    d = _extract_diff(text)
    assert d.startswith("--- a/x.py")
    assert "```" not in d


def test_extract_diff_raw_no_fence():
    text = "Reasoning...\ndiff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b"
    d = _extract_diff(text)
    assert d.startswith("diff --git a/x.py")


def test_extract_diff_dashdash_marker():
    text = "blah\n--- a/foo.py\n+++ b/foo.py\n@@ x @@"
    assert _extract_diff(text).startswith("--- a/foo.py")


# ── score_solution 按 kind 分派(SWE → docker subprocess) ─────────────────

def test_score_solution_swe_resolved(monkeypatch):
    calls = {}

    def fake_run(cmd, capture_output, text, timeout):
        calls["cmd"] = cmd
        return types.SimpleNamespace(stdout="RESOLVED=True\n", stderr="", returncode=0)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    task = {"task_id": "django__django-13220", "kind": "swe"}
    score = score_solution(task, "```diff\n--- a\n+++ b\n@@\n```")
    assert score == 1.0
    assert calls["cmd"][0] == rt.SWE_VENV   # 走 swe-rsi venv subprocess


def test_score_solution_swe_unresolved(monkeypatch):
    monkeypatch.setattr(rt.subprocess, "run",
                        lambda *a, **k: types.SimpleNamespace(stdout="RESOLVED=False\n", stderr="", returncode=0))
    task = {"task_id": "x", "kind": "swe"}
    assert score_solution(task, "--- a\n+++ b") == 0.0


def test_score_solution_swe_empty_diff_zero(monkeypatch):
    # 空 diff(模型没产 patch)→ 不调 docker·直接 0
    called = {"n": 0}
    monkeypatch.setattr(rt.subprocess, "run",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1) or
                        types.SimpleNamespace(stdout="", stderr="", returncode=0))
    assert score_solution({"task_id": "x", "kind": "swe"}, "no diff here") == 0.0
    assert called["n"] == 0


def test_score_solution_swe_subprocess_fail_conservative_zero(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("docker down")
    monkeypatch.setattr(rt.subprocess, "run", boom)
    assert score_solution({"task_id": "x", "kind": "swe"}, "--- a\n+++ b\n@@") == 0.0


def test_score_solution_ale_uses_ale_path(monkeypatch):
    # kind!=swe → 不走 SWE 分支(ALE mock 分)
    monkeypatch.setenv("ALE_MOCK_SCORE", "1")
    score = score_solution({"task_id": "ahc001", "kind": "ale"}, "```python\nprint(1)\n```")
    assert score > 0   # ALE mock 合成分


def test_swe_instruction_mentions_diff():
    assert "diff" in instruction_for("swe").lower()
    assert instruction_for("swe") == INSTRUCTION_SWE
