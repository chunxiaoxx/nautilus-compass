"""W2.1 可感知 · GET /api/platform/soul/activity (read-only platform activity).

Surfaces what the soul/platform is actually DOING — recent engine cycles +
FDE verdicts + a成绩 summary — WITHOUT touching the self-referential internal
economy (pending_nau_rewards / votes). The endpoint must work even when those
tables don't exist (proof it never queries them).
"""
from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401 · register table
from utils.database import get_db
from api.soul_activity import router as activity_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    # engine_cycle_outcomes is a raw-SQL table (not an ORM model) · create minimal shape.
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE engine_cycle_outcomes ("
            "cycle_id TEXT PRIMARY KEY, goal_source TEXT, ship_status TEXT, "
            "git_sha TEXT, composite_score REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO engine_cycle_outcomes (cycle_id, goal_source, ship_status, git_sha) "
            "VALUES ('1780000001','p1_governance','success','abc123def')"
        ))
        conn.execute(text(
            "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, created_at) "
            "VALUES ('data_001-v5','data_001','v5',1,0,1.0,'[]','{}',CURRENT_TIMESTAMP)"
        ))
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(activity_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_activity_returns_cycles_verdicts_and_summary(client):
    r = client.get("/api/platform/soul/activity")
    assert r.status_code == 200, r.text
    data = r.json()["data"]

    assert any(c["cycle_id"] == "1780000001" and c["ship_status"] == "success"
               for c in data["recent_cycles"])
    assert any(v["task_uid"] == "data_001" and v["overall_pass"] is True
               for v in data["fde_verdicts"])

    s = data["summary"]
    assert s["cycles_total"] >= 1
    assert s["ships_success"] >= 1
    assert s["verdicts_passed"] >= 1
    assert s["verdicts_total"] >= 1


def test_activity_does_not_query_nau_or_votes(client):
    """The endpoint must succeed with NO pending_nau_rewards / votes tables in the
    DB — proving it never reads the self-referential economy (anchor #3)."""
    # the fixture DB deliberately lacks those tables; a clean 200 is the proof.
    r = client.get("/api/platform/soul/activity")
    assert r.status_code == 200
    body = r.json()
    assert "nau" not in str(body).lower().replace("nautilus", "")
