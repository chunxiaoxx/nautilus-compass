"""TDD tests for engine.a2a_review · v5agent cycle 8 (Gap 2 + 4).

Wires engine ship → V5/V7/Kairos for async council review via platform_agent_messages.
Sync impl (CLI subprocess context · no asyncio overhead) · DB injection enables mocking.

LIMITATION · per code-review Recommendation 5:
    The FakeConn below routes by parameter shape and never parses SQL. This
    means the following bug classes are INVISIBLE to this test file:
      - Column-name typos (e.g. msg_id vs message_id · cycle 8 schema bug)
      - Missing-column INSERTs / NOT NULL violations
      - JSONB cast errors
      - Trigger side effects
      - ON CONFLICT unique-index assumptions

    Real coverage of the SQL path lives in test_a2a_review_pg.py (Postgres
    integration · requires DATABASE_URL · skipped by default).
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from engine.a2a_review import (
    DEFAULT_TARGETS,
    ReviewOpinion,
    ReviewResult,
    request_review,
)


class FakeRow:
    def __init__(self, content: str, sent_at=None):
        self.content = content
        self.sent_at = sent_at


class FakeConn:
    """Minimal SQLAlchemy connection mock · records sends + returns canned replies."""

    def __init__(self, replies: dict[str, str] | None = None):
        self.replies = replies or {}  # agent -> reply content
        self.sends: list[dict] = []
        self.poll_calls = 0

    def execute(self, statement, params=None):
        params = params or {}
        # Heuristic: INSERT vs SELECT by inspecting params shape
        if "m" in params and "to" in params and "c" in params:
            # INSERT review request
            self.sends.append({"agent": params["to"], "msg_id": params["m"]})
            mock = MagicMock()
            mock.fetchone.return_value = None
            return mock
        # SELECT reply (params: a, mid, tid)
        self.poll_calls += 1
        agent = params.get("a")
        mock = MagicMock()
        if agent in self.replies:
            mock.fetchone.return_value = FakeRow(self.replies[agent])
        else:
            mock.fetchone.return_value = None
        return mock


class FakeEngine:
    def __init__(self, conn: FakeConn):
        self._conn = conn

    @contextmanager
    def begin(self):
        yield self._conn


# ---------- send + receive ----------

def test_sends_request_to_all_default_targets():
    conn = FakeConn()
    engine = FakeEngine(conn)
    request_review(
        task_id="t1", code_diff="x = 1", db_engine=engine,
        timeout_s=1, poll_interval_s=1,
    )
    sent_agents = {s["agent"] for s in conn.sends}
    assert sent_agents == set(DEFAULT_TARGETS)


def test_sends_request_to_custom_targets():
    conn = FakeConn()
    engine = FakeEngine(conn)
    request_review(
        task_id="t2", code_diff="x = 1",
        target_agents=("v5", "v7"),
        db_engine=engine,
        timeout_s=1, poll_interval_s=1,
    )
    sent_agents = {s["agent"] for s in conn.sends}
    assert sent_agents == {"v5", "v7"}


def test_msg_id_includes_task_id_prefix():
    conn = FakeConn()
    engine = FakeEngine(conn)
    request_review(
        task_id="abc12345", code_diff="x", db_engine=engine,
        timeout_s=1, poll_interval_s=1,
        target_agents=("v5",),
    )
    assert any("abc12345"[:20] in s["msg_id"] for s in conn.sends)


# ---------- verdict parsing ----------

def test_aggregates_approve_count():
    conn = FakeConn(replies={
        "nautilus-prime-001": "Looks good, I approve.",
        "v7-telegram": "Solid approach, approve",
        "kairos": "I'm not sure, abstain",
    })
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t3", code_diff="x", db_engine=engine,
        timeout_s=3, poll_interval_s=0,
    )
    assert result.approve_count == 2
    assert result.abstain_count == 1
    assert result.reject_count == 0
    assert result.timeouts == []


def test_aggregates_reject_count():
    conn = FakeConn(replies={
        "nautilus-prime-001": "I REJECT this · security risk",
        "v7-telegram": "approve",
        "kairos": "reject · breaks contract",
    })
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t4", code_diff="x", db_engine=engine,
        timeout_s=3, poll_interval_s=0,
    )
    assert result.reject_count == 2
    assert result.approve_count == 1


def test_no_keyword_defaults_to_abstain():
    conn = FakeConn(replies={
        "nautilus-prime-001": "I have no strong opinion here.",
    })
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t5", code_diff="x", db_engine=engine,
        timeout_s=3, poll_interval_s=0,
        target_agents=("nautilus-prime-001",),
    )
    assert result.abstain_count == 1


# ---------- timeout ----------

def test_records_timeouts_when_no_reply():
    conn = FakeConn(replies={})  # no replies
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t6", code_diff="x", db_engine=engine,
        timeout_s=1, poll_interval_s=0,
    )
    assert sorted(result.timeouts) == sorted(DEFAULT_TARGETS)
    assert result.approve_count == 0
    assert result.reject_count == 0
    assert result.abstain_count == 0


def test_partial_timeout():
    conn = FakeConn(replies={
        "nautilus-prime-001": "approve",
    })
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t7", code_diff="x", db_engine=engine,
        timeout_s=1, poll_interval_s=0,
    )
    assert result.approve_count == 1
    assert set(result.timeouts) == {"v7-telegram", "kairos"}


# ---------- result shape ----------

def test_result_includes_thread_id():
    conn = FakeConn(replies={})
    engine = FakeEngine(conn)
    result = request_review(
        task_id="topic9", code_diff="x", db_engine=engine,
        timeout_s=1, poll_interval_s=0,
        target_agents=("v5",),
    )
    assert result.thread_id == "thr-engine-review-topic9"
    assert result.task_id == "topic9"


def test_opinions_include_raw_text():
    conn = FakeConn(replies={
        "v5": "approve · LGTM",
    })
    engine = FakeEngine(conn)
    result = request_review(
        task_id="t10", code_diff="x", db_engine=engine,
        timeout_s=3, poll_interval_s=0,
        target_agents=("v5",),
    )
    assert "v5" in result.opinions
    assert "LGTM" in result.opinions["v5"]["text"]
    assert result.opinions["v5"]["verdict"] == "approve"
