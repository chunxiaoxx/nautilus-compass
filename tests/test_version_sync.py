"""Lock the three version strings together · Task #60.

pyproject.toml + package.json + mcp_server.SERVER_VERSION must stay
in sync · a mismatch makes the MCP handshake lie to clients about
what they're talking to. This guards the three sites against drift.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mcp_server


def _read_pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "pyproject.toml has no top-level version = \"...\""
    return m.group(1)


def _read_package_version() -> str:
    data = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return data["version"]


def test_all_three_version_strings_match():
    py = _read_pyproject_version()
    pkg = _read_package_version()
    srv = mcp_server.SERVER_VERSION
    assert py == pkg == srv, (
        f"version drift · pyproject={py!r} package={pkg!r} "
        f"server={srv!r}"
    )


def test_server_info_reflects_version():
    info = {"name": mcp_server.SERVER_NAME, "version": mcp_server.SERVER_VERSION}
    assert info["version"] == _read_pyproject_version()
