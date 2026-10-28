"""DMAS #3 · FDE 生产线 dispatch substrate v1 (clean track · no NAU/bounty).

The dispatch lifecycle V5 will consume: open → claim → report → settled(verdict).
Decoupled from academic_tasks / platform_bounties (红线别复活). Reward = external
FDE verdict (verdict-bus), not internal NAU.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register relationship target
from models.fde_dispatch import FdeDispatch  # noqa: F401 · register fde_dispatch
from models.fde_verdict import FdeVerdict  # noqa: F401 · register fde_verdicts
from utils.database import get_db
from api.fde_dispatch import router as fde_router


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # a verdict already exists for data_001 (loop closed once → settled).
        conn.execute(text(
            "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, created_at) "
            "VALUES ('fde-data_001-x','data_001','fde-capsule-v5',1,0,1.0,'[]','{}',CURRENT_TIMESTAMP)"
        ))
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(fde_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_dispatch_creates_open_task_no_bounty_fields(client):
    r = client.post("/api/platform/fde/dispatch", json={
        "task_uid": "data_010", "title": "买方题 010", "description": "造一份…"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["task_uid"] == "data_010"
    assert d["status"] == "open"
    # clean track · must NOT carry bounty/NAU fields
    assert "marketplace_open" not in d and "min_bid_nau" not in d and "token_reward" not in d


def test_dispatch_idempotent(client):
    body = {"task_uid": "data_011", "title": "t", "description": "d"}
    client.post("/api/platform/fde/dispatch", json=body)
    r2 = client.post("/api/platform/fde/dispatch", json=body)
    assert r2.json()["data"]["idempotent"] is True


def test_report_persists_output_for_scoring(client):
    """produce→verdict spine: /report stores the produced output so the scorer can
    pull it via GET /tasks?status=produced (V5 6/6 flag fix)."""
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_020", "title": "t", "description": "d"})
    client.post("/api/platform/fde/claim", json={"task_uid": "data_020", "agent_id": "nautilus-prime-001"})
    out = {"text": "交付答案正文…", "artifacts": {"xlsx": "s3://…/a.xlsx"}}
    rr = client.post("/api/platform/fde/report",
                     json={"task_uid": "data_020", "agent_id": "nautilus-prime-001", "output": out})
    assert rr.status_code == 200
    assert rr.json()["data"]["output"] == out

    # scorer pulls produced queue → sees the output to score
    produced = client.get("/api/platform/fde/tasks", params={"status": "produced"}).json()["data"]["tasks"]
    t = next(x for x in produced if x["task_uid"] == "data_020")
    assert t["output"] == out


def test_report_without_output_still_works(client):
    """output is optional — a status-only report is still valid (backward compat)."""
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_021", "title": "t", "description": "d"})
    client.post("/api/platform/fde/claim", json={"task_uid": "data_021", "agent_id": "a1"})
    rr = client.post("/api/platform/fde/report", json={"task_uid": "data_021", "agent_id": "a1"})
    assert rr.status_code == 200
    assert rr.json()["data"]["status"] == "produced"
    assert rr.json()["data"]["output"] is None


def test_agent_pull_claim_report_lifecycle(client):
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_012", "title": "t", "description": "d"})

    # agent pulls open tasks
    opened = client.get("/api/platform/fde/tasks", params={"status": "open"}).json()["data"]["tasks"]
    assert any(t["task_uid"] == "data_012" for t in opened)

    # agent claims
    rc = client.post("/api/platform/fde/claim", json={"task_uid": "data_012", "agent_id": "nautilus-prime-001"})
    assert rc.status_code == 200
    assert rc.json()["data"]["status"] == "claimed"
    assert rc.json()["data"]["claimed_by"] == "nautilus-prime-001"

    # agent reports completion
    rr = client.post("/api/platform/fde/report", json={"task_uid": "data_012", "agent_id": "nautilus-prime-001"})
    assert rr.status_code == 200
    assert rr.json()["data"]["status"] == "produced"


def test_claim_rejects_already_claimed(client):
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_013", "title": "t", "description": "d"})
    client.post("/api/platform/fde/claim", json={"task_uid": "data_013", "agent_id": "a1"})
    r = client.post("/api/platform/fde/claim", json={"task_uid": "data_013", "agent_id": "a2"})
    assert r.status_code == 409  # already claimed by a1


def test_list_joins_verdict_and_marks_settled(client):
    # data_001 has a verdict → settled; data_014 open → not settled
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_001", "title": "t", "description": "d"})
    client.post("/api/platform/fde/dispatch", json={"task_uid": "data_014", "title": "t", "description": "d"})
    data = client.get("/api/platform/fde/tasks").json()["data"]
    tasks = {t["task_uid"]: t for t in data["tasks"]}
    assert tasks["data_001"]["verdict"]["overall_pass"] is True
    assert tasks["data_001"]["status"] == "settled"   # verdict present → settled
    assert tasks["data_014"]["verdict"] is None
    assert data["summary"]["settled"] >= 1


def test_dispatch_requires_task_uid(client):
    r = client.post("/api/platform/fde/dispatch", json={"title": "x", "description": "y"})
    assert r.status_code == 400
