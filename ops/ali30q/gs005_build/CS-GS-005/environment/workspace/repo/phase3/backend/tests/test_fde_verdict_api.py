"""W1.2 verdict-bus ingest endpoint · POST/GET /api/platform/fde/verdict.

The platform's intake for FDE checklist verdicts (soul/v5 → platform substrate).
Idempotent on verdict_id (re-ingest is safe). GET reads back by task_uid so
compass / soul-activity / data_001 回放 all share one persisted source of truth.
"""
from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register AgentSurvival mapper
import models.fde_dispatch  # noqa: F401 · register FdeDispatch mapper
from models.fde_verdict import FdeVerdict  # noqa: F401 · register table on Base
from models.fde_dispatch import FdeDispatch
from utils.database import get_db
from api.fde_verdict import router as fde_router


@pytest.fixture
def db_and_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # share one in-memory connection across threads/requests
    )
    Base.metadata.create_all(engine)
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
    return TestingSessionLocal, TestClient(app)


@pytest.fixture
def client(db_and_client):
    _, client = db_and_client
    return client


def _data_001_payload():
    return {
        "verdict_id": "data_001-v5-iter1",
        "task_uid": "data_001",
        "source": "v5",
        "checklist_uid": "data_001-checklist",
        "overall_pass": True,
        "veto_failed": False,
        "score": 1.0,
        "items": [{"id": "c2", "pass": True, "veto": True, "reason": ""}],
        "artifacts": {"docx": "out.docx"},
    }


def test_post_verdict_persists_and_get_reads_back(client):
    r = client.post("/api/platform/fde/verdict", json=_data_001_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["data"]["verdict_id"] == "data_001-v5-iter1"

    g = client.get("/api/platform/fde/verdict/data_001")
    assert g.status_code == 200
    gbody = g.json()
    assert gbody["success"] is True
    verdicts = gbody["data"]
    assert isinstance(verdicts, list) and len(verdicts) == 1
    v = verdicts[0]
    assert v["task_uid"] == "data_001"
    assert v["overall_pass"] is True
    assert v["score"] == 1.0
    assert v["items"][0]["id"] == "c2"
    assert v["artifacts"]["docx"] == "out.docx"


def test_post_verdict_is_idempotent_on_verdict_id(client):
    client.post("/api/platform/fde/verdict", json=_data_001_payload())
    # second identical POST must not create a duplicate
    r2 = client.post("/api/platform/fde/verdict", json=_data_001_payload())
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"].get("idempotent") is True

    g = client.get("/api/platform/fde/verdict/data_001")
    assert len(g.json()["data"]) == 1, "idempotent ingest must keep exactly one row"


def test_post_missing_required_field_rejected(client):
    bad = _data_001_payload()
    del bad["task_uid"]
    r = client.post("/api/platform/fde/verdict", json=bad)
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_get_unknown_task_returns_empty_list(client):
    g = client.get("/api/platform/fde/verdict/nonexistent")
    assert g.status_code == 200
    assert g.json()["data"] == []


def test_post_verdict_auto_fills_producer_agent_id_from_dispatch_claim(db_and_client):
    Session, client = db_and_client
    db = Session()
    db.add(FdeDispatch(
        task_uid="data_001",
        title="Data flow 001",
        description="{}",
        status="produced",
        claimed_by="nautilus-prime-001",
    ))
    db.commit()
    db.close()

    r = client.post("/api/platform/fde/verdict", json=_data_001_payload())
    assert r.status_code == 200, r.text
    verdict = r.json()["data"]
    assert verdict["artifacts"]["producer_agent_id"] == 9000002

