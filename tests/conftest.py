"""Shared HTTP test client: mcp_http_server.app's StreamableHTTPSessionManager
supports exactly one lifespan per process, so all modules must share a single
TestClient (session-scoped, never exits). Test isolation comes from unique
emails + the shared tmp DB; per-test env toggles (e.g. COMPASS_EMAIL_REQUIRED)
work because os.environ is process-global and TestClient calls are synchronous.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def http_client(tmp_path_factory):
    from _pytest.monkeypatch import MonkeyPatch
    with MonkeyPatch.context() as mp:
        mp.setenv("COMPASS_MVP_DB",
                  str(tmp_path_factory.mktemp("httpdb") / "http.db"))
        mp.setenv("COMPASS_EMAIL_REQUIRED", "0")   # off by default; opt in per test
        from mcp_http_server import app
        from starlette.testclient import TestClient
        with TestClient(app) as c:
            yield c
