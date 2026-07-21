#!/usr/bin/env python3
"""Contract tests for benchmark profile entrypoints.

These tests keep the Windows and Linux wrappers aligned with the paired
raw-vs-guarded recall gate.
"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_windows_bench_profile_runs_guarded_recall_and_policy_gate():
    text = (ROOT / "tests" / "bench_profile.ps1").read_text(encoding="utf-8")
    assert "eval_recall_guarded.json" in text
    assert "--signal-policy" in text
    assert "guarded" in text
    assert "ops/recall_policy_gate.py" in text
    assert "recall_policy_gate.json" in text
    assert "ops/recall_policy_preflight.py" in text
    assert "recall_policy_preflight.json" in text
    assert "policy_gate" in text
    assert "policy_preflight" in text


def test_linux_bench_profile_runs_guarded_recall_and_policy_gate():
    text = (ROOT / "tests" / "bench_profile.sh").read_text(encoding="utf-8")
    assert "eval_recall_guarded.json" in text
    assert "--signal-policy" in text
    assert "guarded" in text
    assert "ops/recall_policy_gate.py" in text
    assert "recall_policy_gate.json" in text
    assert "ops/recall_policy_preflight.py" in text
    assert "recall_policy_preflight.json" in text
    assert "policy_gate" in text
    assert "policy_preflight" in text
