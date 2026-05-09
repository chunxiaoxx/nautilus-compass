"""V7 governance demo · v1.0+ · path B' scaffold.

Exercises the 3 V7 MCP tools end-to-end so a CI smoke proves the
governance layer is wired right:

    governance_lock_check   →  bootstrap + idempotent re-check
    governance_dispatch     →  4-channel decompose → 4 routed sub-task files
    governance_audit        →  scan recent memory · count suspects

V7 sits ABOVE V5/V6/Kairos. It does NOT execute. It writes routing files
and audit artifacts; platform side mints bounties + collects governance fee.
This demo plays the OSS half only — platform side TODO is documented in
docs/PLATFORM_HANDSHAKE.md §8.4.

Run:

    python examples/v7_governance_demo.py
    python examples/v7_governance_demo.py --verbose

Returns nonzero on any leg failure → CI-able.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from mcp_client import MCPClient, MCPClientError  # noqa: E402

PROJECTS_DIR = Path.home() / ".claude" / "projects"
PLATFORM_QUEUE_DIR = PROJECTS_DIR / "_platform_queue"
GOVERNANCE_AUDIT_DIR = PROJECTS_DIR / "_governance_audits"
GOVERNANCE_LOCK = PLUGIN_ROOT / "governance.lock"

DEMO_TOKEN = "demo-v7-governance"
DEMO_TASK_NAME = "launch-nautilus-compass-v1.0-demo"
DEMO_CHANNELS = ["dev.to", "x-en", "github-issue", "kg"]

EXPECTED_ROUTING = {
    "dev.to": "nautilus-v5",
    "x-en": "nautilus-v5",
    "github-issue": "nautilus-v6",
    "kg": "kairos",
}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def _spawn_server(token: str):
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--token", token]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
    try:
        deadline = time.time() + 3.0
        while time.time() < deadline:
            line = proc.stderr.readline() if proc.stderr else b""
            if b"listening on" in line:
                yield port
                return
        raise RuntimeError("compass MCP server did not announce readiness")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def _text(reply: dict) -> str:
    content = reply.get("content") or []
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return ""


def step_1_lock_bootstrap(host: str, port: int, token: str, verbose: bool) -> None:
    """Bootstrap or verify L0 hash lock."""
    print("\n[1] V7 governance_lock_check · bootstrap + verify")
    with MCPClient(host=host, port=port, token=token,
                   client_name="v7-demo") as c:
        # Bootstrap (idempotent if lock exists)
        boot = _text(c.call_tool("governance_lock_check", {"bootstrap": True}))
        if verbose:
            print(f"    boot: {boot}")
        if "bootstrapped" not in boot:
            raise RuntimeError(f"lock bootstrap unexpected: {boot}")
        # Verify
        verify = _text(c.call_tool("governance_lock_check", {}))
        if verbose:
            print(f"    verify: {verify}")
        if "OK" not in verify:
            raise RuntimeError(f"lock verify failed: {verify}")
        print(f"    L0 lock · bootstrapped + verified · 4 files SHA256-locked")


def step_2_dispatch(host: str, port: int, token: str, verbose: bool) -> str:
    """V7 decomposes complex task into routed sub-tasks."""
    print(f"\n[2] V7 governance_dispatch · {len(DEMO_CHANNELS)} channels")
    with MCPClient(host=host, port=port, token=token,
                   client_name="v7-demo") as c:
        reply = c.call_tool("governance_dispatch", {
            "name": DEMO_TASK_NAME,
            "channels": DEMO_CHANNELS,
            "anchor_pack_hint": "marketing/dev-tools",
            "priority": "high",
            "payload": {
                "release_tag": "v1.0.0",
                "headline": "drift detector + tamper-evident memory log",
            },
        })
        text = _text(reply)
        if verbose:
            print(text)

        # Parse parent_task_id from "V7 dispatch · parent=v7tk_<ms> · ..."
        parent_id = None
        for chunk in text.split("·"):
            chunk = chunk.strip()
            if chunk.startswith("parent="):
                parent_id = chunk.removeprefix("parent=").strip()
                break
        if not parent_id:
            raise RuntimeError(f"could not parse parent_task_id from: {text}")
        print(f"    parent={parent_id}")

        # Verify N sub-task files exist with correct routing
        for idx, ch in enumerate(DEMO_CHANNELS):
            sub_id = f"{parent_id}_{idx:02d}"
            sub_file = PLATFORM_QUEUE_DIR / f"{sub_id}.json"
            if not sub_file.exists():
                raise RuntimeError(f"sub-task file missing: {sub_file}")
            spec = json.loads(sub_file.read_text(encoding="utf-8"))
            actual = spec.get("v7_routed_executor")
            expected = EXPECTED_ROUTING[ch]
            if actual != expected:
                raise RuntimeError(
                    f"routing mismatch on {ch}: got {actual}, expected {expected}"
                )
            if not spec.get("v7_dispatched"):
                raise RuntimeError(f"v7_dispatched flag missing on {sub_id}")
            print(f"    {ch:<14} → {actual:<14} ({sub_id})")
        return parent_id


def step_3_audit(host: str, port: int, token: str, verbose: bool) -> None:
    """V7 scans recent memory for fake-closure / red drift."""
    print("\n[3] V7 governance_audit · 7-day scan")
    with MCPClient(host=host, port=port, token=token,
                   client_name="v7-demo") as c:
        reply = c.call_tool("governance_audit", {"days": 7})
        text = _text(reply)
        if verbose:
            print(text)
        if "audit_" not in text or "scanned" not in text:
            raise RuntimeError(f"audit output unexpected: {text}")
        # Parse audit_id from output
        audit_id = None
        for line in text.splitlines():
            if line.startswith("V7 audit"):
                for chunk in line.split("·"):
                    c2 = chunk.strip()
                    if c2.startswith("audit_"):
                        audit_id = c2.split()[0]
                        break
        if not audit_id:
            raise RuntimeError(f"could not parse audit_id from: {text}")
        archive = GOVERNANCE_AUDIT_DIR / f"{audit_id}.json"
        if not archive.exists():
            raise RuntimeError(f"audit archive missing: {archive}")
        archive_data = json.loads(archive.read_text(encoding="utf-8"))
        scanned = archive_data.get("files_scanned", 0)
        suspects = (
            len(archive_data.get("red_drift", [])) +
            len(archive_data.get("fake_closure", [])) +
            len(archive_data.get("empty_platform_results", []))
        )
        print(f"    audit={audit_id} · scanned={scanned} · suspects={suspects}")


def step_4_cleanup(parent_id: str, verbose: bool) -> None:
    """Idempotent: remove demo artefacts."""
    print("\n[4] cleanup demo artefacts")
    removed = 0
    for idx in range(len(DEMO_CHANNELS)):
        f = PLATFORM_QUEUE_DIR / f"{parent_id}_{idx:02d}.json"
        if f.exists():
            f.unlink()
            removed += 1
            if verbose:
                print(f"    rm {f}")
    print(f"    removed {removed} sub-task file(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true",
                        help="print raw RPC payloads + audit archive")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="leave dispatched sub-task files for inspection")
    args = parser.parse_args(argv)

    print("=" * 64)
    print("V7 governance demo · path B' (decompose+audit+lock, no execute)")
    print("=" * 64)

    parent_id = "v7tk_unknown"
    with _spawn_server(DEMO_TOKEN) as port:
        host = "127.0.0.1"
        try:
            step_1_lock_bootstrap(host, port, DEMO_TOKEN, args.verbose)
            parent_id = step_2_dispatch(host, port, DEMO_TOKEN, args.verbose)
            step_3_audit(host, port, DEMO_TOKEN, args.verbose)
        except (MCPClientError, RuntimeError) as e:
            print(f"\nDEMO FAILED: {e}")
            return 2
        finally:
            if not args.no_cleanup:
                step_4_cleanup(parent_id, args.verbose)

    print("\n" + "=" * 64)
    print("OK · V7 v0.1 governance round-trip verified")
    print("    lock_check · dispatch → 4 routed files · audit scan")
    print("    platform side TODO: v7-monitor cron + governance fee · §8.4")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
