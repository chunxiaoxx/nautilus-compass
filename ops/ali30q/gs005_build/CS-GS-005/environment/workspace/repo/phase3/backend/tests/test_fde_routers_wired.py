"""Wiring smoke · fde_grounding + fde_rsi_delta routers must be mounted on the
production app (main.py), not just test-local FastAPI fixtures.

Until deploy these routers existed + had unit tests but were NOT included in
main.py (gated · G-cloud). This pins the wiring once it lands.

NOTE: main.py is not import-able in this local checkout (master imports
`services.agent_service`, which lives only in the deployed cloud fork — a
pre-existing master/fork divergence, unrelated to FDE). So we assert at the
SOURCE level: the import + include_router statements are present in main.py.
The router-mounts-and-serves behavior is covered by test_fde_grounding.py /
test_fde_rsi_delta.py against a local app fixture.
"""
from __future__ import annotations

import os

_MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")


def _main_src() -> str:
    with open(_MAIN, encoding="utf-8") as fh:
        return fh.read()


def test_grounding_router_imported_and_included():
    src = _main_src()
    assert "from api.fde_grounding import router as fde_grounding_router" in src
    assert "app.include_router(fde_grounding_router)" in src


def test_rsi_delta_router_imported_and_included():
    src = _main_src()
    assert "from api.fde_rsi_delta import router as fde_rsi_delta_router" in src
    assert "app.include_router(fde_rsi_delta_router)" in src


def test_attention_router_imported_and_included():
    src = _main_src()
    assert "from api.fde_attention import router as fde_attention_router" in src
    assert "app.include_router(fde_attention_router)" in src


def test_fde_attention_model_imported():
    src = _main_src()
    assert "import models.fde_attention" in src
