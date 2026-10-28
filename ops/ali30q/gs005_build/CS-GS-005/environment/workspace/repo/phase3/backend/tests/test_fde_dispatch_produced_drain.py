"""FDE dispatch produced-error-drain · drain stuck `produced` tasks (platform turf).

Root cause (2026-06-21): a `produced` task whose output is malformed (not a clean
unified diff · e.g. JSON-wrapped patch from a daemon produce-format inconsistency)
can NEVER verify — fde_bench_poll returns ok=False → errored → no verdict, not added
to `seen` → re-picked and re-errored EVERY cycle, forever poisoning the verify queue.

The drain moves a `produced` task that is old AND has no verdict to a terminal
status ("abandoned") so the verify poller stops re-picking it. It deliberately does
NOT write a reward-0 verdict (ok=False ≠ legit reward 0 — that would pollute the
ratchet, per fde_bench_poll's contract).

Scope locked: produced (no verdict, stale) → abandoned ONLY. Tasks with a verdict,
or recently reported (verify may be in flight), are left alone.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_dispatch import router as fde_router, reap_stale_produced


@pytest.fixture
def db_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def client(db_factory):
    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(fde_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _seed_produced(db, task_uid, reported_minutes_ago=None):
    row = FdeDispatch(task_uid=task_uid, title="t", description="d", status="produced")
    row.claimed_by = "nautilus-prime-001"
    if reported_minutes_ago is not None:
        row.reported_at = datetime.utcnow() - timedelta(minutes=reported_minutes_ago)
    db.add(row)
    db.commit()


def _add_verdict(db, task_uid):
    db.execute(text(
        "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, external_verified, created_at) "
        "VALUES (:vid, :tu, 'compass/bench_eval', 1, 0, 1.0, '[]', '{}', 0, CURRENT_TIMESTAMP)"),
        {"vid": f"bench|{task_uid}|x", "tu": task_uid})
    db.commit()


# --- #948 (2026-09-24 jumpc): deferred 补件窗 hold ---
# 约定:判分方的非终态 deferred 写 fde_verdicts,source='deferred'
# (overall_pass/score 无语义,消费者一律按 source 过滤,防 0 分污染 ratchet)。

def _add_verdict_at(db, task_uid, source, hours_ago, suffix="x"):
    db.execute(text(
        "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, external_verified, created_at) "
        "VALUES (:vid, :tu, :src, 0, 0, 0.0, '[]', '{}', 0, :ts)"),
        {"vid": f"{source}|{task_uid}|{suffix}", "tu": task_uid, "src": source,
         "ts": datetime.utcnow() - timedelta(hours=hours_ago)})
    db.commit()


def test_drain_holds_deferred_within_window(db_factory):
    """deferred(source='deferred')在补件窗内 → produced 不被 30min 短窗扫死。"""
    db = db_factory()
    _seed_produced(db, "jumpc_hold", reported_minutes_ago=120)
    _add_verdict_at(db, "jumpc_hold", "deferred", hours_ago=1)
    drained = reap_stale_produced(db, timeout_seconds=1800)
    assert drained == []
    assert db.query(FdeDispatch).filter_by(task_uid="jumpc_hold").first().status == "produced"


def test_drain_drains_deferred_hold_lapsed(db_factory):
    """补件窗走完零补件 → 如实 abandoned(窗以最近一条 deferred 起算)。"""
    db = db_factory()
    _seed_produced(db, "jumpc_lapsed", reported_minutes_ago=9999)
    _add_verdict_at(db, "jumpc_lapsed", "deferred", hours_ago=73)  # > 48h 默认窗
    drained = reap_stale_produced(db, timeout_seconds=1800)
    assert drained == ["jumpc_lapsed"]
    assert db.query(FdeDispatch).filter_by(task_uid="jumpc_lapsed").first().status == "abandoned"


def test_drain_deferred_hold_param_override(db_factory):
    """deferred_hold_seconds 可调(白名单 W3 参数类)。"""
    db = db_factory()
    _seed_produced(db, "jumpc_param", reported_minutes_ago=9999)
    _add_verdict_at(db, "jumpc_param", "deferred", hours_ago=2)
    drained = reap_stale_produced(db, timeout_seconds=1800, deferred_hold_seconds=3600)
    assert drained == ["jumpc_param"]


def test_drain_terminal_verdict_after_deferred_still_exempt(db_factory):
    """round2 终态 verdict 落在 deferred 之后 → 豁免(走 settled 路径,不看旧 deferred)。"""
    db = db_factory()
    _seed_produced(db, "jumpc_round2", reported_minutes_ago=9999)
    _add_verdict_at(db, "jumpc_round2", "deferred", hours_ago=3)
    _add_verdict_at(db, "jumpc_round2", "compass/bench_eval", hours_ago=0, suffix="r2")
    drained = reap_stale_produced(db, timeout_seconds=1800, deferred_hold_seconds=3600)
    assert drained == []
    assert db.query(FdeDispatch).filter_by(task_uid="jumpc_round2").first().status == "produced"


def test_drain_stale_produced_without_verdict(db_factory):
    db = db_factory()
    _seed_produced(db, "stuck_001", reported_minutes_ago=120)
    drained = reap_stale_produced(db, timeout_seconds=1800)  # 30 min
    assert drained == ["stuck_001"]
    row = db.query(FdeDispatch).filter_by(task_uid="stuck_001").first()
    assert row.status == "abandoned"


def test_drain_leaves_fresh_produced(db_factory):
    db = db_factory()
    _seed_produced(db, "fresh_001", reported_minutes_ago=2)
    drained = reap_stale_produced(db, timeout_seconds=1800)
    assert drained == []
    assert db.query(FdeDispatch).filter_by(task_uid="fresh_001").first().status == "produced"


def test_drain_leaves_produced_with_verdict(db_factory):
    """A produced task that DID verify (has a verdict) must not be drained."""
    db = db_factory()
    _seed_produced(db, "verified_001", reported_minutes_ago=120)
    _add_verdict(db, "verified_001")
    drained = reap_stale_produced(db, timeout_seconds=1800)
    assert drained == []
    assert db.query(FdeDispatch).filter_by(task_uid="verified_001").first().status == "produced"


def test_drain_ignores_open_claimed_settled(db_factory):
    db = db_factory()
    for uid, st in [("o", "open"), ("c", "claimed"), ("s", "settled")]:
        row = FdeDispatch(task_uid=uid, title="t", description="d", status=st)
        row.reported_at = datetime.utcnow() - timedelta(minutes=999)
        db.add(row)
    db.commit()
    drained = reap_stale_produced(db, timeout_seconds=60)
    assert drained == []


def test_drain_null_reported_at_is_stale(db_factory):
    db = db_factory()
    row = FdeDispatch(task_uid="legacy_001", title="t", description="d", status="produced")
    row.reported_at = None
    db.add(row)
    db.commit()
    drained = reap_stale_produced(db, timeout_seconds=60)
    assert drained == ["legacy_001"]
    assert db.query(FdeDispatch).filter_by(task_uid="legacy_001").first().status == "abandoned"


def test_drain_does_not_write_verdict(db_factory):
    """Drain must NOT fabricate a reward-0 verdict (ok=False != legit reward 0)."""
    db = db_factory()
    _seed_produced(db, "stuck_002", reported_minutes_ago=120)
    reap_stale_produced(db, timeout_seconds=1800)
    cnt = db.execute(text("SELECT COUNT(*) FROM fde_verdicts WHERE task_uid='stuck_002'")).fetchone()[0]
    assert cnt == 0


def test_drain_endpoint(client, db_factory):
    db = db_factory()
    _seed_produced(db, "stuck_ep", reported_minutes_ago=120)
    db.close()
    r = client.post("/api/platform/fde/drain", json={"timeout_seconds": 1800})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["drained"] == ["stuck_ep"]
    assert data["count"] == 1
    # drained task no longer appears as produced
    produced = client.get("/api/platform/fde/tasks", params={"status": "produced"}).json()["data"]["tasks"]
    assert not any(t["task_uid"] == "stuck_ep" for t in produced)
