"""verdict-bus 三守卫测试(2026-09-15 · compass 试点首账修复)。

背景:compass 首批复算 10/10 UNVERIFIABLE——①g2-b1-repair-executor 自 8/24 起
450/450 verdict items 空(载荷断供,复算不可用);②external-verify 端点(income
唯一入账门)无鉴权,任何 POST 方换名即可自置 external_verified。

修:ingest 空载荷新行拒收(幂等重放放行)/ external-verify 加 X-API-Key 身份
+verifier_source 必须匹配 agent 注册名 / executor 侧补判据+复算指针 items。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base, Agent, APIKey
import models.agent_survival  # noqa: F401 — mapper dependency
import models.fde_verdict  # noqa: F401
import models.fde_dispatch  # noqa: F401
from utils.database import get_db
from api.fde_verdict import router as verdict_router

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import tools.g2_b1_executor_agent as ex  # noqa: E402


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(verdict_router)
    app.dependency_overrides[get_db] = lambda: TestSession()
    with TestClient(app) as c:
        yield c


def _body(verdict_id="v-g1", items=None):
    return {
        "verdict_id": verdict_id, "task_uid": "t-g1", "source": "g2-b1-repair-executor",
        "overall_pass": True, "score": 1.0,
        **({"items": items} if items is not None else {}),
    }


# ---- 修 2:ingest 空载荷守卫 ----

def test_ingest_rejects_empty_items_new_row(client):
    r = client.post("/api/platform/fde/verdict", json=_body(items=[]))
    assert r.status_code == 400
    assert "non-empty" in r.json()["error"]


def test_ingest_rejects_missing_items_new_row(client):
    r = client.post("/api/platform/fde/verdict", json=_body())  # items 缺省=[]
    assert r.status_code == 400


def test_ingest_allows_empty_items_idempotent_replay(client):
    ok = client.post("/api/platform/fde/verdict", json=_body(items=[
        {"round": 1, "valid": 1, "score": 1.0, "criteria": "g2b1-repair-v1"}]))
    assert ok.status_code == 200
    replay = client.post("/api/platform/fde/verdict", json=_body(items=[]))
    assert replay.status_code == 200
    assert replay.json()["data"]["idempotent"] is True


# ---- 修 3:external-verify 鉴权 ----

def test_external_verify_requires_api_key(client):
    r = client.patch("/api/platform/fde/verdict/v-g1/external-verify",
                     json={"verifier_source": "compass"})
    assert r.status_code == 401


def test_external_verify_key_and_name_match(client, monkeypatch):
    """带 key 但 verifier_source 与注册名不符 → 403;相符 → 过鉴权(业务校验接管)。"""
    session = client.app.dependency_overrides[get_db]()
    session.add(Agent(agent_id=9900099, owner="0x" + "b" * 40, name="compass"))
    session.add(APIKey(key="nau_test_key_compass", agent_id=9900099, name="k",
                       is_active=True))
    session.commit()
    # 名不符
    r = client.patch("/api/platform/fde/verdict/v-g1/external-verify",
                     json={"verifier_source": "someone-else"},
                     headers={"X-API-Key": "nau_test_key_compass"})
    assert r.status_code == 403
    # 名相符但 verdict 不存在 → 404(鉴权已过,进入业务分支)
    r2 = client.patch("/api/platform/fde/verdict/v-g1/external-verify",
                      json={"verifier_source": "compass"},
                      headers={"X-API-Key": "nau_test_key_compass"})
    assert r2.status_code == 404


# ---- 修 1:executor 补 items 载荷 ----

def test_submit_verdict_items_payload_contract():
    evidence = {
        "task": {"task_uid": "g2b1:abc123def456", "repo_path": "nautilus-v5",
                 "reference_fix_commit": "0123456789abcdef"},
        "test_passed": True, "provider": "glm_plan", "provider_used": "glm_plan",
        "total_tokens": 1234, "schema_version": "v9",
    }
    captured = {}

    def fake_post(url, body):
        captured["url"], captured["body"] = url, body
        return type("R", (), {"status_code": 200, "text": "ok"})()

    out = ex.submit_verdict(evidence, backend_base="http://x", poster=fake_post)
    assert out["status"] == 200
    payload = captured["body"]
    items = payload["items"]
    assert items, "items must be non-empty (payload guard)"
    it = items[0]
    assert it["criteria"].startswith("g2b1-repair-v1")
    assert it["repo"] == "nautilus-v5"
    assert it["reference_fix_commit"] == "0123456789abcdef"
    assert it["valid"] == 1 and it["score"] == 1.0
    assert it["provider"] == "glm_plan"
