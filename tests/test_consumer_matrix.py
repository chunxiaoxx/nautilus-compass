"""Consumer-matrix contract test (三支柱·契约化 · 9/15 acceptance artifact).

Every consumer of the daemon ports (9876 local TCP / 8097 public HTTP /
9877 legacy tunnel · 8770 retired) is registered here. The test verifies:
  1. each registered consumer file still exists
  2. it still references the port it is registered against
  3. 9876 consumers follow the token discipline (9/1+ auth requirement)

Run this after ANY protocol/interface change on these ports. A red here
means a consumer was missed — fix the consumer or update the registry
with a dated reason, never delete silently.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

# (file, port-in-file, token-discipline-required)
CONSUMERS_9876 = [
    ("mcp_server.py", True),          # MCP server -> daemon_call
    ("recall.py", True),
    ("doctor.py", True),
    ("mid_session_hook.py", True),
    ("stop_hook.py", True),
    ("audit_kpi.py", False),          # 9876 only in docstring example command
    ("tools/compass_goal_heartbeat.py", True),
    ("tools/recall_usefulness_exp.py", True),
    ("ops/recall_fallback.py", True),
    ("ops/compass_hud_wrapper.py", True),
    ("ops/pull_cloud_candidates.py", False),  # 9876 only in docstring note
    ("examples/semantic_recall_e2e.py", True),
    ("bin/compass-mcp.js", False),    # node wrapper: passthrough, no direct call
    ("daemon_start.ps1", False),      # launcher
    ("ops/compass_start.ps1", False),
    ("ops/local_daemon_start.ps1", False),
]
CONSUMERS_TUNNEL = [
    "ops/mcp_stdio_to_cloud.py",      # 9877 stdio->cloud bridge (retires 9/15)
    "ops/compass_forward_watchdog.ps1",
]
CONSUMERS_HTTP = [
    "compass_http_v09.py",            # 8770 v0.9 (public ingress closed 8/30)
    "cloud_ingest.py",                # POSTs to cloud 8770 /v1/v14/ingest_obs
    "examples/compass_client_v15.py", # v1.5 client, default base 8770
    "ops/compass_health_cron.py",     # polls 8770 /compass/health
    "ops/smoke_keepalive_fix.py",     # smokes 8770 /v1/v14/recall keepalive
]

TOKEN_MARKERS = ("token", "TOKEN")  # auth discipline markers


@pytest.mark.parametrize("rel", [c[0] for c in CONSUMERS_9876])
def test_9876_consumer_exists_and_references_port(rel: str):
    p = ROOT / rel
    assert p.exists(), f"registered 9876 consumer missing: {rel}"
    src = p.read_text(encoding="utf-8", errors="ignore")
    assert "9876" in src, f"{rel} registered as 9876 consumer but no port ref"


@pytest.mark.parametrize("rel,needs_token", CONSUMERS_9876)
def test_9876_token_discipline(rel: str, needs_token: bool):
    if not needs_token:
        pytest.skip("launcher/passthrough — no direct daemon_call")
    p = ROOT / rel
    src = p.read_text(encoding="utf-8", errors="ignore")
    assert any(m in src for m in TOKEN_MARKERS), (
        f"{rel} calls 9876 without token discipline (9/1+ requirement)")


@pytest.mark.parametrize("rel", CONSUMERS_TUNNEL + CONSUMERS_HTTP)
def test_tunnel_http_consumers_exist(rel: str):
    p = ROOT / rel
    assert p.exists(), f"registered consumer missing: {rel}"


def test_registry_is_complete_known_ports():
    """The registry must keep covering every file that references a port.
    Sweep the live tree (ripgrep-backed glob via Path walk, cheap dirs only)
    and fail when an unregistered referencing file shows up in first-party dirs.
    """
    first_party_dirs = ["ops", "tools", "examples", "bin"]
    registered = {c[0] for c in CONSUMERS_9876} | set(CONSUMERS_TUNNEL) | set(CONSUMERS_HTTP)
    for d in first_party_dirs:
        for p in (ROOT / d).rglob("*"):
            if p.suffix in (".py", ".ps1", ".js") and p.is_file():
                try:
                    src = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if any(port in src for port in ("9876", ":8770", ":9877", ":8097")):
                    rel = p.relative_to(ROOT).as_posix()
                    assert rel in registered, (
                        f"unregistered port consumer: {rel} — register it or remove the port ref")
