"""W2.2 · daily activity digest = 成绩 (achievements), NOT a pain list.

The existing enterprise-wechat push surfaced pain points; this digest instead
reports what the platform SHIPPED and what passed FDE QC, from engine_cycle_outcomes
+ fde_verdicts. Read-only · no NAU/votes.
"""
from __future__ import annotations
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.activity_digest import build_daily_activity_digest


def _seeded_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE engine_cycle_outcomes ("
            "cycle_id TEXT PRIMARY KEY, goal_source TEXT, ship_status TEXT, "
            "git_sha TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "CREATE TABLE fde_verdicts ("
            "id INTEGER PRIMARY KEY, verdict_id TEXT, task_uid TEXT, source TEXT, "
            "overall_pass BOOLEAN, veto_failed BOOLEAN, score REAL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO engine_cycle_outcomes (cycle_id, ship_status) VALUES "
            "('c1','success'),('c2','success'),('c3','fail')"
        ))
        conn.execute(text(
            "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score) VALUES "
            "('data_001-v5','data_001','v5',1,0,1.0),"
            "('data_002-v5','data_002','v5',1,0,0.83)"
        ))
    return sessionmaker(bind=engine)()


def test_digest_reports_achievements_not_pain():
    md = build_daily_activity_digest(_seeded_db())
    assert isinstance(md, str) and md.strip()
    # achievements present
    assert "2" in md  # 2 successful cycles AND/OR 2 passed verdicts
    assert "data_001" in md or "verdict" in md.lower()
    # explicitly NOT a pain dump
    assert "Pain:" not in md
    assert "痛点" not in md


def test_digest_counts_cycles_and_verdicts():
    md = build_daily_activity_digest(_seeded_db())
    low = md.lower()
    assert "cycle" in low or "引擎" in md
    assert "verdict" in low or "验收" in md or "qc" in low


def test_digest_failsoft_on_missing_tables():
    """No engine_cycle_outcomes / fde_verdicts tables → still returns a string."""
    engine = create_engine("sqlite://", poolclass=StaticPool)
    db = sessionmaker(bind=engine)()
    md = build_daily_activity_digest(db)
    assert isinstance(md, str)
