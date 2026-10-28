"""control_plane_actions · admin 控制层 TDD.

admin-email 白名单门控的后端 admin 控制模块。复用 platform_dispatch._ROUTES 做路由。

自建 app + include router + override get_db(sqlite StaticPool) + override
get_current_user(伪 user)。不 import main(本地不可 import)。参考 test_control_plane.py
的 fixture 模式。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_verdict import FdeVerdict  # noqa: F401
from models.fde_rsi_delta import FdeRsiDelta  # noqa: F401
from utils.database import get_db
from utils.auth import get_current_user
from api.control_plane_actions import router as actions_router


# --- fake user objects (auth override 返回的对象,只需 .email/.username) ---
class _FakeUser:
    def __init__(self, email: str = "", username: str = ""):
        self.email = email
        self.username = username


def _make_client(user: _FakeUser, engine=None):
    if engine is None:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(actions_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), engine


@pytest.fixture(autouse=True)
def _allowlist(monkeypatch):
    monkeypatch.setenv("CONTROL_ADMIN_EMAILS", "boss@x.com")
    # re-read after each test does not persist; module reads env per-call.
    yield


# ============ 1. require_admin + whoami ============

def test_whoami_admin_true():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.get("/api/platform/control-plane/whoami")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["data"]["is_admin"] is True
    assert body["error"] is None


def test_whoami_non_admin_false():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.get("/api/platform/control-plane/whoami")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["data"]["is_admin"] is False


def test_is_admin_user_fail_closed_when_allowlist_empty(monkeypatch):
    from api.control_plane_actions import is_admin_user
    monkeypatch.setenv("CONTROL_ADMIN_EMAILS", "")
    assert is_admin_user(_FakeUser(email="boss@x.com", username="boss")) is False


def test_is_admin_user_matches_username(monkeypatch):
    from api.control_plane_actions import is_admin_user
    monkeypatch.setenv("CONTROL_ADMIN_EMAILS", "boss")
    assert is_admin_user(_FakeUser(email="x@x.com", username="BOSS")) is True


# ============ 2. POST /dispatch ============

def test_dispatch_admin_ok():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/dispatch",
                    json={"target": "soul", "action": "ping"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    d = body["data"]
    assert d["target"] == "soul"
    assert d["action"] == "ping"
    assert "routed_to" in d
    assert "delivered" in d
    assert "detail" in d


def test_dispatch_non_admin_403():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.post("/api/platform/control-plane/dispatch",
                    json={"target": "soul", "action": "ping"})
    assert r.status_code == 403, r.text


def test_dispatch_unknown_target_400():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/dispatch",
                    json={"target": "nope", "action": "ping"})
    assert r.status_code == 400, r.text


def test_dispatch_missing_action_400():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/dispatch",
                    json={"target": "soul"})
    assert r.status_code == 400, r.text


# ============ 3. POST /goal ============

def test_goal_admin_ok():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/goal",
                    json={"goal": "ship the thing"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    d = body["data"]
    assert d["target"] == "soul"
    assert d["action"] == "dispatch_goal"


def test_goal_non_admin_403():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.post("/api/platform/control-plane/goal",
                    json={"goal": "x"})
    assert r.status_code == 403, r.text


# ============ 4. drill-down GET ============

def _seed_verdict(engine):
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        v = FdeVerdict(
            verdict_id="v-001",
            task_uid="data_001",
            source="soul",
            overall_pass=False,
            veto_failed=True,
            score=0.5,
            items=[{"id": "c1", "pass": False, "veto": True, "reason": "x"}],
        )
        db.add(v)
        db.commit()
    finally:
        db.close()


def test_verdict_drill_down_returns_reason():
    client, engine = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    _seed_verdict(engine)
    r = client.get("/api/platform/control-plane/verdict/v-001")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert items[0]["reason"] == "x"


def test_verdict_drill_down_404():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.get("/api/platform/control-plane/verdict/nope")
    assert r.status_code == 404, r.text


def test_verdict_drill_down_non_admin_403():
    client, engine = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    _seed_verdict(engine)
    r = client.get("/api/platform/control-plane/verdict/v-001")
    assert r.status_code == 403, r.text


def _seed_agent(engine):
    from models.database import Agent
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        a = Agent(id=42, agent_id=42, owner="0x" + "a" * 40, name="Test Agent")
        db.add(a)
        db.commit()
    finally:
        db.close()


def test_agent_drill_down_returns_fields():
    client, engine = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    _seed_agent(engine)
    r = client.get("/api/platform/control-plane/agent/42")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["data"]["id"] == 42
    assert body["data"]["name"] == "Test Agent"


def test_agent_drill_down_404():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.get("/api/platform/control-plane/agent/9999")
    assert r.status_code == 404, r.text


# ============ 5. GET /governance/proposals (admin 读治理提案) ============

def test_governance_proposals_admin_ok():
    """admin 调 → 200 · 统一返回 · fail-soft(sqlite 缺 pg-only 表/列 → 空 data 不 500)。"""
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.get("/api/platform/control-plane/governance/proposals")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["error"] is None
    # data 是 dict(parliament summary 或 fail-soft 占位),路由层成功即可。
    assert isinstance(body["data"], dict)


def test_governance_proposals_non_admin_403():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.get("/api/platform/control-plane/governance/proposals")
    assert r.status_code == 403, r.text


# ============ 6. POST /governance/review (admin 审查/投票提案) ============

def test_governance_review_admin_ok():
    """admin 提交 review → 200 · 转发 in-process · 下游 sqlite 缺表 fail-soft 仍 routed。"""
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/governance/review",
                    json={"proposal_id": "p-001", "decision": "approve"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    d = body["data"]
    assert d["proposal_id"] == "p-001"
    assert d["decision"] == "approve"
    assert "delivered" in d
    assert "detail" in d


def test_governance_review_reject_decision_ok():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/governance/review",
                    json={"proposal_id": "p-002", "decision": "reject"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["decision"] == "reject"


def test_governance_review_non_admin_403():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.post("/api/platform/control-plane/governance/review",
                    json={"proposal_id": "p-001", "decision": "approve"})
    assert r.status_code == 403, r.text


def test_governance_review_missing_proposal_id_400():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/governance/review",
                    json={"decision": "approve"})
    assert r.status_code == 400, r.text


def test_governance_review_bad_decision_400():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/governance/review",
                    json={"proposal_id": "p-001", "decision": "maybe"})
    assert r.status_code == 400, r.text


# ============ 7. POST /agent/{agent_id}/autonomy (admin 调自治级别) ============

def test_agent_autonomy_admin_ok():
    """admin 设 autonomy → 200 · in-process 改 Agent.autonomy_enabled · 审计。"""
    client, engine = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    _seed_agent(engine)
    r = client.post("/api/platform/control-plane/agent/42/autonomy",
                    json={"enabled": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    d = body["data"]
    assert d["agent_id"] == 42
    assert d["autonomy_enabled"] is True


def test_agent_autonomy_disable_ok():
    client, engine = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    _seed_agent(engine)
    r = client.post("/api/platform/control-plane/agent/42/autonomy",
                    json={"enabled": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["autonomy_enabled"] is False


def test_agent_autonomy_404_when_missing():
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/agent/9999/autonomy",
                    json={"enabled": True})
    assert r.status_code == 404, r.text


def test_agent_autonomy_non_admin_403():
    client, engine = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    _seed_agent(engine)
    r = client.post("/api/platform/control-plane/agent/42/autonomy",
                    json={"enabled": True})
    assert r.status_code == 403, r.text


# ============ 8. POST /task/{task_id}/execute (admin 触发执行) ============

def test_task_execute_admin_routed():
    """admin 触发 execute → 200 · self-POST 转发(测试沙箱下游不可达 → delivered=false fail-soft)。"""
    client, _ = _make_client(_FakeUser(email="boss@x.com", username="boss"))
    r = client.post("/api/platform/control-plane/task/7/execute", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    d = body["data"]
    assert d["task_id"] == 7
    assert "delivered" in d
    assert "detail" in d


def test_task_execute_non_admin_403():
    client, _ = _make_client(_FakeUser(email="nobody@y.com", username="nobody"))
    r = client.post("/api/platform/control-plane/task/7/execute", json={})
    assert r.status_code == 403, r.text
