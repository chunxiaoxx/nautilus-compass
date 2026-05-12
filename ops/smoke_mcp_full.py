#!/usr/bin/env python3
"""Full MCP lifecycle smoke · initialize + notifications/initialized + tools/list.

Catches the actual failure point that makes Claude Code give up.
"""
import json
import os
import subprocess
import sys
import time
import threading


SCRIPT = r"C:\Users\chunx\.claude\plugins\nautilus-compass\ops\mcp_stdio_to_cloud.py"
ENV = {
    **os.environ,
    "COMPASS_CLOUD_HOST": "127.0.0.1",
    "COMPASS_CLOUD_PORT": "9877",
    "COMPASS_CLOUD_TOKEN": "cmp_claude_code_compass_dialog_58f2e85353fa90b0500e84d6880a1fc0",
    "COMPASS_AGENT_TYPE": "claude-code-compass-dialog",
    "PYTHONIOENCODING": "utf-8",
}

MSGS = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "claude-code", "version": "2.1.139"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
    {"jsonrpc": "2.0", "id": 4, "method": "prompts/list", "params": {}},
    {"jsonrpc": "2.0", "id": 5, "method": "resources/templates/list", "params": {}},
]


def main() -> int:
    p = subprocess.Popen(
        ["python", SCRIPT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=ENV, text=False,
    )
    out_buf, err_buf = [], []

    def reader(fh, buf):
        for line in fh:
            buf.append(line)

    threading.Thread(target=reader, args=(p.stdout, out_buf), daemon=True).start()
    threading.Thread(target=reader, args=(p.stderr, err_buf), daemon=True).start()

    for m in MSGS:
        payload = (json.dumps(m) + "\n").encode("utf-8")
        print(f"---SEND id={m.get('id', 'notify')}---")
        p.stdin.write(payload)
        p.stdin.flush()
        time.sleep(1.5)

    time.sleep(2)
    print(f"\n--- after 8s ---")
    print(f"process poll: {p.poll()}  (None = running · int = exit code)")
    print(f"\nSTDOUT ({len(out_buf)} lines):")
    for i, ln in enumerate(out_buf):
        s = ln.decode("utf-8", errors="replace").rstrip()
        # truncate huge tool lists
        if len(s) > 400:
            s = s[:200] + " ...(truncated " + str(len(s)) + " chars total)..."
        print(f"  [{i}] {s}")
    print(f"\nSTDERR ({len(err_buf)} lines):")
    for ln in err_buf:
        print(f"  {ln.decode('utf-8', errors='replace').rstrip()}")
    try:
        p.terminate()
        p.wait(timeout=2)
    except Exception:
        p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
