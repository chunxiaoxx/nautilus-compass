"""R453 · daemon rerank remote 分支测试(feat/rerank-remote,不部署)。

判据:
- G1 remote 成功: fake server 返回 scores → 按 scores 重排,ok 路径
- G2 remote 业务失败(ok:false) → 返回 None → 上层回退 dense
- G3 remote 不可达 → None 回退
- G4 env 未配置 → 不发起连接(计数 0)
- G5 超时 → None 回退(fake server 吊住不回)
协议: {"action":"rerank","query":...,"docs":[...],"token":...} → {"ok":true,"scores":[...]}
"""
import json
import socket
import threading
import time
from pathlib import Path

import pytest

import daemon

FAKE_TOKEN_DIR = None


class FakeServer(threading.Thread):
    """预设响应的假 rerank server。mode: ok|bad|hang"""

    def __init__(self, mode: str):
        super().__init__(daemon=True)
        self.mode = mode
        self.conn_count = 0
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", 0))
        self.port = self.srv.getsockname()[1]
        self.srv.listen(4)
        self.srv.settimeout(8)

    def run(self):
        while True:
            try:
                conn, _ = self.srv.accept()
            except OSError:
                return
            self.conn_count += 1
            threading.Thread(target=self.serve, args=(conn,), daemon=True).start()

    def serve(self, conn: socket.socket):
        try:
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buf += chunk
            if self.mode == "ok":
                n = len(json.loads(buf)["docs"])
                conn.sendall(json.dumps({"ok": True, "scores": [float(n - i) for i in range(n)]}).encode() + b"\n")
            elif self.mode == "bad":
                conn.sendall(json.dumps({"ok": False, "error": "boom"}).encode() + b"\n")
            elif self.mode == "hang":
                time.sleep(30)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


@pytest.fixture()
def token_file(tmp_path, monkeypatch):
    tf = tmp_path / "rr_token"
    tf.write_text("test-token")
    monkeypatch.setattr(daemon, "_RERANK_TOKEN_FILE", tf)
    return tf


def test_remote_success(token_file, monkeypatch):
    srv = FakeServer("ok")
    srv.start()
    monkeypatch.setattr(daemon, "_RERANK_REMOTE_ADDR", ("127.0.0.1", srv.port))
    out, ok = daemon._rerank_via_remote("q", ["docA", "docB", "docC"])
    assert ok is True and out is not None and len(out) == 3
    assert out == sorted(out, reverse=True)  # G1 scores 降序返回


def test_remote_bad_fallback(token_file, monkeypatch):
    srv = FakeServer("bad")
    srv.start()
    monkeypatch.setattr(daemon, "_RERANK_REMOTE_ADDR", ("127.0.0.1", srv.port))
    out, ok = daemon._rerank_via_remote("q", ["a", "b"])
    assert out is None and ok is False  # G2


def test_remote_unreachable(token_file, monkeypatch):
    # 占一个确定无人监听的端口
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    dead_port = s.getsockname()[1]
    s.close()
    monkeypatch.setattr(daemon, "_RERANK_REMOTE_ADDR", ("127.0.0.1", dead_port))
    out, ok = daemon._rerank_via_remote("q", ["a"])
    assert out is None and ok is False  # G3


def test_env_off_no_connection(monkeypatch):
    calls = []
    orig = socket.create_connection

    def spy(*a, **k):
        calls.append(1)
        return orig(*a, **k)

    monkeypatch.setattr(socket, "create_connection", spy)
    monkeypatch.setattr(daemon, "_RERANK_REMOTE_ADDR", None)
    out, ok = daemon._rerank_via_remote("q", ["a"])
    assert out is None and ok is False
    assert calls == []  # G4 未配置零连接


def test_rerank_top_remote_reorders(token_file, monkeypatch):
    srv = FakeServer("ok")
    srv.start()
    monkeypatch.setattr(daemon, "_RERANK_REMOTE_ADDR", ("127.0.0.1", srv.port))
    monkeypatch.setattr(daemon, "_PROD_RERANK_USE", True)
    top = [(0.9, {"name": "a.md", "embed_text": "aaa"}),
           (0.8, {"name": "b.md", "embed_text": "bbb"})]
    out = daemon._rerank_top("query", list(top), 2)
    assert [e["name"] for _s, e in out] == ["a.md", "b.md"]  # fake scores 按 index 递减
