"""W-A VIEW 看板 · GET /api/platform/rsi-fde (read-only RSI+FDE control-plane view).

The "可感知" headline surface: one read that answers "is the living system alive?"
— FDE verdicts flowing (external buyer acceptance), agents present (by survival
status), and platform_external_events streaming. Plus a PoI-eligibility summary
DERIVED from passed verdicts (platform-side only · does NOT read compass PoI
internals · G-turf).

Fail-soft per section (a missing table yields an empty section, never a 500), so
the dashboard renders against whatever subset of tables a given DB has. Mirrors
the soul_activity / platform raw-SQL conventions.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from models.fde_verdict import FdeVerdict  # noqa: F401 · register fde_verdicts table
from utils.database import get_db
from api.platform_rsi_fde import router as rsi_fde_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # agents · the ORM model may already be registered on Base · drop + recreate
        # a minimal shape with only the columns the view reads.
        conn.execute(text("DROP TABLE IF EXISTS agents"))
        conn.execute(text(
            "CREATE TABLE agents (id INTEGER PRIMARY KEY, agent_status TEXT, "
            "last_heartbeat TIMESTAMP)"
        ))
        for sid, st in enumerate(
            ["alive", "alive", "active", "inactive", "dead", "archived", "suspended"]
        ):
            conn.execute(text(
                "INSERT INTO agents (id, agent_status, last_heartbeat) VALUES (:i,:s,NULL)"
            ), {"i": sid + 1, "s": st})
        # platform_external_events · raw table (not an ORM model).
        conn.execute(text(
            "CREATE TABLE platform_external_events (id INTEGER PRIMARY KEY, target TEXT, "
            "event_type TEXT, processed_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.execute(text(
            "INSERT INTO platform_external_events (target, event_type, processed_at) "
            "VALUES ('compass-dialog','bounty_completed',CURRENT_TIMESTAMP),"
            "('compass-dialog','marketing_published',CURRENT_TIMESTAMP),"
            "('compass-dialog','bounty_completed',NULL)"
        ))
        # fde_verdicts · one pass + one fail (real source tag is 'fde-capsule-v5').
        conn.execute(text(
            "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, created_at) "
            "VALUES ('fde-data_001-x','data_001','fde-capsule-v5',1,0,1.0,'[]','{}',CURRENT_TIMESTAMP),"
            "('fde-data_003-y','data_003','fde-capsule-v5',0,1,0.5,'[]','{}',CURRENT_TIMESTAMP)"
        ))
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(rsi_fde_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_rsi_fde_view_has_all_sections(client):
    r = client.get("/api/platform/rsi-fde")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert set(d.keys()) >= {"verdicts", "flywheel", "fde_business", "agents", "events", "poi", "generated_at"}


def test_verdicts_section_summary_and_recent(client):
    d = client.get("/api/platform/rsi-fde").json()["data"]
    v = d["verdicts"]
    assert v["summary"]["total"] == 2
    assert v["summary"]["passed"] == 1
    assert v["summary"]["pass_rate"] == 0.5
    assert any(x["task_uid"] == "data_001" and x["overall_pass"] is True for x in v["recent"])
    assert any(x["source"] == "fde-capsule-v5" for x in v["recent"])


def test_agents_section_active_and_distribution(client):
    d = client.get("/api/platform/rsi-fde").json()["data"]
    a = d["agents"]
    assert a["total"] == 7
    # active = agent_status IN ('alive','active') → 2 alive + 1 active = 3
    assert a["active"] == 3
    dist = {x["status"]: x["count"] for x in a["by_status"]}
    assert dist["alive"] == 2 and dist["dead"] == 1


def test_events_section_summary_and_recent(client):
    d = client.get("/api/platform/rsi-fde").json()["data"]
    e = d["events"]
    assert e["summary"]["total"] == 3
    assert e["summary"]["processed"] == 2
    assert any(x["event_type"] == "bounty_completed" for x in e["recent"])
    by_type = {x["event_type"]: x["count"] for x in e["by_type"]}
    assert by_type["bounty_completed"] == 2


def test_poi_summary_derived_from_passed_verdicts(client):
    """PoI-eligible = passed verdicts (platform-side derivation · not compass internals)."""
    d = client.get("/api/platform/rsi-fde").json()["data"]
    p = d["poi"]
    assert p["poi_eligible"] == 1  # only data_001 passed
    assert "data_001" in p["eligible_tasks"]


def test_view_is_failsoft_with_no_tables():
    """No fde_verdicts/agents/events tables → empty sections, still 200 (never 500)."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # deliberately do NOT create any tables
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(rsi_fde_router)
    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app)
    r = c.get("/api/platform/rsi-fde")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["verdicts"]["summary"]["total"] == 0
    assert d["agents"]["total"] == 0
    assert d["events"]["summary"]["total"] == 0


