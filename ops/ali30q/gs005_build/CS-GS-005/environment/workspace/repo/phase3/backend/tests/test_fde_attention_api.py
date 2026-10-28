"""FDE attention queue API contract checks.

Human-first loop surfaces require stable create/list/resolve semantics so ops can
react to S1/S2/S3 failures without manual forensics.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401  (registers AgentSurvival for Agent.survival mapper)
import models.fde_attention  # noqa: F401
from models.fde_attention import FdeAttention  # noqa: F401
from api.fde_attention import router as attention_router
from utils.database import get_db


def _build_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
    app.include_router(attention_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestingSessionLocal, TestClient(app)


def test_attention_api_crud_cycle():
    Session, client = _build_fixture()
    db = Session()
    # 预置一条待办，验证读取过滤和排序
    db.add(FdeAttention(
        stage="s2",
        code="s2_empty_submission",
        severity="warning",
        title="S2 empty submission",
        detail="submission is empty",
        suggested_actions=["rerun", "ignore"],
        status="pending",
        task_uid="task_001",
        context={"task_uid": "task_001"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ))
    db.commit()
    db.close()

    r = client.get("/api/platform/fde/attention?status=pending")
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["count"] == 1
    item = payload["data"]["items"][0]
    assert item["status"] == "pending"
    assert item["task_uid"] == "task_001"

    # 新建缺省动作
    created = client.post("/api/platform/fde/attention", json={
        "task_uid": "task_002",
        "stage": "s1",
        "code": "s1_no_identity",
        "severity": "warning",
        "title": "Missing identity",
        "detail": "expert missing",
    })
    assert created.status_code == 200, created.text
    cbody = created.json()
    assert cbody["success"] is True
    rid = cbody["data"]["id"]
    assert isinstance(rid, int)
    assert cbody["data"]["task_uid"] == "task_002"

    detail = cbody["data"]["detail"]
    assert "expert missing" in detail

    # 默认 suggested_actions 应由服务端补齐
    assert "manual_fix_identity" in cbody["data"]["suggested_actions"]

    resolved = client.post(f"/api/platform/fde/attention/{rid}/resolve", json={
        "status": "resolved",
        "resolution": "manual_fix_identity",
        "resolution_note": "已补充 expert_id",
        "resolved_by": "qa",
    })
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["success"] is True
    assert resolved.json()["data"]["status"] == "resolved"
    assert resolved.json()["data"]["resolution"] == "manual_fix_identity"


def test_attention_api_rejects_unknown_status_and_invalid_create():
    _, client = _build_fixture()

    bad = client.post("/api/platform/fde/attention", json={
        "task_uid": "task_invalid",
        "stage": "s1",
        "code": "bad",
        # title missing intentionally
    })
    assert bad.status_code == 400
    bad_json = bad.json()
    assert bad_json["success"] is False

    unresolved = client.post("/api/platform/fde/attention/99999/resolve", json={
        "status": "resolved",
    })
    assert unresolved.status_code == 404
    ubody = unresolved.json()
    assert ubody["success"] is False
