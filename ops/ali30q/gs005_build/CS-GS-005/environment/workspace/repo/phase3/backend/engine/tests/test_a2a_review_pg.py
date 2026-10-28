"""Postgres integration tests for engine.a2a_review · code-review Important #6.

The sibling unit suite (test_a2a_review.py) uses a FakeConn that does NOT parse
SQL · the cycle-8 schema bug (msg_id vs message_id) slipped past unit tests and
was caught only by real cloud E2E. This file closes that gap.

Activation:
    Set DATABASE_URL env (or NAUTILUS_TEST_DATABASE_URL for an isolated test DB)
    to a Postgres with the platform_agent_messages table. Tests auto-skip when
    DATABASE_URL is missing or the connection cannot be established within 3s.

What this catches that mocks miss:
    - Column-name typos (regression guard for the msg_id bug)
    - Missing columns / NOT NULL / NULL-default violations
    - JSONB cast syntax errors
    - ON CONFLICT unique-index assumption
    - Trigger side effects (e.g. fn_mark_a2a_replied · sla_status flips)
    - thread_id column existence (was assumed metadata-only · actually top-level)

Cleanup contract:
    All inserts use message_id prefix 'pgtest_engine_rev_<run_id>_' so a final
    DELETE removes only test rows. Run id is per-session uuid to avoid cross-run
    contention.
"""
from __future__ import annotations

import json
import os
import secrets
import time
import uuid
from typing import Generator

import pytest

# Pull DATABASE_URL early so the skipif decorator can see it.
DB_URL = os.getenv("NAUTILUS_TEST_DATABASE_URL") or os.getenv("DATABASE_URL", "")

# SQLAlchemy requires explicit dialect prefix if neither psycopg2 nor psycopg
# is the default · normalize to whichever driver is installed.
if DB_URL and DB_URL.startswith("postgresql://"):
    try:
        import psycopg  # noqa: F401
        DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        try:
            import psycopg2  # noqa: F401
            DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            DB_URL = ""  # No driver · force skip


def _connect_or_skip():
    if not DB_URL:
        pytest.skip("DATABASE_URL not set or no psycopg driver installed")
    from sqlalchemy import create_engine
    try:
        eng = create_engine(DB_URL, connect_args={"connect_timeout": 3})
        with eng.connect():
            pass
        return eng
    except Exception as e:
        pytest.skip(f"Postgres connect failed: {type(e).__name__}: {str(e)[:120]}")


@pytest.fixture(scope="module")
def pg_engine():
    eng = _connect_or_skip()
    yield eng
    eng.dispose()


@pytest.fixture
def run_id() -> str:
    """Per-test prefix · keeps inserts isolated + cleanup precise."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(autouse=True)
def _cleanup_after(pg_engine, run_id: str):
    """Delete any rows this test inserted · runs even on failure."""
    yield
    from sqlalchemy import text
    with pg_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM platform_agent_messages WHERE message_id LIKE :pat"),
            {"pat": f"pgtest_engine_rev_{run_id}_%"},
        )
        conn.execute(
            text("DELETE FROM platform_agent_messages WHERE thread_id LIKE :pat"),
            {"pat": f"pgtest_thr_{run_id}_%"},
        )


# ---------- SCHEMA REGRESSION GUARD ----------


def test_required_columns_exist(pg_engine):
    """If this fails, a2a_review.py SQL will break. Pin the contract."""
    from sqlalchemy import text
    expected = {
        "message_id", "thread_id", "from_agent", "to_agent",
        "content", "msg_type", "status", "sent_at", "in_reply_to", "metadata",
    }
    with pg_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='platform_agent_messages'"
        )).fetchall()
    actual = {r.column_name for r in rows}
    missing = expected - actual
    assert not missing, f"platform_agent_messages missing required columns: {missing}"


# ---------- SEND ----------


def test_send_batch_writes_n_rows_in_one_transaction(pg_engine, run_id: str):
    """Important #1 · 3 targets ship in one atomic transaction."""
    from sqlalchemy import text
    from engine.a2a_review import _send_requests_batch

    thread_id = f"pgtest_thr_{run_id}_send"
    task_id = f"pgtest_engine_rev_{run_id}_task"
    targets = ["pgtest_v5", "pgtest_v7", "pgtest_kairos"]

    msg_ids = _send_requests_batch(
        pg_engine, targets, thread_id, "test review request", task_id
    )
    assert set(msg_ids.keys()) == set(targets)
    assert all(m.startswith("engine_rev_") for m in msg_ids.values())

    # Verify rows landed
    with pg_engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM platform_agent_messages WHERE thread_id = :t"),
            {"t": thread_id},
        ).scalar()
    assert count == 3

    # Manual cleanup since these messages use real `engine_rev_` prefix not `pgtest_`
    with pg_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM platform_agent_messages WHERE thread_id = :t"),
            {"t": thread_id},
        )


