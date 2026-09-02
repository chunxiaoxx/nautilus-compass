"""Task 2(2026-09-02 契约迁移版)· TCP server wire 帧剥除顶层 `_eid`。

Boots a real mcp_server subprocess on a loopback port in dev/no-auth mode
(``token_table=None``), drives a raw socket through ``initialize`` + a couple
of simple methods, and asserts every server→client frame carries **no**
top-level ``_eid`` —— f01f9f0(8/24)把"带 _eid"改为"剥除":协议外顶层字段
会让 CC 2.1 严格客户端握手即弃连。EventStore 内部仍记单调 eid,
resume 回放的帧带原 _eid(test_resume_handshake 覆盖)。
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

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def _req(msg_id, method, params=None):
    m = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        m["params"] = params
    return m


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _send_recv(sock: socket.socket, msg: dict, timeout: float = 3.0) -> dict:
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    sock.settimeout(timeout)
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    line, _, _ = buf.partition(b"\n")
    return json.loads(line.decode("utf-8"))


@contextlib.contextmanager
def _tcp_server():
    """Dev/no-auth TCP server (token_table=None) on an ephemeral port."""
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
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
        assert ready, "TCP server did not announce readiness"
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_tcp_server_wire_frames_strip_eid():
    """2026-09-02 契约迁移:wire 帧**不带**顶层 `_eid`(f01f9f0,防 CC 2.1 严格
    客户端握手弃连——这是 8/24 弃连 bug 的根因)。内部 EventStore 仍记单调 eid
    供 resume 回放(由 test_resume_handshake 覆盖:replay 帧带原 _eid 升序)。"""
    with _tcp_server() as port:
        s = socket.socket(); s.connect(("127.0.0.1", port))
        try:
            frames = [
                _send_recv(s, _req(1, "initialize", {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "t", "version": "0"},
                })),
                _send_recv(s, _req(2, "ping")),
                _send_recv(s, _req(3, "tools/list")),
            ]
        finally:
            s.close()

        # 防弃连防线:任何 wire 帧都不得携带协议外顶层 `_eid`。
        for fr in frames:
            assert "_eid" not in fr, f"protocol-foreign _eid leaked to wire: {fr}"

        # 基本健全:JSON-RPC id 原样回、initialize 有 result。
        assert frames[0].get("id") == 1 and "result" in frames[0]
        assert frames[1].get("id") == 2
        assert frames[2].get("id") == 3
