"""T1-A3 · audit 写入端点测试——治"主脑干活全站第一但 cloud audit 0 行"双库分裂(#779)。

daemon 活性平台直接可观测:POST /api/platform/org/audit(鉴权/必填/截断/服务端 ts+ip)。
事件流语义:不幂等(重试重复调用方自担,注释见端点 docstring)。
"""
from __future__ import annotations

import os

os.environ["ORG_AUTH_GRACE"] = "false"  # 测试走强制鉴权路径(生产 9/21 已关宽限)

from datetime import datetime  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from models.database import Base, APIKey  # noqa: E402
import models.agent_survival  # noqa: F401,E402 — mapper dependency
from api.org import router  # noqa: E402
from utils.database import get_db  # noqa: E402

V5_KEY = "naut_test_org_auth_daemon"  # 绑定 daemon 实名(每 daemon 自己的 key)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    s.add(APIKey(key=V5_KEY, name="org-auth:ag_local_laptop_001", is_active=True, agent_id=9000002))
    s.commit()
    yield s
    s.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _payload(**over):
    p = {"actor": "ag_local_laptop_001", "actor_type": "daemon",
         "action": "task_submit", "target": "28c2", "target_type": "task",
         "outcome": "ok", "input_preview": "in", "output_preview": "out",
         "metadata": {"k": "v"}}
    p.update(over)
    return p


def test_audit_post_ok_writes_row_with_server_ts_ip(db, client):
    r = client.post("/api/platform/org/audit", json=_payload(),
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code == 200, r.text
    row = r.json()["data"]
    assert row["actor"] == "ag_local_laptop_001" and row["action"] == "task_submit"
    assert row["ts"]  # 服务端时钟,非客户端声明
    assert row["ip"] == "testclient"  # 服务端记(TestClient 固定 host)
    from models.platform_audit import PlatformAudit
    saved = db.query(PlatformAudit).filter_by(actor="ag_local_laptop_001").one()
    assert saved.outcome == "ok" and saved.meta == {"k": "v"}


def test_audit_auth_rejected_wrong_or_missing_key(client):
    assert client.post("/api/platform/org/audit", json=_payload()).status_code == 401
    r = client.post("/api/platform/org/audit", json=_payload(),
                    headers={"X-API-Key": "naut_wrong"})
    assert r.status_code == 401


def test_audit_key_must_bind_to_actor(client):
    # key 绑 v5,actor 冒充别人 → 401(防伪造他人活动)
    r = client.post("/api/platform/org/audit", json=_payload(actor="prime-001"),
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code == 401


def test_audit_missing_required_fields(client):
    r = client.post("/api/platform/org/audit", json={"action": "x"},
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code == 400 and "actor" in r.json()["error"]


def test_audit_preview_truncated_and_metadata_coerced(db, client):
    r = client.post("/api/platform/org/audit", json=_payload(
        input_preview="a" * 9999, output_preview="b" * 9999,
        metadata={"arr": [1, 2]}),
        headers={"X-API-Key": V5_KEY})
    assert r.status_code == 200
    from models.platform_audit import PlatformAudit
    saved = db.query(PlatformAudit).one()
    assert len(saved.input_preview) <= 2000 and len(saved.output_preview) <= 2000
    assert saved.meta == {"arr": [1, 2]}


def test_audit_metadata_nondict_rejected(client):
    r = client.post("/api/platform/org/audit", json=_payload(metadata="junk"),
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code in (400, 422)


def test_audit_get_liveness_by_actor(db, client):
    client.post("/api/platform/org/audit", json=_payload(),
                headers={"X-API-Key": V5_KEY})
    r = client.get("/api/platform/org/audit", params={"actor": "ag_local_laptop_001"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] == 1 and data["rows"][0]["action"] == "task_submit"


def test_audit_bad_json_shape_rejected(client):
    r = client.post("/api/platform/org/audit", json=[1, 2, 3],
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code in (400, 422)


def test_client_ip_loopback_takes_nginx_real_ip(client):
    # nginx 反代后端见 127.0.0.1,真源在 X-Real-IP(nginx $remote_addr 覆盖式设置)
    from api.org import _client_ip
    from starlette.requests import Request as SRequest

    def _mk(host, hdr=None):
        scope = {"type": "http", "headers": ([(b"x-real-ip", hdr.encode())] if hdr else []),
                 "client": (host, 123)}
        return SRequest(scope)

    assert _client_ip(_mk("127.0.0.1", "1.2.3.4")) == "1.2.3.4"
    assert _client_ip(_mk("127.0.0.1")) == "127.0.0.1"      # 无头兜底
    assert _client_ip(_mk("9.9.9.9", "1.2.3.4")) == "9.9.9.9"  # 直连不采信可伪造头


def test_audit_defaults_fill_notnull_columns(db, client):
    # 生产表除 preview 外全列 NOT NULL:缺省填充防 500(9/23 NotNullViolation 修正)
    r = client.post("/api/platform/org/audit",
                    json={"actor": "ag_local_laptop_001", "action": "a", "outcome": "ok"},
                    headers={"X-API-Key": V5_KEY})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["actor_type"] == "unspecified" and d["target"] == "" and d["metadata"] == {}
