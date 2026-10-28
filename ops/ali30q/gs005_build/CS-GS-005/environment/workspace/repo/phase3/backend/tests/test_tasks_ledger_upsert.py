"""DMAS task-layer revival (2026-09-10 activation day) · verdict→tasks ledger.

Every FDE verdict ingested lands a production.tasks row (the 105-day-dead task
ledger) so executed work is visible in the DMAS task layer again. Idempotent on
task_id = "verdict-<task_uid>". DB mocked; no real Postgres.
"""
import sys
import os
from unittest.mock import MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.fde_verdict import _upsert_tasks_ledger
from models.database import Task, TaskStatus, TaskType


def _verdict_row(passed=True, task_uid="g2b1:abc123def456", source="g2-b1-repair-executor",
                 verdict_id="g2b1-abc123def4-minimax_m3", score=1.0):
    row = MagicMock()
    row.task_uid = task_uid
    row.source = source
    row.verdict_id = verdict_id
    row.overall_pass = passed
    row.score = score
    row.external_verified = False
    return row


def _db_without_existing():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None
    return db


def test_pass_verdict_creates_completed_task_row():
    db = _db_without_existing()
    _upsert_tasks_ledger(db, row=_verdict_row(passed=True), producer_agent_id=9000010)
    db.add.assert_called_once()
    t = db.add.call_args.args[0]
    assert isinstance(t, Task)
    assert t.task_id == "verdict-g2b1:abc123def456"
    assert t.publisher == "g2-b1-repair-executor"
    assert t.task_type == TaskType.CODE
    assert t.status == TaskStatus.COMPLETED
    assert t.reward == 0  # B=0 fuel: no income minting
    assert t.agent == "9000010"
    assert t.completed_at is not None
    assert "g2b1-abc123def4-minimax_m3" in t.result
    db.commit.assert_called_once()


def test_fail_verdict_creates_failed_task_row():
    db = _db_without_existing()
    _upsert_tasks_ledger(db, row=_verdict_row(passed=True, verdict_id="v-pass"),
                         producer_agent_id=None)
    _upsert_tasks_ledger(db, row=_verdict_row(passed=False, verdict_id="v-fail"),
                         producer_agent_id=None)
    t = db.add.call_args.args[0]
    assert t.status == TaskStatus.FAILED
    assert t.completed_at is None
    assert t.agent == "unknown"


def test_idempotent_on_existing_task_id():
    db = _db_without_existing()
    db.query.return_value.filter_by.return_value.first.return_value = Task(
        task_id="verdict-g2b1:abc123def456")
    _upsert_tasks_ledger(db, row=_verdict_row(), producer_agent_id=9000010)
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_long_task_uid_truncated_to_column_limit():
    db = _db_without_existing()
    long_uid = "g2b1:" + "a" * 120
    _upsert_tasks_ledger(db, row=_verdict_row(task_uid=long_uid), producer_agent_id=1)
    t = db.add.call_args.args[0]
    assert len(t.task_id) <= 66


def test_timestamps_naive_utc():
    """Column is timestamp WITHOUT time zone; tz-aware would be misread (-8h)."""
    db = _db_without_existing()
    _upsert_tasks_ledger(db, row=_verdict_row(), producer_agent_id=1)
    t = db.add.call_args.args[0]
    assert t.completed_at.tzinfo is None
    assert t.created_at.tzinfo is None
    assert isinstance(t.completed_at, datetime)
