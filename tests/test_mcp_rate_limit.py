"""Per-token rate limit tests · v1.0 (Task #51).

RateBucket unit math + handle_message dispatch gate + token-file schema
+ --rate-limit flag parser + one end-to-end TCP flood test.
"""
from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import mcp_server  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_buckets():
    mcp_server._rate_clear()
    yield
    mcp_server._rate_clear()


# ─── RateBucket math ──────────────────────────────────────────────


def test_bucket_starts_full():
    b = mcp_server.RateBucket(rps=1.0, burst=5.0)
    snap = b.snapshot()
    assert snap["tokens"] == pytest.approx(5.0)


def test_bucket_drains_and_refills_at_rps():
    t0 = 1000.0
    b = mcp_server.RateBucket(rps=2.0, burst=3.0)
    # Drain all 3 at t0 · 4th call must fail.
    for _ in range(3):
        ok, wait = b.acquire(now=t0)
        assert ok, (ok, wait)
    ok, wait = b.acquire(now=t0)
    assert not ok
    assert wait == pytest.approx(0.5, rel=0.01)  # 1 token / 2 rps
    # Half a second later · exactly 1 token refilled.
    ok, _ = b.acquire(now=t0 + 0.5)
    assert ok
    ok, _ = b.acquire(now=t0 + 0.5)
    assert not ok


def test_bucket_caps_at_burst_no_matter_how_long_idle():
    t0 = 0.0
    b = mcp_server.RateBucket(rps=10.0, burst=4.0)
    # Idle for 1 hour · tokens must still cap at burst, not overflow.
    ok, _ = b.acquire(now=t0 + 3600.0)  # consume 1
    assert ok
    # 3 left · 4th should already fail with cap respected.
    for _ in range(3):
        ok, _ = b.acquire(now=t0 + 3600.0)
        assert ok
    ok, _ = b.acquire(now=t0 + 3600.0)
    assert not ok


def test_bucket_rejects_non_positive_args():
    with pytest.raises(ValueError):
        mcp_server.RateBucket(rps=0, burst=1)
    with pytest.raises(ValueError):
        mcp_server.RateBucket(rps=1, burst=0)


# ─── _parse_rate_flag ────────────────────────────────────────────


def test_parse_rate_flag_basic():
    assert mcp_server._parse_rate_flag("alpha=5/10") == ("alpha", 5.0, 10.0)


@pytest.mark.parametrize("bad", [
    "no-equals", "empty=", "=5/10", "t=5", "t=5/", "t=a/b", "t=0/10", "t=5/-1",
])
def test_parse_rate_flag_rejects_garbage(bad):
    with pytest.raises(ValueError):
        mcp_server._parse_rate_flag(bad)


# ─── handle_message dispatch gate ────────────────────────────────


def test_tools_call_returns_32029_when_bucket_empty():
    # rps=0.001 · 1 token / 1000s · natural per-call latency cannot
    # refill the bucket before the second call arrives, regardless of
    # platform-specific tool slowness (e.g. Windows daemon connect-refused
    # taking ~2s). feedback_log is sub-millisecond + has no external deps,
    # so the test is deterministic on any platform.
    mcp_server._rate_register("spam-tok", rps=0.001, burst=1.0)
    # First call drains bucket.
    reply1 = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "feedback_log",
                    "arguments": {"direction": "good", "reason": "t"}}},
        scopes={"*"}, token="spam-tok",
    )
    assert reply1.get("error", {}).get("code") != -32029  # first pass
    # Second call within same tick is rate-limited.
    reply2 = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "feedback_log",
                    "arguments": {"direction": "good", "reason": "t"}}},
        scopes={"*"}, token="spam-tok",
    )
    assert reply2["error"]["code"] == -32029
    assert "retry in" in reply2["error"]["message"]


def test_rate_limit_applies_to_resources_read():
    mcp_server._rate_register("reader-tok", rps=1.0, burst=1.0)
    # Bad uri · but rate-limit must fire before URI validation for
    # security: don't leak resource existence info to the spammer.
    mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "resources/read",
         "params": {"uri": "compass://session/x/session_y.md"}},
        scopes={"resources.read"}, token="reader-tok",
    )
    reply2 = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "resources/read",
         "params": {"uri": "compass://session/x/session_y.md"}},
        scopes={"resources.read"}, token="reader-tok",
    )
    assert reply2["error"]["code"] == -32029


def test_rate_limit_does_not_gate_ping_or_status():
    mcp_server._rate_register("cheap-tok", rps=0.001, burst=1.0)
    # Drain the bucket so we know it's empty.
    mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 0, "method": "tools/call",
         "params": {"name": "recall", "arguments": {"query": "x"}}},
        scopes={"*"}, token="cheap-tok",
    )
    # ping + server/status must still succeed.
    pong = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
        scopes={"*"}, token="cheap-tok",
    )
    assert pong.get("result") == {}
    status = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "server/status"},
        scopes={"*"}, token="cheap-tok",
    )
    assert "uptime_seconds" in status["result"]


def test_rate_limit_skipped_when_no_bucket_for_token():
    """Tokens without a bucket are unlimited — safe default."""
    for i in range(50):
        reply = mcp_server.handle_message(
            {"jsonrpc": "2.0", "id": i, "method": "tools/call",
             "params": {"name": "recall", "arguments": {"query": "x"}}},
            scopes={"*"}, token="no-bucket-tok",
        )
        assert reply.get("error", {}).get("code") != -32029, i


