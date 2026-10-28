"""Org mailbox P0 · 离线测试(sqlite 内存,不碰生产 DB)。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from models.database import Base  # noqa: E402
import models.org_mailbox as _m  # noqa: F401,E402  (register table)
import models.agent_survival as _s  # noqa: F401,E402  (Agent relationship chain needs AgentSurvival)
from api.org import router  # noqa: E402


def _client():
    engine = create_engine("sqlite://",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    from models.database import APIKey
    Base.metadata.create_all(engine, tables=[_m.OrgMailbox.__table__, APIKey.__table__])
    session = sessionmaker(bind=engine)()

    from fastapi import Depends, FastAPI
    app = FastAPI()
    app.include_router(router)

    def _get_db():
        yield session

    app.dependency_overrides[__import__("utils.database", fromlist=["get_db"]).get_db] = _get_db
    return TestClient(app), session


def _mail(**over):
    base = {"from_agent": "platform", "to_agent": "v5", "trace_id": "t-1",
            "title": "三台阶回函", "body": "deadline 明晚",
            "deadline": (datetime.utcnow() + timedelta(days=1)).isoformat()}
    base.update(over)
    return base


def test_post_get_ack_roundtrip():
    c, _ = _client()
    r = c.post("/api/platform/org/mailbox", json=_mail())
    assert r.status_code == 200 and r.json()["success"]
    mid = r.json()["data"]["id"]

    r = c.get("/api/platform/org/mailbox", params={"to": "v5"})
    assert len(r.json()["data"]) == 1
    assert r.json()["data"][0]["title"] == "三台阶回函"

    r = c.post(f"/api/platform/org/mailbox/{mid}/ack", json={"note": "已认领台阶一"})
    assert r.json()["data"]["ack_at"] is not None

    r = c.get("/api/platform/org/mailbox", params={"to": "v5"})
    assert r.json()["data"] == []  # 默认 unread=1,ack 后消失


def test_post_duplicate_trace_returns_409():
    """9/17 假绿修复(compass 349):重复 (to,trace) 显式 409+existing_id,不再静默旧函。"""
    c, _ = _client()
    r1 = c.post("/api/platform/org/mailbox", json=_mail())
    assert r1.status_code == 200
    r2 = c.post("/api/platform/org/mailbox", json=_mail())
    assert r2.status_code == 409
    assert r2.json()["data"]["existing_id"] == r1.json()["data"]["id"]
    rows = c.get("/api/platform/org/mailbox", params={"to": "v5", "unread": False}).json()["data"]
    assert len(rows) == 1


def test_post_rejects_missing_and_bad_deadline():
    c, _ = _client()
    r = c.post("/api/platform/org/mailbox", json={k: v for k, v in _mail().items()
                                                  if k != "deadline"})
    assert r.status_code == 400 and "deadline" in r.json()["error"]
    r = c.post("/api/platform/org/mailbox", json=_mail(deadline="whenever"))
    assert r.status_code == 400


def test_ack_idempotent_and_404():
    c, _ = _client()
    mid = c.post("/api/platform/org/mailbox", json=_mail()).json()["data"]["id"]
    c.post(f"/api/platform/org/mailbox/{mid}/ack", json={"note": "ok"})
    r = c.post(f"/api/platform/org/mailbox/{mid}/ack")
    assert r.json()["data"]["idempotent"] is True
    assert c.post("/api/platform/org/mailbox/999/ack").status_code == 404


# --- P1 bootstrap 聚合端点 ---
def test_bootstrap_returns_seven_sections():
    c, s = _client()
    from models.database import Base
    import models.database as mdb
    import models.org_mailbox as om  # noqa: F401(测试内引用)
    # agents 表也建,塞一行
    eng = s.get_bind()
    Base.metadata.create_all(eng, tables=[mdb.Agent.__table__])
    from datetime import datetime
    s.add(mdb.Agent(agent_id=9000010, owner="0x" + "a" * 40,
                    name="nautilus-repair-executor-001",
                    reputation=100, total_earnings=0))
    s.add(om.OrgMailbox(id=99, from_agent="platform", to_agent="9000010", trace_id="t-b",
                        title="bt", body="", deadline=datetime.utcnow()))
    s.commit()
    r = c.get("/api/platform/org/bootstrap", params={"agent": "9000010"})
    d = r.json()["data"]
    for sec in ("identity", "state", "mailbox", "contracts", "goals", "memory",
                "capability_index", "health"):
        assert sec in d, sec
    assert d["mailbox"]["due_12h"] == 1
    assert d["identity"]["agent_id"] == 9000010
    assert isinstance(d["state"].get("sha1"), str)


# --- 任务端点(§⓪-E 派单五件套:类型/验收判据/交付格式/SLA/消费者) ---
def _task(**over):
    base = {"from_agent": "platform", "to_agent": "compass",
            "trace_id": "task-c2-20260901", "title": "[C2] 函件对账",
            "body": "对账 mailbox DB vs loop_state.json",
            "deadline": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "task_type": "C2",
            "acceptance": "diff 清单逐条可复核,漏判=0",
            "deliverable_format": "md 清单投 mailbox 回函",
            "consumer": "platform-loop 日报 + 台账"}
    base.update(over)
    return base


def test_task_post_requires_five_fields():
    c, _ = _client()
    for missing in ("task_type", "acceptance", "deliverable_format", "consumer"):
        body = {k: v for k, v in _task().items() if k != missing}
        r = c.post("/api/platform/org/task", json=body)
        assert r.status_code == 400 and missing in r.json()["error"], missing


def test_task_post_stores_meta_and_renders_body():
    c, _ = _client()
    r = c.post("/api/platform/org/task", json=_task())
    assert r.status_code == 200 and r.json()["success"]
    d = r.json()["data"]
    assert d["task_meta"]["task_type"] == "C2"
    assert d["task_meta"]["consumer"] == "platform-loop 日报 + 台账"
    # 验收判据渲染进 body(读函即见,不依赖 JSON 列)
    assert "C2" in d["body"] and "diff 清单逐条可复核" in d["body"]


def test_task_post_duplicate_returns_409():
    c, _ = _client()
    assert c.post("/api/platform/org/task", json=_task()).status_code == 200
    assert c.post("/api/platform/org/task", json=_task()).status_code == 409


def test_task_list_returns_only_tasks():
    c, _ = _client()
    c.post("/api/platform/org/mailbox", json=_mail())  # 普通函不进任务清单
    c.post("/api/platform/org/task", json=_task())
    rows = c.get("/api/platform/org/tasks").json()["data"]
    assert len(rows) == 1 and rows[0]["task_meta"]["task_type"] == "C2"


# --- 服务端 created_at 兜底(9/16:外部回函 created_at=None 缺口,审计时间线断) ---
def test_post_mail_fills_created_at_server_side():
    c, s = _client()
    r = c.post("/api/platform/org/mailbox", json=_mail())
    assert r.status_code == 200
    row = s.query(_m.OrgMailbox).filter_by(trace_id="t-1").first()
    assert row.created_at is not None  # 不依赖投函方填写


def test_post_task_fills_created_at_server_side():
    c, s = _client()
    r = c.post("/api/platform/org/task", json=_task())
    assert r.status_code == 200
    row = s.query(_m.OrgMailbox).filter_by(trace_id="task-c2-20260901").first()
    assert row.created_at is not None


# --- X-API-Key 投函鉴权(9/17 上线,预告函 306-309) ---
def _mk_key(s, name="org-auth:v5", key="test-key-v5-0001"):
    from models.database import APIKey
    s.add(APIKey(key=key, agent_id=9000017, name=name, is_active=True))
    s.commit()


def test_auth_grace_allows_without_key(monkeypatch):
    monkeypatch.delenv("ORG_AUTH_GRACE", raising=False)  # 缺省=true 宽限
    c, _ = _client()
    r = c.post("/api/platform/org/mailbox", json=_mail(from_agent="v5", trace_id="auth-1"))
    assert r.status_code == 200


def test_auth_valid_key_matching_from_passes():
    c, s = _client()
    _mk_key(s)
    r = c.post("/api/platform/org/mailbox", json=_mail(from_agent="v5", trace_id="auth-2"),
               headers={"X-API-Key": "test-key-v5-0001"})
    assert r.status_code == 200


def test_auth_key_from_mismatch_rejected_401():
    c, s = _client()
    _mk_key(s)
    r = c.post("/api/platform/org/mailbox", json=_mail(from_agent="flywheel", trace_id="auth-3"),
               headers={"X-API-Key": "test-key-v5-0001"})
    assert r.status_code == 401 and "bound to 'v5'" in r.json()["error"]


def test_auth_grace_off_missing_key_rejected(monkeypatch):
    monkeypatch.setenv("ORG_AUTH_GRACE", "false")
    c, _ = _client()
    r = c.post("/api/platform/org/mailbox", json=_mail(from_agent="v5", trace_id="auth-4"))
    assert r.status_code == 401 and "grace period ended" in r.json()["error"]


def test_auth_invalid_key_rejected_even_in_grace():
    c, _ = _client()
    r = c.post("/api/platform/org/mailbox", json=_mail(from_agent="v5", trace_id="auth-5"),
               headers={"X-API-Key": "totally-wrong"})
    assert r.status_code == 401 and "invalid" in r.json()["error"]
