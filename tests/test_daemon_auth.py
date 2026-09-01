#!/usr/bin/env python3
"""v3.0.10 · daemon 9876 token 鉴权 · TDD。

背景:本地 daemon 经 -R 反向隧道可被云端进程触达(stop_hook.py 注释实证),
原零鉴权 = 隧道域内任何进程可 recall/ingest/shutdown。本测试钉死:
  · token 文件自动生成(64 hex, 0600)与复用
  · ping 免鉴权(探活依赖: daemon_start.ps1/sh 的 spawn 判定走 ping)
  · 其余 action(含 status/shutdown)无 token / 错 token 一律 auth_failed
  · shutdown 无 token 被拒(不测带 token 的 shutdown —— handler 会 os._exit 杀测试进程)
"""
from __future__ import annotations

import json
import socket
import threading
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402


@pytest.fixture
def tokfile(tmp_path: Path, monkeypatch):
    p = tmp_path / "compass_daemon_token"
    monkeypatch.setenv("COMPASS_DAEMON_TOKEN_FILE", str(p))
    monkeypatch.setattr(zmd, "_DAEMON_TOKEN_CACHE", None)
    yield p
    monkeypatch.setattr(zmd, "_DAEMON_TOKEN_CACHE", None)


def _roundtrip(payload: dict) -> dict:
    """Feed one JSON line to handle_conn over a socketpair, return response."""
    server, client = socket.socketpair()
    t = threading.Thread(target=zmd.handle_conn, args=(server,), daemon=True)
    t.start()
    client.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    client.settimeout(8)
    buf = b""
    while b"\n" not in buf:
        c = client.recv(65536)
        if not c:
            break
        buf += c
    client.close()
    server.close()
    t.join(timeout=8)
    return json.loads(buf.split(b"\n")[0].decode("utf-8"))


def test_token_autocreated_random_hex(tokfile):
    tok = zmd._daemon_token()
    assert len(tok) == 64 and int(tok, 16) >= 0        # 64 hex chars
    assert tokfile.exists()
    assert tokfile.read_text(encoding="utf-8").strip() == tok


def test_token_reused_existing_file(tokfile, monkeypatch):
    tokfile.write_text("ab" * 32, encoding="utf-8")
    monkeypatch.setattr(zmd, "_DAEMON_TOKEN_CACHE", None)
    assert zmd._daemon_token() == "ab" * 32


def test_auth_ok_match_and_mismatch(tokfile):
    good = zmd._daemon_token()
    assert zmd._auth_ok({"token": good}) is True
    assert zmd._auth_ok({"token": "0" * 64}) is False
    assert zmd._auth_ok({}) is False
    assert zmd._auth_ok({"token": ""}) is False


def test_roundtrip_ping_no_token_ok(tokfile):
    r = _roundtrip({"action": "ping"})
    assert r.get("pong") is True


def test_roundtrip_status_without_token_denied(tokfile):
    r = _roundtrip({"action": "status"})
    assert r.get("ok") is False and r.get("error") == "auth_failed"


def test_roundtrip_status_wrong_token_denied(tokfile):
    r = _roundtrip({"action": "status", "token": "0" * 64})
    assert r.get("ok") is False and r.get("error") == "auth_failed"


def test_roundtrip_status_with_token_allowed(tokfile):
    r = _roundtrip({"action": "status", "token": zmd._daemon_token()})
    assert r.get("ok") is True


def test_shutdown_without_token_denied(tokfile):
    # 故意不测带 token 的 shutdown:handle_conn 会 os._exit(0) 杀掉测试进程
    r = _roundtrip({"action": "shutdown"})
    assert r.get("ok") is False and r.get("error") == "auth_failed"
