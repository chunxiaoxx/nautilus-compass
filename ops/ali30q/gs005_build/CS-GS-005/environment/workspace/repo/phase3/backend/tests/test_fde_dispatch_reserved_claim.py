"""Named-claim gate (2026-08-25 · kairos 抢 p5 燃料事件).

Root cause: /fde/dispatch/claim is first-come-first-served for ANY agent_id.
Fuel minted with an owner in mind sat `open` for hours and a resident poller
(kairos) claimed it. Fix: optional `reserved_for` (top-level on /dispatch, or
pre-existing key inside the description JSON) — when set, only that agent_id
may claim; everyone else gets 403. Tasks without reserved_for keep the old
open-market behavior (back-compat for the S1 派活表 unnamed flow).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from models.fde_dispatch import FdeDispatch  # noqa: F401
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from utils.platform_auth import require_platform_key
from api.fde_dispatch import router as fde_router


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(fde_router)
    app.dependency_overrides[get_db] = override_get_db
    # bypass X-Platform-Key (env-present on cloud → 401 without this override;
    # env-absent locally would silently pass — override makes it deterministic)
    app.dependency_overrides[require_platform_key] = lambda: None
    return TestClient(app)


def _mint(client, task_uid, reserved_for=None, description=None):
    body = {"task_uid": task_uid, "title": f"t {task_uid}"}
    if description is not None:
        body["description"] = description
    if reserved_for is not None:
        body["reserved_for"] = reserved_for
    return client.post("/api/platform/fde/dispatch", json=body)


def test_reserved_task_rejects_other_agent(client):
    _mint(client, "fuel_r1", reserved_for="nautilus-prime-001")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "fuel_r1", "agent_id": "kairos"})
    assert r.status_code == 403
    assert "reserved" in r.json()["error"]


def test_reserved_task_accepts_owner(client):
    _mint(client, "fuel_r2", reserved_for="nautilus-prime-001")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "fuel_r2", "agent_id": "nautilus-prime-001"})
    assert r.status_code == 200
    assert r.json()["data"]["claimed_by"] == "nautilus-prime-001"


def test_reserved_for_inside_description_json_is_honored(client):
    # fuel minters already stuff a JSON dict into description (p5 rows) — the
    # reservation may live there; claim gate must read it back out.
    _mint(client, "fuel_r3", description={"fde_class": 3, "reserved_for": "flywheel-daemon"})
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "fuel_r3", "agent_id": "kairos"})
    assert r.status_code == 403
    r2 = client.post("/api/platform/fde/claim",
                     json={"task_uid": "fuel_r3", "agent_id": "flywheel-daemon"})
    assert r2.status_code == 200


def test_unreserved_task_stays_open_market(client):
    # back-compat: S1 派活表 unnamed flow and pre-existing rows keep FCFS.
    _mint(client, "fuel_r4")
    r = client.post("/api/platform/fde/claim",
                    json={"task_uid": "fuel_r4", "agent_id": "kairos"})
    assert r.status_code == 200


def test_dispatch_persists_reserved_for_into_description(client):
    _mint(client, "fuel_r5", reserved_for="expert:zhang",
          description={"fde_class": 3})
    r = client.get("/api/platform/fde/tasks", params={"status": "open"})
    row = next(t for t in r.json()["data"]["tasks"] if t["task_uid"] == "fuel_r5")
    desc = row["description"]
    if isinstance(desc, str):  # Text column · stored as JSON string
        import json as _json
        desc = _json.loads(desc)
    assert desc["reserved_for"] == "expert:zhang"
    assert desc["fde_class"] == 3  # original content preserved
