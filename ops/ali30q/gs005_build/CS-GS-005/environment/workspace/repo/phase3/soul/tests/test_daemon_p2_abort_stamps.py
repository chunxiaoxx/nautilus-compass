"""Slice B backlog-blocker sentinel · daemon abort paths must stamp the P2
dispatch row's ship_outcome so a doomed row does not block the queue forever.

After PR #81 the daemon only stamped agent_dispatch_log on the success path
(_mark_dispatch_shipped called after pr_gate.create_draft_pr). On every abort
path (engine checks failed / pytest red / pr_gate reject / outer exception)
the row stayed ship_outcome=NULL · _next_p2_agent_dispatch picks the OLDEST
row with NULL outcome · so the very next cycle would re-pick the same doomed
row forever.

These tests lock that the abort paths stamp the dispatch row with a
descriptive outcome (`checks_failed` / `pytest_red` / `pr_gate_reject` /
`exception`) and cycle_id=NULL (no engine_cycle_outcomes row exists yet).
The yaml path (P3 source) must NOT touch the dispatch ledger.
"""
from __future__ import annotations
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


def _baseline(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.budget_gate, "record_cost", lambda *a, **k: None)
    monkeypatch.setattr(daemon.pr_gate, "has_open_pr_for", lambda gid: False)
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (True, "ok"))
    monkeypatch.setattr(daemon.pr_gate, "check_diff_loc", lambda n, m=None: (True, "ok"))
    monkeypatch.setattr(daemon.goal_selector, "mark_done", lambda gid: True)
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: None)
    monkeypatch.setattr(daemon.failure_track, "record_failure", lambda x: None)
    _fake_git(monkeypatch)


def _p2_goal():
    return {
        "id": "dispatch-77",
        "agent_id": 9000002,
        "task_spec": "garbage task that will fail engine.ship checks",
        "task_spec_hash": "x" * 64,
        "task_type": "code",
    }


def _capture_mark(monkeypatch):
    """Spy on _mark_dispatch_shipped · returns list of (id, outcome, cycle_id) tuples."""
    marked = []
    monkeypatch.setattr(daemon, "_mark_dispatch_shipped",
                        lambda did, outcome, cycle_id=None: marked.append((did, outcome, cycle_id)))
    return marked


def test_abort_on_ship_checks_failed_stamps_dispatch_row(monkeypatch):
    """engine.ship returned check_result.passed=False · daemon aborts but must
    still stamp the P2 row with ship_outcome='checks_failed' (cycle_id=None ·
    engine_cycle_outcomes has no row to FK against)."""
    _baseline(monkeypatch)
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (_p2_goal(), GoalSource.P2_AGENT_DISPATCH),
    )
    # ship fails its own checks
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=False, applied=False)))
    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert len(marked) == 1, "abort path must stamp the dispatch row exactly once"
    did, outcome, cycle_id = marked[0]
    assert did == 77
    assert outcome == "checks_failed"
    assert cycle_id is None, "cycle_id must be NULL · no engine_cycle_outcomes row exists yet"


def test_abort_on_pytest_red_stamps_dispatch_row(monkeypatch):
    """_run_pytest returned False (tests red) · same stamp rule applies."""
    _baseline(monkeypatch)
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (_p2_goal(), GoalSource.P2_AGENT_DISPATCH),
    )
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))
    # ship's check passed but pytest gate red
    monkeypatch.setattr(daemon, "_run_pytest", lambda base, paths: False)
    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert len(marked) == 1
    did, outcome, cycle_id = marked[0]
    assert did == 77
    assert outcome == "pytest_red"
    assert cycle_id is None


def test_abort_on_pr_gate_reject_stamps_dispatch_row(monkeypatch):
    """pr_gate.check_paths blocked (blacklisted path) · same stamp rule."""
    _baseline(monkeypatch)
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (_p2_goal(), GoalSource.P2_AGENT_DISPATCH),
    )
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))
    # pr_gate rejects the changed paths
    monkeypatch.setattr(daemon.pr_gate, "check_paths", lambda c: (False, "blocked"))
    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert len(marked) == 1
    did, outcome, cycle_id = marked[0]
    assert did == 77
    assert outcome == "pr_gate_reject"
    assert cycle_id is None


