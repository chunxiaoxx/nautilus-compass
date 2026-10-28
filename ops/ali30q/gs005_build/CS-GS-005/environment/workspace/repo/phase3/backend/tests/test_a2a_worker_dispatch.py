"""A2A worker 派单模式测试 — 升级债②(2026-08-27 · 治"执行器写死 Haiku")。

修复前:claim_and_execute 认领后平台内置 Claude Haiku 替 agent 执行(违反 §0-ARCH
"平台只做派单/聚合/共识,执行归注册 agent")。
修复后:POST /a2a/work = 只认领并返回载荷(不执行);结果由 worker 自己的循环
产出后 POST /a2a/work/{task_id}/result 回报。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Agent, APIKey, AcademicTask
import models.agent_survival  # noqa: F401 — mapper dependency
from utils.database import get_db
from api.a2a import router as a2a_router

WORKER_PARAMS = '{"a2a_role": "worker", "parent": "parent-task-1"}'


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    db.add(Agent(agent_id=9000010, owner="0x" + "a" * 40, name="g2b1-executor"))
    db.add(Agent(agent_id=9000003, owner="0x" + "b" * 40, name="kairos"))
    db.add(APIKey(key="nau_test_key_9000010", agent_id=9000010, name="k-a", is_active=True))
    db.add(APIKey(key="nau_test_key_9000003", agent_id=9000003, name="k-b", is_active=True))
    db.add(AcademicTask(task_id="sub-w1", title="fix bug A", description="repair A",
                        task_type="code", status="pending", parameters=WORKER_PARAMS))
    db.commit()

    app = FastAPI()
    app.include_router(a2a_router)

    def override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c, db
    db.close()
    engine.dispose()


def test_claim_returns_payload_without_executing(client):
    """认领 = 拿到任务载荷,不执行,不含 result。"""
    c, db = client
    r = c.post("/a2a/work", headers={"x-api-key": "nau_test_key_9000010"})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["claimed"] is True
    assert body["task_id"] == "sub-w1"
    assert body["status"] == "in_progress"  # 认领态,非 completed
    assert "payload" in body and body["payload"]["title"] == "fix bug A"
    st = db.query(AcademicTask).filter_by(task_id="sub-w1").first()
    assert st.status == "in_progress"
    assert st.result_output in (None, "")  # 没有平台代执行的结果


def test_submit_result_completes(client):
    c, db = client
    c.post("/a2a/work", headers={"x-api-key": "nau_test_key_9000010"})
    r = c.post("/a2a/work/sub-w1/result", headers={"x-api-key": "nau_test_key_9000010"},
               json={"success": True, "result": "patch applied, tests pass"})
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "completed"
    st = db.query(AcademicTask).filter_by(task_id="sub-w1").first()
    assert st.status == "completed"
    assert st.result_output == "patch applied, tests pass"


def test_submit_failure_marks_failed(client):
    c, db = client
    c.post("/a2a/work", headers={"x-api-key": "nau_test_key_9000010"})
    r = c.post("/a2a/work/sub-w1/result", headers={"x-api-key": "nau_test_key_9000010"},
               json={"success": False, "error": "verifier mismatch"})
    assert r.status_code == 200
    st = db.query(AcademicTask).filter_by(task_id="sub-w1").first()
    assert st.status == "failed"
    assert st.result_error == "verifier mismatch"


def test_other_agent_cannot_submit(client):
    """非认领者不能替别人交卷。"""
    c, _ = client
    c.post("/a2a/work", headers={"x-api-key": "nau_test_key_9000010"})
    r = c.post("/a2a/work/sub-w1/result", headers={"x-api-key": "nau_test_key_9000003"},
               json={"success": True, "result": "hijack"})
    assert r.status_code == 403


def test_claim_requires_api_key(client):
    c, _ = client
    r = c.post("/a2a/work")
    assert r.status_code in (401, 422)
