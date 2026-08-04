#!/usr/bin/env python3
"""Verify bridge heartbeat keeps TCP alive across 3-min idle.

Without heartbeat: cloud closes at 2-5min · bridge sees <eof> · MCP × failed.
With heartbeat (60s newline): TCP should survive any practical idle.

Spawns the bridge as subprocess (matching Claude Code's wire), sends init,
idles 3 minutes, then sends tools/list. Pass = both replies arrive cleanly.
"""
import json
import os
import subprocess
import sys
import threading
import time


SCRIPT = r"C:\Users\chunx\.claude\plugins\nautilus-compass\ops\mcp_stdio_to_cloud.py"
ENV = {
    **os.environ,
    "COMPASS_CLOUD_HOST": "127.0.0.1",
    "COMPASS_CLOUD_PORT": "9877",
    "COMPASS_CLOUD_TOKEN": os.environ.get("COMPASS_CLOUD_TOKEN", ""),
    "COMPASS_AGENT_TYPE": "claude-code-smoke-idle-3min",
    "PYTHONIOENCODING": "utf-8",
}

IDLE_SECONDS = 180  # 3 min · longer than known 2-5 min cloud close


def main() -> int:
    p = subprocess.Popen(
        ["python", SCRIPT],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=ENV, text=False,
    )
    out_buf = []
    err_buf = []

    def reader(fh, buf):
        for line in fh:
            buf.append(line)

    threading.Thread(target=reader, args=(p.stdout, out_buf), daemon=True).start()
    threading.Thread(target=reader, args=(p.stderr, err_buf), daemon=True).start()

    def send(m):
        payload = (json.dumps(m) + "\n").encode("utf-8")
        print(f"send id={m.get('id', 'notify')}: {m['method']}", flush=True)
        p.stdin.write(payload)
        p.stdin.flush()

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "idle-smoke", "version": "0.0.1"}}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    time.sleep(3)

    pre_count = len(out_buf)
    print(f"pre-idle stdout lines: {pre_count}")
    if p.poll() is not None:
        print(f"bridge died early · exit code {p.poll()}")
        for ln in err_buf[-5:]:
            print(f"  STDERR: {ln.decode('utf-8', errors='replace').rstrip()}")
        return 1

    print(f"idling {IDLE_SECONDS}s (heartbeat should tick every 60s) ...", flush=True)
    t0 = time.time()
    while time.time() - t0 < IDLE_SECONDS:
        time.sleep(15)
        elapsed = int(time.time() - t0)
        alive = p.poll() is None
        print(f"  t={elapsed:3d}s · process alive={alive}", flush=True)
        if not alive:
            print(f"  ✗ bridge died during idle at t={elapsed}s")
            for ln in err_buf[-5:]:
                print(f"    STDERR: {ln.decode('utf-8', errors='replace').rstrip()}")
            return 1

    print(f"\npost-idle test · tools/list again ...", flush=True)
    send({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
    time.sleep(5)

    new_replies = len(out_buf) - pre_count
    print(f"new stdout replies after idle + retry: {new_replies}")
    last3 = out_buf[-3:] if len(out_buf) >= 3 else out_buf
    for ln in last3:
        s = ln.decode("utf-8", errors="replace").rstrip()
        print(f"  STDOUT: {s[:120]}")

    success = new_replies >= 1 and any(b'"id": 3' in x for x in out_buf)
    print(f"\nresult: {'PASS' if success else 'FAIL'} · idle {IDLE_SECONDS}s · heartbeat {'kept conn alive' if success else 'did not save conn'}")

    try:
        p.terminate()
        p.wait(timeout=2)
    except Exception:
        p.kill()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
