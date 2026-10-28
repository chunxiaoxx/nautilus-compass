"""Goal-stack priority sorter · P1 governance > P2 agent dispatch > P3 self-reflection."""
from __future__ import annotations
from soul.goal_stack import next_goal, GoalSource


def test_priority_p1_governance_wins(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance",
                        lambda: {"id": "gov-1", "task": "fix-thing"})
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch",
                        lambda: {"id": "dispatch-1", "task": "add-feature"})
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "gov-1"
    assert source == GoalSource.P1_GOVERNANCE


def test_priority_p2_when_p1_empty(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch",
                        lambda: {"id": "dispatch-1", "task": "add-feature"})
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "dispatch-1"
    assert source == GoalSource.P2_AGENT_DISPATCH


def test_priority_p3_fallback_when_p1_p2_empty(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection",
                        lambda: {"id": "reflect-1", "task": "refactor"})
    goal, source = next_goal()
    assert goal["id"] == "reflect-1"
    assert source == GoalSource.P3_SELF_REFLECTION


def test_all_empty_returns_none(monkeypatch):
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p3_self_reflection", lambda: None)
    goal, source = next_goal()
    assert goal is None
    assert source is None
