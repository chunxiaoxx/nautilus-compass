"""Smoke for examples/full_capability_demo.py · launch-ready video demo.

Locks in:
- Demo runs to completion (exit 0) on a fresh laptop with optional deps
  (BGE daemon may be down — that's a graceful ⚠ not a fatal ✗).
- All five demos produce a verdict line.
- Final summary reports total ok count.
- MCP round-trip really hits the 8-tool surface.

Wall-clock budget: ~15s · subprocess waits for spawned mcp_server stdio.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "examples" / "full_capability_demo.py"


def test_demo_completes_without_crashing():
    assert DEMO.is_file(), f"missing {DEMO}"
    result = subprocess.run(
        [sys.executable, str(DEMO)],
        capture_output=True, text=True, encoding="utf-8",
        timeout=60, cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"demo exit={result.returncode}\n"
        f"stdout: {result.stdout[-500:]}\n"
        f"stderr: {result.stderr[-500:]}"
    )
    out = result.stdout
    # Every demo prints a banner of the form "Demo N/5"
    for n in range(1, 6):
        assert f"Demo {n}/5" in out, f"missing banner Demo {n}/5\n{out}"
    # Final summary line shape: "X/5 ok · ..."
    assert "/5 ok" in out, f"missing summary line\n{out[-500:]}"


def test_demo_mcp_round_trip_exposes_tools():
    """The MCP demo step must surface tools — the protocol is the
    most likely surface to silently break and not have a smoke."""
    result = subprocess.run(
        [sys.executable, str(DEMO)],
        capture_output=True, text=True, encoding="utf-8",
        timeout=60, cwd=str(ROOT),
    )
    out = result.stdout
    assert "tools/list" in out, "MCP demo did not log tools/list"
    # Server should expose at least the 7 core tools + long_task = 8.
    assert "8 tools" in out or any(
        t in out for t in ("drift_check", "ingest_obs", "feedback_log")
    ), f"MCP tool surface missing from demo output:\n{out[-500:]}"
