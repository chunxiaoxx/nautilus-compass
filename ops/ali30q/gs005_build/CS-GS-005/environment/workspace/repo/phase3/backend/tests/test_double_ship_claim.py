"""W4.2 止血 · peek-and-claim prevents double-ship of accepted governance proposals.

Two consumers race on `status='accepted'` rows in platform_improvement_proposals:
  - soul_executor.execute_accepted_proposals (nautilus-soul-executor.timer · SQLAlchemy)
  - the soul daemon's P1 governance path (now active after W4.1)

Both must atomically claim (accepted → claiming) BEFORE shipping. The atomic
`UPDATE ... WHERE status='accepted' RETURNING` is the serialization point: only
one consumer's UPDATE matches a row; the other gets nothing and skips.

This file tests the soul_executor claim primitive on sqlite (the daemon side is
guarded in phase3/soul/tests/test_daemon_p1_claim.py).
"""
from __future__ import annotations
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.soul_executor import _claim_accepted


def _db_with_accepted_row():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE platform_improvement_proposals ("
            "id VARCHAR PRIMARY KEY, proposed_change TEXT, status VARCHAR, "
            "resolved_by VARCHAR, resolved_at TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO platform_improvement_proposals (id, proposed_change, status) "
            "VALUES ('gov-42', '{\"task\":\"do x\",\"type\":\"code\"}', 'accepted')"
        ))
    return sessionmaker(bind=engine)()


def test_claim_is_atomic_only_one_winner():
    db = _db_with_accepted_row()

    first = _claim_accepted(db, "gov-42", "consumer-A")
    assert first is not None, "first consumer claims the accepted row"
    assert first[0] == "gov-42"

    second = _claim_accepted(db, "gov-42", "consumer-B")
    assert second is None, "second consumer must get nothing (row no longer accepted)"


def test_claim_marks_status_claiming():
    db = _db_with_accepted_row()
    _claim_accepted(db, "gov-42", "consumer-A")
    status = db.execute(
        text("SELECT status, resolved_by FROM platform_improvement_proposals WHERE id='gov-42'")
    ).fetchone()
    assert status[0] == "claiming"
    assert status[1] == "consumer-A"


def test_claim_returns_none_for_unknown_or_nonaccepted():
    db = _db_with_accepted_row()
    # already non-accepted
    db.execute(text("UPDATE platform_improvement_proposals SET status='executed_ok' WHERE id='gov-42'"))
    db.commit()
    assert _claim_accepted(db, "gov-42", "x") is None
    # unknown id
    assert _claim_accepted(db, "nope", "x") is None
