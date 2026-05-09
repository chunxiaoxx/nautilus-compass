"""Third-party client integration shim · Task #61.

Subprocesses examples/third_party_client.py, which is **pure stdlib** —
zero import of mcp_client.py or anything else from this repo. If this
test stays green, anyone with `json` and a subprocess pipe in their
language can speak MCP to nautilus-compass.

This unblocks the rc2 → 1.0.0 promotion: the protocol surface is
proven portable, not just "works with our own client".
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIM = ROOT / "examples" / "third_party_client.py"


def test_shim_completes_full_round_trip():
    assert SHIM.is_file(), f"missing {SHIM}"
    result = subprocess.run(
        [sys.executable, str(SHIM)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"shim exit={result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    out = result.stdout
    # Each step prints a ✓ marker · all five must be present.
    for marker in (
        "✓ initialize",
        "✓ tools/list",
        "✓ tools/call recall",
        "✓ tools/call drift_check",
        "✓ shutdown",
    ):
        assert marker in out, f"missing step marker {marker!r}\n{out}"
    # Capabilities round-trip must surface all three rc2 surfaces.
    assert "tools" in out and "resources" in out and "logging" in out, (
        f"capabilities banner missing one of tools/resources/logging:\n{out}"
    )
    # Both required tools must show up in tools/list.
    assert "recall" in out and "drift_check" in out


def test_shim_imports_no_repo_modules():
    """Static guard · the whole point is that this script is portable.

    If someone adds `import mcp_client` here later they break the
    promotion criterion. Catch it at lint time.
    """
    text = SHIM.read_text(encoding="utf-8")
    forbidden = (
        "import mcp_client",
        "from mcp_client",
        "import mcp_server",
        "from mcp_server",
        "import recall",
        "import compass",
    )
    for needle in forbidden:
        assert needle not in text, (
            f"third-party shim must not depend on this repo · "
            f"found {needle!r} in {SHIM.name}"
        )
