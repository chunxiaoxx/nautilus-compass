"""W2.4 · GET /api/platform/proposals/{id} must surface the resolution fields
(resolution_note / resolved_by / resolved_at) so a human/dashboard can see WHY
a governance proposal terminated — not just its status.
"""
from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from utils.database import get_db
from api.platform_proposals import router as proposals_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE platform_improvement_proposals ("
            "id TEXT PRIMARY KEY, task_id INTEGER, agent_id INTEGER, root_cause TEXT, "
            "proposed_change TEXT, expected_impact TEXT, rollback_plan TEXT, "
            "vote_score REAL, vote_count INTEGER, status TEXT, created_at TIMESTAMP, "
            "resolution_note TEXT, resolved_by TEXT, resolved_at TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO platform_improvement_proposals "
            "(id, task_id, agent_id, status, vote_score, vote_count, "
            " resolution_note, resolved_by, resolved_at) "
            "VALUES ('p1', 1, 9000005, 'executed_ok', 2.0, 1, "
            "'Soul shipped DRAFT PR: http://pr/1', 'soul', CURRENT_TIMESTAMP)"
        ))
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(proposals_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_get_proposal_includes_resolution_fields(client):
    r = client.get("/api/platform/proposals/p1")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["status"] == "executed_ok"
    assert data["resolution_note"] == "Soul shipped DRAFT PR: http://pr/1"
    assert data["resolved_by"] == "soul"
    assert data["resolved_at"] is not None
