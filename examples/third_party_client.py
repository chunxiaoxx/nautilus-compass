#!/usr/bin/env python3
"""Third-party MCP client shim · pure stdlib · Task #61.

Demonstrates that the MCP server in this plugin speaks plain
JSON-RPC 2.0 over stdio · zero compass-specific dependencies.

Anyone with a JSON parser and a subprocess pipe (Node, Go, Rust, Swift,
shell) can replicate this loop in their own language. We use only
stdlib `json`, `subprocess`, `sys` — explicitly **no** import of
`mcp_client.py` or anything else from this repo. If this works, the
protocol surface is genuinely portable.

Run:
    python examples/third_party_client.py

Round-trip exercised:
    1. spawn server as a child process
    2. initialize handshake
    3. tools/list
    4. tools/call recall (with a benign query)
    5. tools/call drift_check (with a benign prompt)
    6. shutdown via stdin close

Exits 0 on a clean round-trip · 1 on any protocol or process error.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Windows GBK consoles choke on ✓ — match compass_verify.py and force
# UTF-8 stdout/stderr so the demo prints cleanly under any console.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "mcp_server.py"


class JsonRpcError(RuntimeError):
    pass


def send(proc: subprocess.Popen, payload: dict) -> None:
    line = json.dumps(payload) + "\n"
    assert proc.stdin is not None
    proc.stdin.write(line)
    proc.stdin.flush()


def recv(proc: subprocess.Popen) -> dict:
    """Read one JSON-RPC frame (one line) and parse it."""
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline()
        if not line:
            stderr = ""
            if proc.stderr is not None:
                try:
                    stderr = proc.stderr.read() or ""
                except Exception:
                    pass
            raise JsonRpcError(
                f"server closed stdout without reply · stderr: {stderr[:500]}"
            )
        line = line.strip()
        if not line:
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            # Skip non-JSON noise (banners, log lines)
            continue
        # Skip server-initiated notifications · we only want the reply
        # to our most recent request.
        if "id" not in frame and frame.get("method", "").startswith(
            "notifications/"
        ):
            continue
        return frame


def call(proc: subprocess.Popen, msg_id: int, method: str,
         params: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        payload["params"] = params
    send(proc, payload)
    reply = recv(proc)
    if "error" in reply:
        raise JsonRpcError(
            f"{method} failed · code={reply['error'].get('code')} "
            f"msg={reply['error'].get('message')}"
        )
    return reply["result"]


def main() -> int:
    if not SERVER.is_file():
        print(f"server not found at {SERVER}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(ROOT),
    )

    try:
        # 1. initialize
        info = call(proc, 1, "initialize",
                    {"protocolVersion": "2024-11-05",
                     "clientInfo": {"name": "third-party-shim",
                                    "version": "0.1.0"}})
        protocol = info.get("protocolVersion")
        server_name = info.get("serverInfo", {}).get("name")
        server_version = info.get("serverInfo", {}).get("version")
        caps = info.get("capabilities", {})
        print(f"✓ initialize · protocol={protocol} · "
              f"{server_name} {server_version}")
        for cap in ("tools", "resources", "logging"):
            assert cap in caps, f"missing capability {cap!r}"
        print(f"  capabilities: {sorted(caps.keys())}")

        # 2. notifications/initialized · fire-and-forget
        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3. tools/list
        tools_result = call(proc, 2, "tools/list")
        names = [t["name"] for t in tools_result.get("tools", [])]
        assert names, "tools/list returned empty"
        print(f"✓ tools/list · {len(names)} tools: "
              f"{', '.join(sorted(names))}")
        for required in ("recall", "drift_check"):
            assert required in names, (
                f"required tool {required!r} missing from {names}"
            )

        # 4. tools/call recall · benign query · daemon may be down,
        #    we accept any text reply (including empty hits)
        recall_result = call(proc, 3, "tools/call",
                             {"name": "recall",
                              "arguments": {"query": "hello world"}})
        content = recall_result.get("content", [])
        assert isinstance(content, list), f"recall content not list: {content}"
        snippet = ""
        for c in content:
            if c.get("type") == "text":
                snippet = (c.get("text") or "")[:80]
                break
        print(f"✓ tools/call recall · {len(content)} content items"
              f"{' · ' + snippet if snippet else ''}")

        # 5. tools/call drift_check · benign prompt
        drift_result = call(proc, 4, "tools/call",
                            {"name": "drift_check",
                             "arguments": {"prompt": "what is 2+2"}})
        content = drift_result.get("content", [])
        assert isinstance(content, list)
        print(f"✓ tools/call drift_check · {len(content)} content items")

        # 6. clean shutdown · close stdin so the server's stdio loop exits
        assert proc.stdin is not None
        proc.stdin.close()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=2)
        print(f"✓ shutdown · exit={proc.returncode}")
        return 0

    except JsonRpcError as e:
        print(f"protocol error · {e}", file=sys.stderr)
        return 1
    except AssertionError as e:
        print(f"assertion failed · {e}", file=sys.stderr)
        return 1
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
