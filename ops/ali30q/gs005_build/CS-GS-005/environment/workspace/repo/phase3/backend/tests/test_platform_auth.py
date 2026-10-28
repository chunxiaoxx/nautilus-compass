"""require_platform_key · fail-closed on prod (key set) · permissive in dev (unset)."""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from utils.platform_auth import require_platform_key


@pytest.fixture
def app():
    a = FastAPI()

    @a.post("/guarded")
    def guarded(_=Depends(require_platform_key)):
        return {"ok": True}

    return a


def test_permissive_when_no_key_configured(app, monkeypatch):
    monkeypatch.delenv("PLATFORM_DISPATCH_KEY", raising=False)
    c = TestClient(app)
    assert c.post("/guarded").status_code == 200


def test_rejects_when_key_set_and_header_missing(app, monkeypatch):
    monkeypatch.setenv("PLATFORM_DISPATCH_KEY", "secret123")
    c = TestClient(app)
    assert c.post("/guarded").status_code == 401


def test_rejects_wrong_key(app, monkeypatch):
    monkeypatch.setenv("PLATFORM_DISPATCH_KEY", "secret123")
    c = TestClient(app)
    assert c.post("/guarded", headers={"X-Platform-Key": "nope"}).status_code == 401


def test_accepts_matching_key(app, monkeypatch):
    monkeypatch.setenv("PLATFORM_DISPATCH_KEY", "secret123")
    c = TestClient(app)
    assert c.post("/guarded", headers={"X-Platform-Key": "secret123"}).status_code == 200
