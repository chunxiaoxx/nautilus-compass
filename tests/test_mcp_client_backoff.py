"""MCPClient -32029 auto-backoff tests · v1.0 (Task #52)."""
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

from mcp_client import MCPClient, MCPClientError, _parse_retry_after  # noqa: E402


# ─── _parse_retry_after ──────────────────────────────────────────


@pytest.mark.parametrize("msg,expected", [
    ("rate limited · retry in 0.73s", 0.73),
    ("retry in 5s", 5.0),
    ("retry in  12.5s", 12.5),
    ("Retry In 0.1S", 0.1),
    ("no retry info here", 1.0),  # fallback default
    ("", 1.0),
    ("retry in abc s", 1.0),
])
def test_parse_retry_after(msg, expected):
    assert _parse_retry_after(msg) == pytest.approx(expected, rel=1e-3)


def test_parse_retry_after_custom_default():
    assert _parse_retry_after("nothing", default=3.5) == 3.5


def test_parse_retry_after_clamps_negative_to_zero():
    # Regex won't match a minus sign · fallback kicks in.
    assert _parse_retry_after("retry in -1s") == 1.0


# ─── Fake RPC · unit-test the _call branch without a real server ─


class _FakeSock:
    """Pairs (canned_replies_per_send) mocked at the socket layer.

    Each send advances one reply from the queue. `sendall` records the
    outgoing JSON so we can assert retries replay the same payload.
    """

    def __init__(self, replies: list[dict]) -> None:
        self.replies = list(replies)
        self.sent: list[bytes] = []
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, n: int) -> bytes:
        if not self.replies:
            return b""
        r = self.replies.pop(0)
        return (json.dumps(r) + "\n").encode()

    def settimeout(self, *_a, **_kw) -> None:
        pass

    def close(self) -> None:
        self.closed = True


def _client_with_fake(replies: list[dict], **kwargs) -> MCPClient:
    c = MCPClient(host="127.0.0.1", port=0, token=None, **kwargs)
    c._sock = _FakeSock(replies)  # type: ignore[assignment]
    return c


def _ok(rid: int) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": {"ok": True}}


def _rate(rid: int, after: float = 0.05) -> dict:
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32029, "message": f"rate limited · retry in {after}s"}}


def _other_err(rid: int) -> dict:
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32001, "message": "unauthorized"}}


def test_zero_retries_default_raises_on_32029():
    c = _client_with_fake([_rate(1)])
    with pytest.raises(MCPClientError) as ei:
        c._call("tools/call", {"name": "recall", "arguments": {}})
    assert "-32029" in str(ei.value) or "rate limited" in str(ei.value)


def test_with_retries_sleeps_then_succeeds():
    c = _client_with_fake([_rate(1, after=0.02), _ok(2)],
                          rate_limit_retries=2, rate_limit_multiplier=1.0)
    t0 = time.monotonic()
    result = c._call("tools/call", {"name": "recall", "arguments": {}})
    elapsed = time.monotonic() - t0
    assert result == {"ok": True}
    assert c.rate_limit_waits == 1
    assert c.last_rate_limit_wait_s == pytest.approx(0.02, abs=0.01)
    # Slept ≥ parsed wait · with buffer.
    assert elapsed >= 0.018


def test_with_retries_exhausts_and_raises():
    """Three -32029 replies in a row · max 2 retries · the third surfaces."""
    c = _client_with_fake([_rate(1, 0.01), _rate(2, 0.01), _rate(3, 0.01)],
                          rate_limit_retries=2, rate_limit_multiplier=1.0)
    with pytest.raises(MCPClientError):
        c._call("tools/call", {"name": "recall", "arguments": {}})
    assert c.rate_limit_waits == 2


def test_non_rate_errors_pass_through_unchanged():
    c = _client_with_fake([_other_err(1)], rate_limit_retries=5)
    with pytest.raises(MCPClientError) as ei:
        c._call("tools/call", {"name": "recall", "arguments": {}})
    assert "-32001" in str(ei.value) or "unauthorized" in str(ei.value)
    assert c.rate_limit_waits == 0


def test_multiplier_extends_wait():
    c = _client_with_fake([_rate(1, after=0.02), _ok(2)],
                          rate_limit_retries=1, rate_limit_multiplier=3.0)
    c._call("tools/call", {"name": "recall", "arguments": {}})
    assert c.last_rate_limit_wait_s == pytest.approx(0.06, abs=0.005)


# ─── End-to-end TCP: real server + real rate-limit ──────────────


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _tcp_server_strict():
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--token", "back-tok:*",
           "--rate-limit", "back-tok=0.5/1"]  # 0.5 rps · refill every 2s · burst 1
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


def test_tcp_client_transparently_retries_when_rate_limited():
    """First call drains the 1-burst bucket · second call would 32029 · with
    rate_limit_retries=3 the client waits and succeeds.

    feedback_log instead of recall · see no_retry sibling for rationale.
    """
    fb = {"direction": "good", "reason": "t"}
    with _tcp_server_strict() as port:
        with MCPClient(port=port, token="back-tok",
                       rate_limit_retries=3, rate_limit_multiplier=1.1) as c:
            c.call_tool("feedback_log", fb)
            # This one would normally raise -32029 · instead we sleep + retry.
            result = c.call_tool("feedback_log", fb)
            assert isinstance(result, dict)
            assert c.rate_limit_waits >= 1


def test_tcp_client_no_retry_raises_on_rate_limit():
    """Default rate_limit_retries=0 keeps the old strict behaviour.

    Uses feedback_log (sub-ms, no daemon) so the bucket genuinely
    drains between back-to-back calls — recall blocks ~2s on Windows
    when the BGE daemon is down, which would refill the rps=0.5 bucket
    and mask the rate-limit denial.
    """
    fb = {"direction": "good", "reason": "t"}
    with _tcp_server_strict() as port:
        with MCPClient(port=port, token="back-tok") as c:
            c.call_tool("feedback_log", fb)  # drains bucket
            with pytest.raises(MCPClientError) as ei:
                c.call_tool("feedback_log", fb)
            assert "-32029" in str(ei.value) or "rate limited" in str(ei.value)
            assert c.rate_limit_waits == 0