# ---------- POLL ----------


def test_poll_returns_none_when_no_reply(pg_engine, run_id: str):
    from engine.a2a_review import _poll_reply
    thread_id = f"pgtest_thr_{run_id}_noreply"
    result = _poll_reply(pg_engine, "pgtest_v5", "pgtest_nomatch_xyz", thread_id)
    assert result is None


def test_poll_finds_reply_via_in_reply_to(pg_engine, run_id: str):
    from sqlalchemy import text
    from engine.a2a_review import _poll_reply

    thread_id = f"pgtest_thr_{run_id}_irto"
    our_mid = f"pgtest_engine_rev_{run_id}_irto_msg"

    # Inject a synthetic reply
    with pg_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO platform_agent_messages "
            "(message_id, thread_id, from_agent, to_agent, content, msg_type, "
            " status, sent_at, in_reply_to, metadata) "
            "VALUES (:m, :t, :f, 'nautilus_engine', :c, 'review_reply', "
            " 'unread', NOW(), :ir, CAST('{}' AS jsonb)) "
            "ON CONFLICT (message_id) DO NOTHING"
        ), {
            "m": f"pgtest_engine_rev_{run_id}_irto_reply",
            "t": thread_id,
            "f": "pgtest_v5",
            "c": "I approve this change",
            "ir": our_mid,
        })

    # Send started just before injection · since_epoch covers the reply
    opinion = _poll_reply(
        pg_engine, "pgtest_v5", our_mid, thread_id,
        since_epoch=time.time() - 60,
    )
    assert opinion is not None
    assert opinion.verdict == "approve"
    assert "approve" in opinion.text.lower()


def test_poll_finds_reply_via_thread_id_fallback(pg_engine, run_id: str):
    from sqlalchemy import text
    from engine.a2a_review import _poll_reply

    thread_id = f"pgtest_thr_{run_id}_tidfb"

    with pg_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO platform_agent_messages "
            "(message_id, thread_id, from_agent, to_agent, content, msg_type, "
            " status, sent_at, metadata) "
            "VALUES (:m, :t, :f, 'nautilus_engine', :c, 'review_reply', "
            " 'unread', NOW(), CAST('{}' AS jsonb)) "
            "ON CONFLICT (message_id) DO NOTHING"
        ), {
            "m": f"pgtest_engine_rev_{run_id}_tidfb_reply",
            "t": thread_id,
            "f": "pgtest_v7",
            "c": "Reject · breaks contract",
        })

    opinion = _poll_reply(
        pg_engine, "pgtest_v7", "pgtest_no_such_mid", thread_id,
        since_epoch=time.time() - 60,
    )
    assert opinion is not None
    assert opinion.verdict == "reject"


def test_poll_since_epoch_excludes_old_messages(pg_engine, run_id: str):
    """Important #2 regression · stale reply pickup bounded."""
    from sqlalchemy import text
    from engine.a2a_review import _poll_reply

    thread_id = f"pgtest_thr_{run_id}_since"

    # Insert a reply with sent_at = 2 hours ago
    with pg_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO platform_agent_messages "
            "(message_id, thread_id, from_agent, to_agent, content, msg_type, "
            " status, sent_at, metadata) "
            "VALUES (:m, :t, :f, 'nautilus_engine', :c, 'review_reply', "
            " 'unread', NOW() - INTERVAL '2 hours', CAST('{}' AS jsonb)) "
            "ON CONFLICT (message_id) DO NOTHING"
        ), {
            "m": f"pgtest_engine_rev_{run_id}_since_old",
            "t": thread_id,
            "f": "pgtest_v5",
            "c": "approve · this is an old stale reply",
        })

    # since_epoch = 1h ago · should NOT pick up the 2h-old message
    opinion = _poll_reply(
        pg_engine, "pgtest_v5", "any_mid", thread_id,
        since_epoch=time.time() - 3600,
    )
    assert opinion is None

    # Same query without the bound · would pick it up
    opinion = _poll_reply(
        pg_engine, "pgtest_v5", "any_mid", thread_id,
        since_epoch=time.time() - 86400,  # 1 day window
    )
    assert opinion is not None
    assert opinion.verdict == "approve"
