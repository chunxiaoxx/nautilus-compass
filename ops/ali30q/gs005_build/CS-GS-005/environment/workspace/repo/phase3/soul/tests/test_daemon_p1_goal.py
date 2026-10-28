"""W4.1 止血 · daemon.run_once must handle P1 governance goals without KeyError.

P1 governance rows (goal_stack._next_p1_governance) carry only
{id, proposal_id, proposed_change} — NO `description` key. The shared ship
path reads goal["description"] (daemon.py:685), so a raw P1 row raises
KeyError: 'description' and the entire P1 governance route is dead.

The adapter (mirroring the P2 task_spec→description copy at daemon.py:629-630)
must derive a codegen-friendly description from proposed_change before the
shared ship path runs. proposed_change may be a JSON blob (daemon self-writes)
or a natural-language task spec (compass/V5 voted proposals) — both must
surface a non-empty, actionable ship task.
"""
from __future__ import annotations
import json
from soul import daemon
from soul.goal_stack import GoalSource


class _FakeResult:
    def __init__(self, passed=True, applied=True, files=None, git_commit="abc1234"):
        self.check_result = {"passed": passed}
        self.applied = applied
        self.git_commit = git_commit
        self.files_planned = files or [{"path": "phase3/soul/__init__.py", "size": 200}]


def _fake_git(monkeypatch):
    def fake_run(cmd, **kw):
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()
    monkeypatch.setattr(daemon.subprocess, "run", fake_run)


def _baseline_gates(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "record_cost", lambda *a, **k: None)
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: False)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    monkeypatch.setattr(daemon.failure_track, "record_success", lambda: None)
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: None)
    monkeypatch.setattr(daemon, "_emit_goal_source_to_outcome", lambda cid, src: None)


def test_daemon_p1_governance_goal_no_keyerror(monkeypatch):
    """P1 row without `description` must NOT raise KeyError and must ship the
    proposed_change as the task. This is the W4.1 止血 regression guard."""
    _baseline_gates(monkeypatch)

    fake_p1 = {
        "id": "gov-42",
        "proposal_id": 42,
        "proposed_change": "Add input validation to the /api/foo endpoint handler.",
    }
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (fake_p1, GoalSource.P1_GOVERNANCE),
    )

    ship_calls = []

    def _fake_ship(engine, task_desc, repo, **kw):
        ship_calls.append(task_desc)
        return _FakeResult(passed=True, applied=True)

    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(), _fake_ship))
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: "http://pr/gov-42")

    # Must not raise KeyError: 'description'
    rc = daemon.run_once()

    assert rc == 0, "P1 governance cycle should complete (no crash)"
    assert len(ship_calls) == 1, "ship called exactly once for the P1 goal"
    task = ship_calls[0]
    assert task and task.strip(), "ship task must be non-empty"
    assert "input validation" in task, (
        "the proposed_change text must reach engine.ship as the goal description"
    )


def test_daemon_p1_json_proposed_change_yields_actionable_task(monkeypatch):
    """A JSON-blob proposed_change (daemon self-write shape) must still produce a
    non-empty actionable ship task, not a raw JSON dump or empty string."""
    _baseline_gates(monkeypatch)

    fake_p1 = {
        "id": "gov-7",
        "proposal_id": 7,
        "proposed_change": json.dumps({
            "description": "Refactor cache eviction to LRU.",
            "type": "code",
        }),
    }
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (fake_p1, GoalSource.P1_GOVERNANCE),
    )

    ship_calls = []
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda e, t, r, **kw: (ship_calls.append(t),
                                                        _FakeResult())[1]))
    _fake_git(monkeypatch)
    monkeypatch.setattr(daemon.pr_gate, "create_draft_pr",
                        lambda b, t, body: "http://pr/gov-7")

    rc = daemon.run_once()
    assert rc == 0
    assert len(ship_calls) == 1
    assert "Refactor cache eviction to LRU." in ship_calls[0], (
        "JSON proposed_change should surface its description field as the task"
    )
