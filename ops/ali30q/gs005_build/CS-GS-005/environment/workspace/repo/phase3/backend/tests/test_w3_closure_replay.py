"""W3.2 closure 验收锚 · end-to-end replay of the two real buyer verdicts through
the new platform path: ingest (W1.2) → persist (W1.1) → visible in soul/activity
(W2.1).

This proves "1 条线可靠地闭": a real FDE verdict flows from a producer into the
platform substrate and becomes observable, with PoI-ready fields, WITHOUT any
self-referential NAU/votes step.

Payloads are the representative shapes of the two real verdicts:
  - data_001: 11/11 items pass, overall_pass, no veto (v5 · docx/xlsx/pptx)
  - data_002: 10/12 items pass, overall_pass, no veto (4 否决项 c2/c9/c10/c11 全过 ·
    c4/c5 non-veto fail · md/pdf)
The literal verdict JSON files live in v5's vtf workspace
(_v5_data001_real_verdict / _v5_data002_real_verdict_20260605.json) — the cloud
replay POSTs those actual files (G-cloud). This test replays their shape locally.
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
from api.fde_verdict import router as fde_router
from api.soul_activity import router as activity_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE engine_cycle_outcomes ("
            "cycle_id TEXT PRIMARY KEY, goal_source TEXT, ship_status TEXT, "
            "git_sha TEXT, composite_score REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
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
    app.include_router(activity_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _data_001_verdict():
    items = [{"id": f"c{i}", "pass": True, "veto": (i in (3, 9, 10, 11)), "reason": ""}
             for i in range(1, 12)]
    return {
        "verdict_id": "data_001-v5-iter1", "task_uid": "data_001", "source": "v5",
        "checklist_uid": "data_001-checklist", "overall_pass": True,
        "veto_failed": False, "score": 1.0, "items": items,
        "artifacts": {"docx": "out.docx", "xlsx": "out.xlsx", "pptx": "out.pptx"},
    }


def _data_002_verdict():
    # 12 items · c4/c5 non-veto fail · veto items c2/c9/c10/c11 all pass · overall_pass
    items = []
    for i in range(1, 13):
        veto = i in (2, 9, 10, 11)
        passed = i not in (4, 5)
        items.append({"id": f"c{i}", "pass": passed, "veto": veto,
                      "reason": "" if passed else "non-veto checklist miss"})
    return {
        "verdict_id": "data_002-v5-iter4", "task_uid": "data_002", "source": "v5",
        "checklist_uid": "data_002-checklist", "overall_pass": True,
        "veto_failed": False, "score": round(10 / 12, 4), "items": items,
        "artifacts": {"md": "report.md", "pdf": "report.pdf"},
    }


def test_two_real_verdicts_replay_to_activity(client):
    # 1. ingest both real verdicts (W1.2)
    for payload in (_data_001_verdict(), _data_002_verdict()):
        r = client.post("/api/platform/fde/verdict", json=payload)
        assert r.status_code == 200, r.text
        assert r.json()["success"] is True

    # 2. each is readable back by task_uid (W1.1 persist)
    g1 = client.get("/api/platform/fde/verdict/data_001").json()["data"]
    assert g1 and g1[0]["score"] == 1.0 and g1[0]["overall_pass"] is True
    g2 = client.get("/api/platform/fde/verdict/data_002").json()["data"]
    assert g2 and g2[0]["overall_pass"] is True and g2[0]["veto_failed"] is False

    # 3. both surface in soul/activity (W2.1 可感知) — the closure
    act = client.get("/api/platform/soul/activity").json()["data"]
    task_uids = {v["task_uid"] for v in act["fde_verdicts"]}
    assert {"data_001", "data_002"} <= task_uids
    assert act["summary"]["verdicts_total"] == 2
    assert act["summary"]["verdicts_passed"] == 2  # both overall_pass


def test_replay_is_idempotent(client):
    """Re-replaying the same verdicts (e.g. a retry) does not double-count."""
    for _ in range(2):
        for payload in (_data_001_verdict(), _data_002_verdict()):
            client.post("/api/platform/fde/verdict", json=payload)

    act = client.get("/api/platform/soul/activity").json()["data"]
    assert act["summary"]["verdicts_total"] == 2, "idempotent ingest · no duplicates"