def test_dashboard_html_renders(client):
    r = client.get("/api/platform/rsi-fde/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text
    # the page must self-fetch the JSON view and have the three headline panels.
    assert "/api/platform/rsi-fde" in body
    assert "FDE" in body and ("Verdict" in body or "verdict" in body)
    # the RSI flywheel track (第3类确定性) must have its own legible panel.
    assert "飞轮" in body


def _client_with_sources(verdicts):
    """A client whose fde_verdicts is seeded with (task_uid, source, pass, score) rows."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for i, (tu, src, ok, sc) in enumerate(verdicts):
            conn.execute(text(
                "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, created_at) "
                "VALUES (:vid,:tu,:src,:ok,0,:sc,'[]','{}',CURRENT_TIMESTAMP)"),
                {"vid": f"v{i}", "tu": tu, "src": src, "ok": 1 if ok else 0, "sc": sc})
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(rsi_fde_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_flywheel_section_isolates_deterministic_rsi_track():
    """第3类确定性 RSI track (source=compass/bench_eval) 单列, 与第1/2类 soul QC 区分."""
    c = _client_with_sources([
        ("compass_exp_c2d_001", "compass/bench_eval", True, 1.0),   # RSI 确定性·过
        ("compass_exp_c3_002", "compass/bench_eval", False, 0.0),   # RSI 确定性·未过
        ("expert_t2_x", "soul", True, 1.0),                          # 第2类 QC
    ])
    d = c.get("/api/platform/rsi-fde").json()["data"]
    assert "flywheel" in d
    det = d["flywheel"]["deterministic"]
    assert det["total"] == 2 and det["passed"] == 1
    assert any(x["task_uid"] == "compass_exp_c2d_001" for x in det["recent"])
    by_source = {x["source"]: x for x in d["flywheel"]["by_source"]}
    assert by_source["compass/bench_eval"]["total"] == 2
    assert by_source["soul"]["total"] == 1


def test_fde_business_section_isolates_human_authored_loop():
    """FDE 人工业务环(source=soul/feishu-expert)单列, 与飞轮自动轨(机器判)区分."""
    c = _client_with_sources([
        ("expert_line2_persona_drift", "soul", True, 1.0),          # 第2类教案·人工QC过
        ("expert_t1_x", "feishu-expert", True, 0.9),                 # 第1类题·人工QC过
        ("expert_t2_fail", "soul", False, 0.3),                      # 人工QC打回
        ("compass_exp_c2d_001", "compass/bench_eval", True, 1.0),    # 飞轮自动轨·排除
    ])
    d = c.get("/api/platform/rsi-fde").json()["data"]
    assert "fde_business" in d
    fb = d["fde_business"]
    assert fb["total"] == 3 and fb["passed"] == 2                    # 3 人工·2 过(不含飞轮)
    uids = {x["task_uid"] for x in fb["recent"]}
    assert "expert_line2_persona_drift" in uids
    assert "compass_exp_c2d_001" not in uids                         # 飞轮不入人工环


def test_fde_business_section_excludes_test_uids():
    """my_test_*/test_* 残留不污染甲方可见的业务环卡."""
    c = _client_with_sources([
        ("expert_line2_real", "soul", True, 1.0),
        ("my_test_001", "soul", False, 0.6),                         # 测试残留·排除
        ("test_seed_x", "soul", True, 1.0),                          # 测试残留·排除
    ])
    fb = c.get("/api/platform/rsi-fde").json()["data"]["fde_business"]
    assert fb["total"] == 1 and fb["passed"] == 1
    uids = {x["task_uid"] for x in fb["recent"]}
    assert uids == {"expert_line2_real"}
