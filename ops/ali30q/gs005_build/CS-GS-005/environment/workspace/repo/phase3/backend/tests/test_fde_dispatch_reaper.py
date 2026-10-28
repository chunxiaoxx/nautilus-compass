"""FDE dispatch claimed-timeout reaper · stale-claim reclamation (platform turf).

Root-cause fix for the V5 daemon split-brain orphan failure mode (2026-06-20): a
daemon that claims an open task then dies / serves stale code never reports →
the task stays `claimed` forever → the flywheel空转 (no other healthy agent can
re-claim it). The reaper returns a `claimed` task to `open` once its `claimed_at`
exceeds a timeout, so a healthy daemon can pick it up again.

Scope locked: claimed → (timeout) → open ONLY. produced / settled untouched.
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
import models.agent_survival  # noqa: F401 · register relationship target
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_dispatch import router as fde_router, reap_stale_claims


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


def _seed(db, task_uid, status, claimed_minutes_ago=None):
    row = FdeDispatch(task_uid=task_uid, title="t", description="d", status=status)
    if claimed_minutes_ago is not None:
        row.claimed_by = "nautilus-prime-001"
        row.claimed_at = datetime.utcnow() - timedelta(minutes=claimed_minutes_ago)
    db.add(row)
    db.commit()


# ---- reap_stale_claims() pure function ----

def test_reaper_reclaims_stale_claimed(db_factory):
    db = db_factory()
    _seed(db, "stale_001", "claimed", claimed_minutes_ago=60)
    reclaimed = reap_stale_claims(db, timeout_seconds=1800)  # 30 min
    assert reclaimed == ["stale_001"]
    row = db.query(FdeDispatch).filter_by(task_uid="stale_001").first()
    assert row.status == "open"
    assert row.claimed_by is None
    assert row.claimed_at is None


def test_reaper_leaves_fresh_claims(db_factory):
    db = db_factory()
    _seed(db, "fresh_001", "claimed", claimed_minutes_ago=2)
    reclaimed = reap_stale_claims(db, timeout_seconds=1800)
    assert reclaimed == []
    row = db.query(FdeDispatch).filter_by(task_uid="fresh_001").first()
    assert row.status == "claimed"
    assert row.claimed_by == "nautilus-prime-001"


def test_reaper_ignores_open_produced_settled(db_factory):
    db = db_factory()
    _seed(db, "open_x", "open")
    _seed(db, "produced_x", "produced", claimed_minutes_ago=999)
    _seed(db, "settled_x", "settled", claimed_minutes_ago=999)
    reclaimed = reap_stale_claims(db, timeout_seconds=60)
    assert reclaimed == []
    assert db.query(FdeDispatch).filter_by(task_uid="produced_x").first().status == "produced"
    assert db.query(FdeDispatch).filter_by(task_uid="settled_x").first().status == "settled"


def test_reaper_handles_null_claimed_at_safely(db_factory):
    """A claimed row with no claimed_at (legacy) must not crash the reaper."""
    db = db_factory()
    row = FdeDispatch(task_uid="legacy_001", title="t", description="d", status="claimed")
    row.claimed_by = "a1"
    row.claimed_at = None
    db.add(row)
    db.commit()
    reclaimed = reap_stale_claims(db, timeout_seconds=60)
    # null claimed_at → treat as stale (unknown age, safe to reclaim)
    assert reclaimed == ["legacy_001"]
    assert db.query(FdeDispatch).filter_by(task_uid="legacy_001").first().status == "open"


def test_reaper_reclaims_multiple_and_orders(db_factory):
    db = db_factory()
    _seed(db, "stale_a", "claimed", claimed_minutes_ago=120)
    _seed(db, "stale_b", "claimed", claimed_minutes_ago=90)
    _seed(db, "fresh_c", "claimed", claimed_minutes_ago=1)
    reclaimed = reap_stale_claims(db, timeout_seconds=1800)
    assert set(reclaimed) == {"stale_a", "stale_b"}


# ---- POST /reap endpoint ----

def test_reap_endpoint_reclaims_and_reports(client, db_factory):
    db = db_factory()
    _seed(db, "stale_ep", "claimed", claimed_minutes_ago=60)
    db.close()
    r = client.post("/api/platform/fde/reap", json={"timeout_seconds": 1800})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["reclaimed"] == ["stale_ep"]
    assert data["count"] == 1
    # the task is now claimable again
    opened = client.get("/api/platform/fde/tasks", params={"status": "open"}).json()["data"]["tasks"]
    assert any(t["task_uid"] == "stale_ep" for t in opened)


def test_reap_endpoint_default_timeout(client, db_factory):
    """No body → uses default timeout, still safe (fresh claims survive)."""
    db = db_factory()
    _seed(db, "fresh_ep", "claimed", claimed_minutes_ago=1)
    db.close()
    r = client.post("/api/platform/fde/reap", json={})
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 0
