"""test_daemon_status.py · TDD for /status endpoint (v2.1.0+).

Integration test against running daemon on 127.0.0.1:9876.
Validates required fields per plan_compass_internal_ux_stage12_implementation.md Task 1.
"""
import json
import socket


def _send(action: str, timeout: float = 10.0) -> dict:
    s = socket.create_connection(("127.0.0.1", 9876), timeout=timeout)
    try:
        s.sendall((json.dumps({"action": action}) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            c = s.recv(65536)
            if not c:
                break
            buf += c
    finally:
        s.close()
    return json.loads(buf.split(b"\n", 1)[0])


def test_daemon_status_returns_required_fields():
    r = _send("status")
    assert r.get("ok") is True or r.get("ts") is not None, f"missing ok/ts: {r}"
    assert "uptime_s" in r, f"missing uptime_s: {r}"
    assert "cpu_pct" in r, f"missing cpu_pct: {r}"
    assert "recall" in r, f"missing recall: {r}"
    assert "p9_cache" in r["recall"], f"missing recall.p9_cache: {r}"
    assert "inotify" in r["recall"], f"missing recall.inotify: {r}"


def test_daemon_ping_still_works():
    r = _send("ping")
    assert r.get("ok") is True
    assert r.get("pong") is True
