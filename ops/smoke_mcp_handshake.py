#!/usr/bin/env python3
"""End-to-end MCP handshake smoke · simulates what Claude Code does.

Spawns mcp_stdio_to_cloud.py as subprocess · sends `initialize` JSON-RPC
· waits up to 5s for response · prints what we got.

This reproduces the exact failure mode Claude Code sees if the bridge
script can't complete MCP handshake.
"""
import json
import os
import subprocess
import sys
import time


SCRIPT = r"C:\Users\chunx\.claude\plugins\nautilus-compass\ops\mcp_stdio_to_cloud.py"
ENV = {
    **os.environ,
    "COMPASS_CLOUD_HOST": "127.0.0.1",
    "COMPASS_CLOUD_PORT": "9877",
    "COMPASS_CLOUD_TOKEN": os.environ.get("COMPASS_CLOUD_TOKEN", ""),
    "COMPASS_AGENT_TYPE": "claude-code-compass-dialog",
    "PYTHONIOENCODING": "utf-8",
}

INIT_REQ = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "smoke", "version": "0.0.1"},
    },
}


def main() -> int:
    print(f"spawning: python {SCRIPT}")
    p = subprocess.Popen(
        ["python", SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=ENV,
        text=False,  # bytes mode
    )
    # send initialize
    payload = (json.dumps(INIT_REQ) + "\n").encode("utf-8")
    print(f"send: {payload!r}")
    p.stdin.write(payload)
    p.stdin.flush()
    # read stdout with 5s timeout
    import threading
    out_buf = []
    err_buf = []

    def reader(fh, buf):
        try:
            for line in fh:
                buf.append(line)
        except Exception as e:
            buf.append(f"reader exc: {e!r}".encode())

    t_out = threading.Thread(target=reader, args=(p.stdout, out_buf), daemon=True)
    t_err = threading.Thread(target=reader, args=(p.stderr, err_buf), daemon=True)
    t_out.start()
    t_err.start()
    time.sleep(5)
    print("--- after 5s ---")
    print(f"poll: {p.poll()}  (None = still running)")
    print(f"stdout lines: {len(out_buf)}")
    for ln in out_buf[:10]:
        print(f"  STDOUT: {ln!r}")
    print(f"stderr lines: {len(err_buf)}")
    for ln in err_buf[:10]:
        print(f"  STDERR: {ln!r}")
    # cleanup
    try:
        p.terminate()
        p.wait(timeout=2)
    except Exception:
        p.kill()
    return 0 if out_buf else 1


if __name__ == "__main__":
    sys.exit(main())
