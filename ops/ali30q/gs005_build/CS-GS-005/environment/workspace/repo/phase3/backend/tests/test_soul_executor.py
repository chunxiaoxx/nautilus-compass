"""Tests for Soul executor · governance-route consumer (Inc 1 Sub-task 2).

DB + ship_fn are faked; no real Postgres / git. Mirrors the pattern in
`test_soul_consumer.py` and extends FakeDB to capture the SELECT statement
text so we can assert the WHERE-clause filters (type='code' / resolved_by IS
NULL) without standing up a real database.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services import soul_executor
from services import proposal_consensus


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeResultProxy:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeDB:
    """Captures execute() calls + the SELECT SQL text for substring assertions.

    Returns seeded rows for the SELECT; records every UPDATE params dict in
    `self.updates`; counts commits in `self.commits`. The exact SQL string
    passed to the first SELECT is saved as `self.select_sql` so tests 4+5
    can assert the WHERE clause filters are present.
    """

    def __init__(self, rows):
        self._rows = rows
        self.updates = []
        self.claims = []
        self.commits = 0
        self.select_sql = None
        self.select_params = None

    def execute(self, stmt, params=None):
        sql = str(stmt)
        sql_l = sql.lower()
        if "select" in sql_l and self.select_sql is None:
            self.select_sql = sql
            self.select_params = params
            return _FakeResultProxy(self._rows)
        # W4.2 peek-and-claim UPDATE...RETURNING · infrastructure, not a writeback.
        # Return a non-empty row so the claim succeeds (this consumer wins).
        if "claiming" in sql_l and "returning" in sql_l:
            self.claims.append(params)
            return _FakeResultProxy([(params.get("pid"), "x")])
        # writeback UPDATE
        self.updates.append(params)
        return _FakeResultProxy([])

    def commit(self):
        self.commits += 1


# ---------------------------------------------------------------------------
# Tests 1-6: executor behavior (per plan §"Sub-task 2 · Tests")
# ---------------------------------------------------------------------------


def test_executor_ships_and_writes_back_ok():
    """Row with type='code' + task ships successfully; writeback marks executed_ok."""
    db = _FakeDB(rows=[("gov-1", {"type": "code", "task": "add util"})])

    def fake_ship(task, base_dir, branch, commit_msg, cycle_id=None):
        assert task == "add util"
        assert branch == "soul/gov-gov-1"
        assert commit_msg.startswith("soul: gov proposal gov-1")
        assert cycle_id == "gov-gov-1"
        return {
            "success": True,
            "pr_url": "https://github.com/x/y/pull/42",
            "cycle_id": cycle_id,
        }

    out = soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", limit=5, _ship_fn=fake_ship
    )

    assert len(out) == 1
    assert out[0]["shipped"] is True
    assert out[0]["status"] == "executed_ok"
    assert "pull/42" in out[0]["pr_url"]

    # writeback fired exactly once
    assert db.commits == 2  # claim + writeback
    assert len(db.claims) == 1 and db.claims[0]["pid"] == "gov-1"
    assert len(db.updates) == 1
    upd = db.updates[0]
    assert upd["pid"] == "gov-1"
    assert upd["status"] == "executed_ok"
    assert "pull/42" in upd["note"]
    # DRAFT PR phrasing carries the human-review-required reminder
    assert "DRAFT PR" in upd["note"]


def test_executor_writes_failed_on_check_stage_fail():
    """Ship returns success=False at check stage → status=executed_failed + note."""
    db = _FakeDB(rows=[("gov-2", {"type": "code", "task": "make it faster"})])

    def fake_ship(task, base_dir, branch, commit_msg, cycle_id=None):
        return {
            "success": False,
            "stage": "check",
            "detail": "ruff failed",
            "cycle_id": cycle_id,
        }

    out = soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", _ship_fn=fake_ship
    )

    assert len(out) == 1
    assert out[0]["shipped"] is False
    assert out[0]["status"] == "executed_failed"

    assert db.commits == 2  # claim + writeback
    upd = db.updates[0]
    assert upd["pid"] == "gov-2"
    assert upd["status"] == "executed_failed"
    assert "check" in upd["note"]
    assert "ruff failed" in upd["note"]


def test_executor_writes_failed_on_missing_task():
    """proposed_change={'type':'code'} (no task) → no ship call, writeback fail-note."""
    db = _FakeDB(rows=[("gov-3", {"type": "code"})])  # NO 'task' key

    call_count = {"n": 0}

    def fake_ship(*args, **kwargs):
        call_count["n"] += 1
        return {"success": True, "pr_url": "should-not-be-called"}

    out = soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", _ship_fn=fake_ship
    )

    # Ship was NOT invoked
    assert call_count["n"] == 0

    assert len(out) == 1
    assert out[0]["shipped"] is False
    assert out[0]["status"] == "executed_failed"

    # writeback still happened (so the row terminates)
    assert db.commits == 1
    upd = db.updates[0]
    assert upd["pid"] == "gov-3"
    assert upd["status"] == "executed_failed"
    assert "task missing" in upd["note"].lower() or "task" in upd["note"]


def test_executor_skips_non_code_type():
    """SELECT WHERE clause must filter on (proposed_change->>'type')='code'.

    We assert the executor's emitted SQL contains the JSONB type filter so a
    row with type='experiment' would be excluded at the database level. (We
    don't need to fake non-code rows being returned because the WHERE clause
    is the filter mechanism; testing the SQL guarantees the contract.)
    """
    db = _FakeDB(rows=[])

    out = soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", _ship_fn=lambda *a, **k: {}
    )

    assert out == []
    assert db.select_sql is not None
    # The JSONB type discriminator must be in the WHERE clause
    assert "proposed_change->>'type'" in db.select_sql
    assert "'code'" in db.select_sql


def test_executor_skips_already_resolved():
    """SELECT WHERE clause must include resolved_by IS NULL filter.

    Asserts the SQL contract that already-resolved rows (resolved_by='soul')
    cannot be picked up a second time, preventing double-ship.
    """
    db = _FakeDB(rows=[])

    soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", _ship_fn=lambda *a, **k: {}
    )

    assert db.select_sql is not None
    assert "resolved_by IS NULL" in db.select_sql


def test_executor_empty_queue_noop():
    """0 rows → no UPDATE, no commit, empty return."""
    db = _FakeDB(rows=[])

    def fake_ship(*args, **kwargs):
        raise AssertionError("ship_fn must not be called on empty queue")

    out = soul_executor.execute_accepted_proposals(
        db, "/tmp/ws", _ship_fn=fake_ship
    )

    assert out == []
    assert db.commits == 0
    assert db.updates == []


# ---------------------------------------------------------------------------
# Tests 7-8: consensus router type-gate (per plan §"Type-route gating")
# ---------------------------------------------------------------------------


class _FactoryCounter:
    """Counts how many times the db_factory is invoked.

    `on_consensus_reached` calls `db_factory()` to open a sandbox session
    only when it actually creates a sandbox experiment. For type='code'
    rows it must short-circuit BEFORE calling the factory; for non-code
    types it must still invoke the factory.
    """

    def __init__(self):
        self.called = 0

    def __call__(self):
        self.called += 1
        return _NullSession()


class _NullSession:
    """No-op session so `db.close()` in the sandbox branch doesn't crash."""

    def close(self):
        pass


