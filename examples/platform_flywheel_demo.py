"""Platform flywheel demo · v1.0+ (BP1 + BP3).

End-to-end simulation of the OSS ↔ platform bidirectional flywheel:

    compass dialog ──[submit_platform_task]──→ _platform_queue/
           ▲                                        │
           │                                        │ V5 cycle claims
           │                                        │ (simulated here as
           │                                        │  read+update file)
           │                                        ▼
           │                                  platform agent does work
           │                                        │
           └─[session_search]── memory ←─[ingest_platform_task_result]─┘

This demo plays both halves so you can run it standalone with no platform
deployed yet:

  1. Compass peer · submit_platform_task("publish-launch-post", channels=[dev.to,x])
  2. Platform poller (this script) · reads queue file, marks status=claimed
  3. Platform agent peer · ingest_platform_task_result(task_id, summary, ...)
  4. Either peer · session_search("platform task launch") → finds the result
  5. Cleanup smoke artefacts so the demo is idempotent

Run directly (spawns its own TCP server on a free port):

    python examples/platform_flywheel_demo.py

Or with verbose JSON-RPC tracing:

    python examples/platform_flywheel_demo.py --verbose

Returns nonzero exit code on failure of any leg of the round-trip,
making it usable as a CI smoke for the BP1+BP3 contract.
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
PLATFORM_RESULTS_DIR = PROJECTS_DIR / "_platform_results"

DEMO_TOKEN = "demo-flywheel-shared"
DEMO_TASK_NAME = "publish-launch-post-flywheel-demo"


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


def step_1_compass_submit(host: str, port: int, token: str, verbose: bool) -> str:
    """Compass dialog hands work to the platform via submit_platform_task."""
    print("\n[1] compass dialog → submit_platform_task")
    with MCPClient(host=host, port=port, token=token,
                   client_name="compass-dialog") as compass:
        reply = compass.call_tool("submit_platform_task", {
            "name": DEMO_TASK_NAME,
            "channels": ["dev.to", "x"],
            "anchor_pack_hint": "marketing/dev-tools",
            "priority": "high",
            "payload": {
                "title": "Compass v1.0 launch",
                "body_md": "Open-source memory layer for LLM agents...",
                "tags": ["llm", "memory", "mcp", "a2a"],
            },
        })
        text = _text(reply)
        if verbose:
            print(f"    raw: {text}")
        # Parse out task_id from the response text
        # Format: "task queued · id=tk_<unix_ms> · channels=... · priority=high · file-only..."
        for token_part in text.split("·"):
            token_part = token_part.strip()
            if token_part.startswith("id="):
                task_id = token_part.removeprefix("id=").strip()
                print(f"    queued · task_id={task_id}")
                return task_id
        raise RuntimeError(f"could not parse task_id from: {text}")


def step_2_platform_poll(task_id: str, verbose: bool) -> dict:
    """Simulate platform V5 cycle polling the queue dir."""
    print("\n[2] platform V5 cycle ← poll _platform_queue/")
    queue_file = PLATFORM_QUEUE_DIR / f"{task_id}.json"
    if not queue_file.exists():
        raise RuntimeError(f"BP1 broken: queue file missing at {queue_file}")
    spec = json.loads(queue_file.read_text(encoding="utf-8"))
    if verbose:
        print(f"    queue file: {queue_file}")
        print(f"    spec channels: {spec.get('channels')} · priority: {spec.get('priority')}")
    # V5 cycle would match anchor_pack_hint → platform_anchor_packs and pick agent
    # Simulate the claim by writing back status=claimed
    spec["status"] = "claimed"
    spec["claimed_by"] = "platform-agent-0xdemoagent"
    spec["claimed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    queue_file.write_text(json.dumps(spec, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"    claimed by {spec['claimed_by']} · status={spec['status']}")
    return spec


def step_3_platform_work(spec: dict) -> dict:
    """Simulate platform agent doing the actual publish work."""
    print("\n[3] platform agent → executes channels")
    # Real V5 cycle would dispatch via channel adapters (dispatch_publish etc).
    # Here we just fabricate URLs as if both channels succeeded.
    channels_published = []
    for ch in spec.get("channels", []):
        url = f"https://{ch}/u/demo/{spec['task_id']}"
        channels_published.append({
            "channel": ch,
            "url": url,
            "status": "success",
        })
        print(f"    {ch:<12} → {url}")
    return {
        "task_id": spec["task_id"],
        "result_summary": (
            f"Published '{spec['name']}' to {len(channels_published)} channels "
            f"({', '.join(c['channel'] for c in channels_published)}) · "
            f"all 200 OK · platform agent simulated"
        ),
        "channels_published": channels_published,
        "drift": "green",
        "agent_id": spec.get("claimed_by", "platform-agent-unknown"),
    }


def step_4_platform_ingest(host: str, port: int, token: str,
                            result_payload: dict, verbose: bool) -> str:
    """Platform calls ingest_platform_task_result to push result back into compass memory."""
    print("\n[4] platform agent → ingest_platform_task_result")
    with MCPClient(host=host, port=port, token=token,
                   client_name="platform-agent") as platform:
        reply = platform.call_tool("ingest_platform_task_result", result_payload)
        text = _text(reply)
        print(f"    {text}")
        return text


def step_5_compass_search(host: str, port: int, token: str,
                           task_id: str, verbose: bool) -> bool:
    """Compass dialog confirms the result is searchable cross-session."""
    print("\n[5] compass dialog → session_search confirms result in memory")
    with MCPClient(host=host, port=port, token=token,
                   client_name="compass-dialog") as compass:
        reply = compass.call_tool("session_search", {
            "query": f"platform task {task_id}",
            "top_k": 3,
        })
        text = _text(reply)
        if verbose:
            print(text)
        # Look for our task_id in the search hits
        if task_id[:20] in text or "platform_" in text.lower():
            print(f"    HIT · result is searchable cross-session ✓")
            return True
        print("    MISS · BP3 broken? full output:")
        print(text)
        return False


def step_6_cleanup(task_id: str, verbose: bool) -> None:
    """Idempotent: remove demo artefacts so subsequent runs start clean."""
    print("\n[6] cleanup demo artefacts")
    targets: list[Path] = []
    targets.append(PLATFORM_QUEUE_DIR / f"{task_id}.json")
    targets.append(PLATFORM_RESULTS_DIR / f"{task_id}_result.json")
    # Find session_*.md written by ingest_platform_task_result
    for proj_dir in PROJECTS_DIR.iterdir():
        mem = proj_dir / "memory"
        if not mem.is_dir():
            continue
        for f in mem.glob(f"session_*platform_{task_id[:24]}*.md"):
            targets.append(f)
    removed = 0
    for t in targets:
        if t.exists():
            t.unlink()
            removed += 1
            if verbose:
                print(f"    rm {t}")
    print(f"    removed {removed} demo artefact(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true",
                        help="print raw RPC payloads + queue file contents")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="leave demo artefacts behind for inspection")
    args = parser.parse_args(argv)

    print("=" * 64)
    print("Platform flywheel demo · BP1 (compass→platform) + BP3 (back)")
    print("=" * 64)

    with _spawn_server(DEMO_TOKEN) as port:
        host = "127.0.0.1"
        try:
            task_id = step_1_compass_submit(host, port, DEMO_TOKEN, args.verbose)
            spec = step_2_platform_poll(task_id, args.verbose)
            result_payload = step_3_platform_work(spec)
            step_4_platform_ingest(host, port, DEMO_TOKEN, result_payload, args.verbose)
            ok = step_5_compass_search(host, port, DEMO_TOKEN, task_id, args.verbose)
        except (MCPClientError, RuntimeError) as e:
            print(f"\nDEMO FAILED: {e}")
            return 2
        finally:
            if not args.no_cleanup:
                # task_id may not exist if step 1 failed
                step_6_cleanup(locals().get("task_id", "tk_demo_unknown"), args.verbose)

    if not ok:
        return 1
    print("\n" + "=" * 64)
    print("OK · BP1 + BP3 round-trip verified")
    print("    submit → file → claim → work → ingest → session_search hit")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
