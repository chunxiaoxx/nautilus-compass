"""Wiring smoke · control_plane router must be mounted on the production app
(main.py), not just test-local FastAPI fixtures.

control_plane.py (GET /api/platform/control-plane + POST /api/platform/dispatch)
had unit tests against a local app fixture but was NOT included in main.py
(gated · the aggregation spine + safe-action dispatch). This pins the wiring
once it lands.

NOTE: main.py is not import-able in this local checkout (master imports
`services.agent_service`, which lives only in the deployed cloud fork — a
pre-existing master/fork divergence, unrelated to the control plane). So we
assert at the SOURCE level: the import + include_router statements are present
in main.py. The router-mounts-and-serves behavior is covered by
test_control_plane.py / test_control_plane_loops.py against a local app fixture
and by scripts/run_control_plane_local.py for live curl.
"""
from __future__ import annotations

import os

_MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")


def _main_src() -> str:
    with open(_MAIN, encoding="utf-8") as fh:
        return fh.read()


def test_control_plane_router_wired():
    src = _main_src()
    assert "from api.control_plane import router as control_plane_router" in src
    assert "app.include_router(control_plane_router)" in src