def test_consensus_route_skips_sandbox_when_type_is_code():
    """type='code' must short-circuit; db_factory must NOT be called."""
    factory = _FactoryCounter()

    proposal_consensus.on_consensus_reached(
        "pid-1",
        {"type": "code", "task": "extract helper"},
        factory,
    )

    assert factory.called == 0


def test_consensus_route_creates_sandbox_when_type_is_not_code(monkeypatch):
    """type='experiment' must NOT short-circuit; db_factory IS called.

    Monkeypatches `services.sandbox.create_experiment` so we don't actually
    create real sandbox rows; we just verify the factory was invoked
    (meaning the non-code branch fired).
    """
    factory = _FactoryCounter()

    create_calls = {"n": 0}

    def fake_create_experiment(db, proposal_id, proposed_change):
        create_calls["n"] += 1
        return "exp-sentinel-1"

    # Patch the symbol that on_consensus_reached imports inside its try block.
    import services.sandbox as sandbox_mod
    monkeypatch.setattr(sandbox_mod, "create_experiment", fake_create_experiment)

    proposal_consensus.on_consensus_reached(
        "pid-2",
        {"type": "experiment", "task": "try alternate routing weights"},
        factory,
    )

    # The non-code branch invoked the factory exactly once
    assert factory.called == 1
    # And ran create_experiment on the resulting session
    assert create_calls["n"] == 1
