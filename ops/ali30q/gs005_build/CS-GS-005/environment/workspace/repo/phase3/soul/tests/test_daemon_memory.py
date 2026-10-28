# -*- coding: utf-8 -*-
"""U17 赋能三件单测:记忆文件免疫性/扩域冲突防护/前缀拼装/失败史警示。"""
from soul import daemon
from soul.config import MEMORY_FILE, SELF_IMPROVE_EXCLUDE, SELF_IMPROVE_SCOPE


def test_memory_file_survives_bootstrap_reset():
    """untracked + .soul- 前缀双保险:硬重置不删,PR 门禁黑名单亦挡。"""
    assert MEMORY_FILE.name.startswith(".soul-")


def test_scope_widened_with_conflict_guard():
    assert "phase3/backend/ops/*.py" in SELF_IMPROVE_SCOPE
    assert "phase3/soul/tests/*.py" in SELF_IMPROVE_SCOPE
    for guarded in ("ops/pr_review", "ops/agent_roster", "ops/auto_ack",
                    "ops/send_org_mail", "ops/ack_org_mail"):
        assert guarded in SELF_IMPROVE_EXCLUDE  # 提案者不得改考官


def test_format_memory_lines():
    lines = daemon._format_memory_lines([
        {"ts": "2026-09-26 01:07:00", "goal": "g1", "ok": False, "note": "checks_failed"},
        {"ts": "2026-09-26 02:07:00", "goal": "g2", "ok": True, "note": "PR http://x/1"},
    ]).splitlines()
    assert "FAIL" in lines[0] and "g1" in lines[0]
    assert "OK" in lines[1] and "PR" in lines[1]


def test_task_prefix_warns_prior_failures(monkeypatch):
    monkeypatch.setattr(daemon, "_org_context", lambda: "你有 2 封未处理组织函件")
    monkeypatch.setattr(daemon, "_memory_load", lambda: [
        {"ts": "t", "goal": "g1", "ok": False, "note": "checks_failed"},
        {"ts": "t", "goal": "g2", "ok": True, "note": "PR"}])
    p = daemon._task_prefix("g1")
    assert "曾失败 1 次" in p and "checks_failed" in p and "组织函件" in p


def test_task_prefix_empty_when_no_signals(monkeypatch):
    monkeypatch.setattr(daemon, "_org_context", lambda: "")
    monkeypatch.setattr(daemon, "_memory_load", lambda: [])
    assert daemon._task_prefix("g-any") == ""  # 零信号=零注入,不吃 prompt 预算


def test_task_prefix_no_cross_goal_leak(monkeypatch):
    """g2 的失败史不得泄进 g1 的前缀(只警同目标)。"""
    monkeypatch.setattr(daemon, "_org_context", lambda: "")
    monkeypatch.setattr(daemon, "_memory_load", lambda: [
        {"ts": "t", "goal": "g2", "ok": False, "note": "checks_failed"}])
    assert daemon._task_prefix("g1") == ""
