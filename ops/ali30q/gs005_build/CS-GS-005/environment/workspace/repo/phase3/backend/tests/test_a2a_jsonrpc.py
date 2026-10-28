"""A2A JSON-RPC 绑定 v0 测试 — Google A2A v1.0.0 最小协议面(2026-09-12 对齐开工)。

范围(诚实声明,AgentCard 同步):
- tasks/get:平台任务状态 → A2A 状态机映射(pending→submitted 等 5 态)
- message/send:文本投递 nautilus 系统收件箱(异步,回 agent Message)
未实现方法(tasks/cancel/streaming/push)→ -32601。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Agent, APIKey, AcademicTask
import models.agent_survival  # noqa: F401 — mapper dependency(Agent↔AgentSurvival)
from utils.database import get_db
from api.a2a_jsonrpc import router as jsonrpc_router

AUTH = {"X-API-Key": "nau_test_key_9000010"}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    db.add(Agent(agent_id=9000010, owner="0x" + "a" * 40, name="g2b1-executor"))
    db.add(APIKey(key="nau_test_key_9000010", agent_id=9000010, name="k-a", is_active=True))
    db.add(AcademicTask(task_id="t-pend", title="p", description="d", task_type="code",
                        status="pending"))
    db.add(AcademicTask(task_id="t-work", title="p", description="d", task_type="code",
                        status="in_progress"))
    db.add(AcademicTask(task_id="t-review", title="p", description="d", task_type="code",
                        status="needs_review"))
    db.add(AcademicTask(task_id="t-done", title="p", description="d", task_type="code",
                        status="completed", result_output="patch applied"))
    db.add(AcademicTask(task_id="t-fail", title="p", description="d", task_type="code",
                        status="failed", result_error="boom"))
    db.commit()

    app = FastAPI()
    app.include_router(jsonrpc_router)

    def override():
        try:
            yield db
        finally:
            pass

    # 测试环境无 redis:mock 投递后端(同 test_a2a_relay_auth 模式)
    class _FakeRedis:
        def __init__(self):
            self.boxes = {}

        def rpush(self, key, val):
            self.boxes.setdefault(key, []).append(val)

    fake = _FakeRedis()
    import utils.redis_client as _rc
    from unittest.mock import patch
    with patch.object(_rc, "get_redis", return_value=fake):
        app.dependency_overrides[get_db] = override
        with TestClient(app) as c:
            yield c, db, fake
    db.close()
    engine.dispose()


def _rpc(c, method, params=None, headers=None):
    return c.post("/api/a2a/v1", headers=headers or AUTH,
                  json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})


@pytest.mark.parametrize("task_id,a2a_state", [
    ("t-pend", "submitted"),
    ("t-work", "working"),
    ("t-review", "input-required"),
    ("t-done", "completed"),
    ("t-fail", "failed"),
])
def test_tasks_get_maps_platform_states(client, task_id, a2a_state):
    """平台 5 态 → A2A TaskState 全覆盖映射(needs_review→input-required)。"""
    c, _, _ = client
    r = _rpc(c, "tasks/get", {"id": task_id})
    assert r.status_code == 200
    body = r.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 1
    assert body["result"]["id"] == task_id
    assert body["result"]["status"]["state"] == a2a_state


def test_tasks_get_completed_has_text_artifact(client):
    c, _, _ = client
    r = _rpc(c, "tasks/get", {"id": "t-done"})
    artifacts = r.json()["result"].get("artifacts", [])
    assert artifacts and artifacts[0]["parts"][0]["text"] == "patch applied"


def test_tasks_get_unknown_task_returns_a2a_error(client):
    c, _, _ = client
    r = _rpc(c, "tasks/get", {"id": "no-such-task"})
    assert r.status_code == 200
    err = r.json()["error"]
    assert err["code"] == -32001
    assert "not found" in err["message"].lower()


def test_message_send_delivers_to_system_inbox(client):
    """message/send → nautilus 系统收件箱,信封含 sender 名(与 relay 同格式)。"""
    c, _, fake = client
    r = _rpc(c, "message/send", {"message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "hello nautilus"}],
    }})
    assert r.status_code == 200
    result = r.json()["result"]
    assert result["role"] == "agent"          # A2A 响应以 agent Message 回
    assert result["messageId"]
    assert any("hello nautilus" in e for e in fake.boxes["nautilus:inbox"])
    assert any("g2b1-executor" in e for e in fake.boxes["nautilus:inbox"])


def test_message_send_requires_text(client):
    c, _, fake = client
    r = _rpc(c, "message/send", {"message": {"role": "user", "parts": []}})
    assert r.json()["error"]["code"] == -32602
    assert fake.boxes == {}


def test_unimplemented_method_returns_32601(client):
    """v0 未实现(streaming/list 等)→ 明确 method not found,不静默假成功。
    (tasks/cancel 已于 2026-09-15 Day2 实现,移出未实现样本。)"""
    c, _, _ = client
    for m in ("message/stream", "tasks/list", "tasks/pushNotificationConfig/set"):
        r = _rpc(c, m, {"id": "t-pend"})
        assert r.json()["error"]["code"] == -32601


def test_invalid_jsonrpc_envelope_rejected(client):
    c, _, _ = client
    r = c.post("/api/a2a/v1", headers=AUTH,
               json={"id": 1, "method": "tasks/get"})   # 缺 jsonrpc 字段
    assert r.json()["error"]["code"] == -32600


def test_unauthenticated_rejected(client):
    c, _, _ = client
    r = c.post("/api/a2a/v1",
               json={"jsonrpc": "2.0", "id": 1, "method": "tasks/get", "params": {}})
    assert r.status_code == 401


def test_version_header_echoed(client):
    c, _, _ = client
    r = _rpc(c, "tasks/get", {"id": "t-pend"})
    assert r.headers.get("A2A-Version") == "1.0"


def test_unsupported_version_rejected(client):
    """请求 A2A-Version 非 1.x/0.3 → VersionNotSupportedError,不硬吃。"""
    c, _, _ = client
    r = _rpc(c, "tasks/get", {"id": "t-pend"}, headers={**AUTH, "A2A-Version": "9.9"})
    body = r.json()
    assert body["error"]["code"] < 0
    assert "version" in body["error"]["message"].lower()


# ---- tasks/cancel(2026-09-15 Day2 · 平台已有 cancelled 状态先例,非伪造) ----

def test_tasks_cancel_active_task_succeeds(client):
    """非终态任务 cancel → status='cancelled' + A2A canceled 态返回。"""
    c, _, _ = client
    r = _rpc(c, "tasks/cancel", {"id": "t-pend"})
    assert r.json()["result"]["status"]["state"] == "canceled"
    # 取消后 tasks/get 读回也映射 canceled(cancelled 映射 bug 顺手修)
    r2 = _rpc(c, "tasks/get", {"id": "t-pend"})
    assert r2.json()["result"]["status"]["state"] == "canceled"


def test_tasks_cancel_terminal_task_rejects(client):
    """终态任务 cancel → TaskNotCancelableError(-32011),不静默成功。"""
    c, _, _ = client
    r = _rpc(c, "tasks/cancel", {"id": "t-done"})
    assert r.json()["error"]["code"] == -32011
    # 已取消的再取消 → 同样 -32011(终态)
    _rpc(c, "tasks/cancel", {"id": "t-work"})
    r2 = _rpc(c, "tasks/cancel", {"id": "t-work"})
    assert r2.json()["error"]["code"] == -32011


def test_tasks_cancel_unknown_task(client):
    c, _, _ = client
    r = _rpc(c, "tasks/cancel", {"id": "t-none"})
    assert r.json()["error"]["code"] == -32001


def test_tasks_cancel_requires_id(client):
    c, _, _ = client
    r = _rpc(c, "tasks/cancel", {})
    assert r.json()["error"]["code"] == -32602
