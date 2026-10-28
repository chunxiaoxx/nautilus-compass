"""Tests for Soul consumer · agent→soul loop closure.

DB + ship_fn are faked; no real Postgres / git.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services import soul_consumer


class _FakeResultProxy:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeDB:
    """Captures execute() calls; returns seeded rows for the SELECT."""
    def __init__(self, rows):
        self._rows = rows
        self.updates = []
        self.commits = 0

    def execute(self, stmt, params=None):
        sql = str(stmt).lower()
        if "select" in sql:
            return _FakeResultProxy(self._rows)
        # UPDATE
        self.updates.append(params)
        return _FakeResultProxy([])

    def commit(self):
        self.commits += 1


def test_consumer_ships_and_writes_back():
    db = _FakeDB(rows=[("prop-1", "add a util function", "feature")])

    def fake_ship(task, base_dir, branch, commit_msg, cycle_id=None):
        assert branch == "soul/prop-1"
        return {"success": True, "pr_url": "https://github.com/x/y/pull/7", "cycle_id": cycle_id}

    out = soul_consumer.consume_pending_proposals(db, "/tmp/ws", limit=5, _ship_fn=fake_ship)
    assert len(out) == 1
    assert out[0]["shipped"] is True
    assert "pull/7" in out[0]["pr_url"]
    # writeback happened
    assert db.commits == 1
    assert db.updates[0]["pid"] == "prop-1"
    assert "DRAFT PR" in db.updates[0]["note"]


def test_consumer_writes_rejection_note_on_gate_fail():
    db = _FakeDB(rows=[("prop-2", "touch .env", "config")])

    def fake_ship(task, base_dir, branch, commit_msg, cycle_id=None):
        return {"success": False, "stage": "pr_gate", "detail": "blacklisted path: .env", "cycle_id": cycle_id}

    out = soul_consumer.consume_pending_proposals(db, "/tmp/ws", _ship_fn=fake_ship)
    assert out[0]["shipped"] is False
    assert "pr_gate" in db.updates[0]["note"]
    assert db.updates[0]["pid"] == "prop-2"


def test_consumer_empty_queue_noop():
    db = _FakeDB(rows=[])
    out = soul_consumer.consume_pending_proposals(db, "/tmp/ws", _ship_fn=lambda *a, **k: {})
    assert out == []
    assert db.commits == 0