def test_yaml_p3_path_abort_does_not_touch_dispatch_log(monkeypatch):
    """Regression guard · a yaml goal failing checks must NOT stamp the
    dispatch ledger (it isn't a dispatch row)."""
    _baseline(monkeypatch)
    yaml_goal = {"id": "g42", "description": "yaml goal", "source": "yaml"}
    monkeypatch.setattr(daemon.goal_selector, "select_goal", lambda **k: yaml_goal)
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=False, applied=False)))
    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert marked == [], "yaml-goal failure must not stamp the dispatch ledger"


def test_abort_on_engine_import_fail_stamps_dispatch_row(monkeypatch):
    """F11 follow-up · _load_engine raised ImportError BEFORE branch create ·
    daemon must still stamp the P2 row so the queue does not block on this
    doomed dispatch (engine_cycle_outcomes has no row · cycle_id stays None)."""
    _baseline(monkeypatch)
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (_p2_goal(), GoalSource.P2_AGENT_DISPATCH),
    )

    def _raise_import(*a, **k):
        raise ImportError("nautilus_engine missing")
    monkeypatch.setattr(daemon, "_load_engine", _raise_import)

    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert len(marked) == 1, "engine_import_fail must stamp the dispatch row exactly once"
    did, outcome, cycle_id = marked[0]
    assert did == 77
    assert outcome == "engine_import_fail"
    assert cycle_id is None, "cycle_id must be NULL · no engine_cycle_outcomes row exists yet"


def test_abort_on_branch_create_fail_stamps_dispatch_row(monkeypatch):
    """F11 follow-up · git checkout -b returned non-zero AFTER engine import ·
    daemon must still stamp the P2 row (no engine_cycle_outcomes row yet · cycle_id None)."""
    _baseline(monkeypatch)
    monkeypatch.setattr(
        "soul.goal_stack.next_goal",
        lambda: (_p2_goal(), GoalSource.P2_AGENT_DISPATCH),
    )
    monkeypatch.setattr(daemon, "_load_engine",
                        lambda: (lambda **k: object(),
                                 lambda *a, **k: _FakeResult(passed=True, applied=True)))

    # selectively fail only the `checkout -b` invocation · let other _git calls pass
    real_git = daemon._git

    def selective_git(repo, *args):
        if len(args) >= 2 and args[0] == "checkout" and args[1] == "-b":
            class R:
                returncode = 1
                stdout = ""
                stderr = "fatal: branch already exists"
            return R()
        return real_git(repo, *args)

    monkeypatch.setattr(daemon, "_git", selective_git)

    marked = _capture_mark(monkeypatch)

    rc = daemon.run_once()
    assert rc == 1
    assert len(marked) == 1, "branch_create_fail must stamp the dispatch row exactly once"
    did, outcome, cycle_id = marked[0]
    assert did == 77
    assert outcome == "branch_create_fail"
    assert cycle_id is None


def test_mark_dispatch_shipped_accepts_optional_cycle_id(monkeypatch):
    """Helper contract · cycle_id is optional · None must produce a SQL UPDATE
    setting cycle_id to NULL (the SQL placeholder %s with a None argument
    becomes NULL in psycopg2 · no caller-side str coercion needed)."""
    import os
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    sql_calls = []

    class _FakeCursor:
        def execute(self, sql, args):
            sql_calls.append((sql, args))

    class _FakeConn:
        def cursor(self):
            return _FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

    import importlib
    import sys
    fake_pg = type(sys)("psycopg2")
    fake_pg.connect = lambda dsn: _FakeConn()
    monkeypatch.setitem(sys.modules, "psycopg2", fake_pg)

    # default cycle_id=None (positional 2-arg call must work)
    daemon._mark_dispatch_shipped(99, "checks_failed")
    assert len(sql_calls) == 1
    sql, args = sql_calls[0]
    assert "agent_dispatch_log" in sql
    assert args == ("checks_failed", None, 99)