def test_rate_limit_skipped_when_token_is_none():
    """Stdio / dev mode · no token, no bucket, no limit."""
    for i in range(20):
        reply = mcp_server.handle_message(
            {"jsonrpc": "2.0", "id": i, "method": "tools/call",
             "params": {"name": "recall", "arguments": {"query": "x"}}},
            scopes=None, token=None,
        )
        assert reply.get("error", {}).get("code") != -32029


# ─── token-file schema ──────────────────────────────────────────


def test_token_file_dict_form_registers_bucket(tmp_path):
    f = tmp_path / "tokens.json"
    f.write_text(json.dumps({
        "alpha": {"scopes": ["tools.read"], "rate_limit": {"rps": 3, "burst": 6}},
        "beta":  ["tools.write"],  # legacy form still works
    }), encoding="utf-8")
    table = mcp_server._load_token_table(None, str(f))
    assert table == {"alpha": {"tools.read"}, "beta": {"tools.write"}}
    assert mcp_server._rate_bucket_for("alpha") is not None
    assert mcp_server._rate_bucket_for("beta") is None  # unlimited


def test_token_file_rate_limit_defaults_burst_to_rps(tmp_path):
    f = tmp_path / "tokens.json"
    f.write_text(json.dumps({
        "a": {"scopes": ["*"], "rate_limit": {"rps": 7}},
    }), encoding="utf-8")
    mcp_server._load_token_table(None, str(f))
    b = mcp_server._rate_bucket_for("a")
    assert b.burst == 7.0
    assert b.rps == 7.0


def test_token_file_bad_rate_limit_rejected(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({
        "a": {"scopes": ["*"], "rate_limit": {"burst": 10}},  # missing rps
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="bad rate_limit"):
        mcp_server._load_token_table(None, str(f))


# ─── end-to-end TCP flood ───────────────────────────────────────


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _tcp_server_with_rate_limit(rps: float = 0.1, burst: float = 2.0):
    """Default is deliberately strict (rps=0.1 · 1 token per 10s) so even
    slow handlers can't sneak in a refill between requests."""
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--token", "flood-tok:*",
           "--rate-limit", f"flood-tok={rps}/{burst}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
    deadline = time.time() + 3.0
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if b"listening on" in line:
            ready = True
            break
    try:
        if not ready:
            proc.kill()
            raise RuntimeError("server never ready")
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_tcp_flood_gets_32029_after_burst_exhausted():
    """Raw-socket pipelined flood · guaranteed faster than bucket refill."""
    with _tcp_server_with_rate_limit() as port:
        sock = socket.create_connection(("127.0.0.1", port))
        f = sock.makefile("rwb", buffering=0)
        # initialize
        f.write((json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                             "params": {"authToken": "flood-tok"}}) + "\n").encode())
        f.readline()  # init reply
        # Pipeline 8 requests without waiting for replies · refill can't keep up.
        for i in range(8):
            f.write((json.dumps({"jsonrpc": "2.0", "id": i + 1, "method": "tools/call",
                                 "params": {"name": "recall",
                                            "arguments": {"query": f"q{i}"}}}) + "\n").encode())
        replies = [json.loads(f.readline().decode()) for _ in range(8)]
        sock.close()
        ok_count = sum(1 for r in replies if "result" in r)
        limited = [r for r in replies if r.get("error", {}).get("code") == -32029]
        assert ok_count >= 2, replies  # burst consumed
        assert limited, f"expected some -32029 · got {replies}"
        assert "retry in" in limited[0]["error"]["message"]


def test_tcp_rate_limit_bucket_refills():
    """After sleeping, the bucket must refill and allow fresh calls.

    Uses feedback_log (sub-ms, no daemon) so the flood actually drains
    the bucket — recall takes ~2s on Windows when the daemon is down,
    which would refill the bucket between flood frames and mask the
    test's intent.
    """
    # rps=2 · 0.7s sleep ≈ 1.4 tokens refilled.
    fb_args = {"direction": "good", "reason": "t"}
    with _tcp_server_with_rate_limit(rps=2.0, burst=1.0) as port:
        sock = socket.create_connection(("127.0.0.1", port))
        f = sock.makefile("rwb", buffering=0)
        f.write((json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                             "params": {"authToken": "flood-tok"}}) + "\n").encode())
        f.readline()
        # Exhaust the bucket with a pipelined flood.
        for i in range(6):
            f.write((json.dumps({"jsonrpc": "2.0", "id": i + 1, "method": "tools/call",
                                 "params": {"name": "feedback_log",
                                            "arguments": fb_args}}) + "\n").encode())
        drained = [json.loads(f.readline().decode()) for _ in range(6)]
        assert any(r.get("error", {}).get("code") == -32029 for r in drained)
        # Sleep enough for bucket to refill (rps=2 · 0.8s ≈ 1.6 tokens).
        time.sleep(0.8)
        f.write((json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/call",
                             "params": {"name": "feedback_log",
                                        "arguments": fb_args}}) + "\n").encode())
        reply = json.loads(f.readline().decode())
        sock.close()
        assert "result" in reply, reply
