"""Automation health report — the self-attestation daily line (三支柱·自证化).

One-line output for the daily report: every standing automation's latest
success signal + recall consumption count. Probes report UNKNOWN when a
source is missing — never a guessed default (probe-key lesson 2026-09-02).
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
CANDIDATE_STATES = [
    ROOT / "ops" / "wd_auth_state.txt",
    ROOT / "wd_auth_state.txt",
    Path.home() / ".claude" / "plugins" / "nautilus-compass" / "wd_auth_state.txt",
]


def daemon_ping() -> str:
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect(("127.0.0.1", 9876))
        s.sendall(json.dumps({"action": "ping"}).encode() + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        r = json.loads(buf.decode())
        return f"UP(pid={r.get('pid', '?')})" if r.get("pong") else "UNKNOWN"
    except Exception:
        return "DOWN"


def watchdog_state() -> str:
    for p in CANDIDATE_STATES:
        if p.exists():
            age = time.time() - p.stat().st_mtime
            return f"last_run={age/60:.0f}min_ago"
    return "state_file:UNKNOWN"


def watchdog_task() -> str:
    try:
        out = subprocess.run(
            ["schtasks", "/Query", "/TN", "compass-watchdog"],
            capture_output=True, text=True, timeout=15)
        return "task:OK" if out.returncode == 0 else "task:ABSENT"
    except Exception:
        return "task:UNKNOWN"


def heartbeat_recent() -> str:
    hb = Path.home() / ".claude" / ".cache" / "goalmode_heartbeat.log"
    if not hb.exists():
        return "log:ABSENT"
    return f"last={(time.time()-hb.stat().st_mtime)/3600:.1f}h_ago"


def recall_count_24h() -> str:
    log = (Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "daemon.log")
    if not log.exists():
        return "UNKNOWN"
    cutoff = time.time() - 86400
    try:
        with log.open(encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 2_000_000))
            tail = f.read()
    except OSError:
        return "UNKNOWN"
    n = len(re.findall(r"recall", tail))
    return f"~{n}"


def main() -> None:
    print(" | ".join([
        "AUTOMATION-REPORT",
        f"daemon9876:{daemon_ping()}",
        f"watchdog:{watchdog_state()} {watchdog_task()}",
        f"heartbeat:{heartbeat_recent()}",
        f"recall24h:{recall_count_24h()}",
    ]))


if __name__ == "__main__":
    main()
