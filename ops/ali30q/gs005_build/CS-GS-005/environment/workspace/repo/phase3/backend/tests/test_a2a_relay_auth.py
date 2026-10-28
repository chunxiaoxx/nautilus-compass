"""A2A relay 认证安全测试 — 治硬编码 AGENT_SECRETS(2026-08-27 转移线⑤升级债①)。

修复前:AGENT_SECRETS 明文 3 个旧 secret + /send 未认证也能发(仅标 ?)。
修复后:全部认证走 APIKey 表(x-api-key 同款),name 与 key 所属 agent 必须一致,
未认证 401,收件人须为注册 agent(或系统名 nautilus)。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Agent, APIKey
import models.agent_survival  # noqa: F401 — mapper dependency(Agent↔AgentSurvival)
from utils.database import get_db
from api.a2a_relay import router as relay_router

# 旧明文 secret(修复后必须失效)
LEGACY_SECRET = "nau_kairos_a2a_secret_2026"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()

    db.add(Agent(agent_id=9000010, owner="0x" + "a" * 40, name="g2b1-executor"))
    db.add(Agent(agent_id=9000003, owner="0x" + "b" * 40, name="kairos"))
    db.add(APIKey(key="nau_test_key_9000010", agent_id=9000010, name="test-key-a", is_active=True))
    db.add(APIKey(key="nau_test_key_9000003", agent_id=9000003, name="test-key-b", is_active=True))
    db.commit()

    app = FastAPI()
    app.include_router(relay_router)

    def override():
        try:
            yield db
        finally:
            pass

    # 测试环境无 redis:mock 掉 relay 的投递后端
    class _FakeRedis:
        def __init__(self):
            self.boxes = {}
        def rpush(self, key, val):
            self.boxes.setdefault(key, []).append(val)
        def lpop(self, key):
            box = self.boxes.get(key, [])
            return box.pop(0) if box else None
        def llen(self, key):
            return len(self.boxes.get(key, []))

    fake = _FakeRedis()
    import utils.redis_client as _rc
    from unittest.mock import patch
    with patch.object(_rc, "get_redis", return_value=fake):
        app.dependency_overrides[get_db] = override
        yield TestClient(app)
    db.close()
    engine.dispose()


def _send(c, **kw):
    return c.post("/api/a2a/send", json={"to": "kairos", "message": "hi"}, **kw)


def test_legacy_hardcoded_secret_rejected(client):
    """旧明文 AGENT_SECRETS 必须不再通过认证。"""
    r = _send(client, headers={"X-Agent-Name": "kairos", "X-Agent-Token": LEGACY_SECRET})
    assert r.status_code == 401


def test_unauthenticated_send_rejected(client):
    """无 header 不再是'标 ? 继续发',必须 401。"""
    r = _send(client)
    assert r.status_code == 401


def test_valid_api_key_and_matching_name_accepted(client):
    headers = {"X-Agent-Name": "g2b1-executor", "X-Agent-Token": "nau_test_key_9000010"}
    r = _send(client, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["verified"] is True
    assert body["from"] == "g2b1-executor"


def test_name_key_mismatch_rejected(client):
    """拿 A 的 key 冒名 B → 401(防冒名)。"""
    headers = {"X-Agent-Name": "kairos", "X-Agent-Token": "nau_test_key_9000010"}
    r = _send(client, headers=headers)
    assert r.status_code == 401


def test_unknown_recipient_rejected(client):
    """收件人须为注册 agent 或系统名,白名单不再硬编码。"""
    headers = {"X-Agent-Name": "g2b1-executor", "X-Agent-Token": "nau_test_key_9000010"}
    r = client.post("/api/a2a/send", json={"to": "ghost-agent", "message": "hi"}, headers=headers)
    assert r.status_code in (400, 404)


def test_new_registered_agent_reachable(client):
    """新注册 agent(9000010)作为收件人可达——relay 不再只认 3 个旧名字。"""
    headers = {"X-Agent-Name": "kairos", "X-Agent-Token": "nau_test_key_9000003"}
    r = client.post("/api/a2a/send", json={"to": "g2b1-executor", "message": "hi"},
                    headers=headers)
    assert r.status_code == 200
    assert r.json()["success"] is True
