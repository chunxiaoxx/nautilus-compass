"""MCP resources/* tests · v1.0 (Task #48).

Covers server dispatch (in-process), full round-trip via MCPClient, and
path-traversal rejection.
"""
from __future__ import annotations

import contextlib
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
from mcp_client import MCPClient, MCPClientError  # noqa: E402


# ─── fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def fake_projects_root(tmp_path, monkeypatch):
    """Swap PROJECTS_ROOT to a tmp dir with two projects and some sessions."""
    proj_a = tmp_path / "proj-a" / "memory"
    proj_a.mkdir(parents=True)
    proj_b = tmp_path / "proj-b" / "memory"
    proj_b.mkdir(parents=True)

    (proj_a / "session_20260101-0900_first.md").write_text(
        "---\nname: first\ndrift: green\n---\nbody A", encoding="utf-8")
    time.sleep(0.01)  # ensure distinct mtimes
    (proj_a / "session_20260101-1000_second.md").write_text(
        "---\nname: second\n---\nbody B", encoding="utf-8")
    time.sleep(0.01)
    (proj_b / "session_20260101-1100_third.md").write_text(
        "body C", encoding="utf-8")
    # non-session file should be ignored
    (proj_a / "README.md").write_text("skip me", encoding="utf-8")

    monkeypatch.setattr(mcp_server, "PROJECTS_ROOT", tmp_path)
    return tmp_path


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ─── in-process server dispatch ───────────────────────────────────


def test_initialize_advertises_resources_capability():
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    })
    assert "resources" in reply["result"]["capabilities"]


def test_resources_list_returns_session_files(fake_projects_root):
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {},
    })
    items = reply["result"]["resources"]
    assert len(items) == 3
    # mtime-desc: third (proj-b) first, then second, then first.
    assert items[0]["uri"].endswith("proj-b/session_20260101-1100_third.md")
    assert items[1]["uri"].endswith("proj-a/session_20260101-1000_second.md")
    assert items[2]["uri"].endswith("proj-a/session_20260101-0900_first.md")
    for r in items:
        assert r["uri"].startswith("compass://session/")
        assert r["mimeType"] == "text/markdown"
        assert "mtime=" in r["description"]


def test_resources_list_honors_limit(fake_projects_root):
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 3, "method": "resources/list",
        "params": {"limit": 2},
    })
    assert len(reply["result"]["resources"]) == 2


def test_resources_read_returns_body(fake_projects_root):
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 4, "method": "resources/read",
        "params": {"uri": "compass://session/proj-a/session_20260101-0900_first.md"},
    })
    content = reply["result"]["contents"][0]
    assert content["mimeType"] == "text/markdown"
    assert "body A" in content["text"]
    assert "name: first" in content["text"]


def test_resources_read_requires_uri():
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {},
    })
    assert reply["error"]["code"] == -32602


@pytest.mark.parametrize("bad_uri", [
    "http://example.com/session.md",
    "compass://session/proj-a/../../../etc/passwd",
    "compass://session/proj-a/../README.md",
    "compass://session/proj-a/session_foo.md/extra",
    "compass://session/proj-a/notes.txt",          # wrong extension
    "compass://session/proj-a/readme.md",          # missing session_ prefix
    "compass://session/only-one-part",
])
def test_resources_read_rejects_bad_uris(fake_projects_root, bad_uri):
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 6, "method": "resources/read",
        "params": {"uri": bad_uri},
    })
    assert "error" in reply, reply
    assert reply["error"]["code"] == -32602, reply


def test_resources_read_missing_file_returns_32002(fake_projects_root):
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 7, "method": "resources/read",
        "params": {"uri": "compass://session/proj-a/session_99999999-9999_ghost.md"},
    })
    assert reply["error"]["code"] == -32002


def test_resources_read_truncates_large_files(tmp_path, monkeypatch):
    proj = tmp_path / "big-proj" / "memory"
    proj.mkdir(parents=True)
    huge = "X" * (mcp_server.RESOURCE_MAX_BYTES + 1024)
    (proj / "session_big.md").write_text(huge, encoding="utf-8")
    monkeypatch.setattr(mcp_server, "PROJECTS_ROOT", tmp_path)
    reply = mcp_server.handle_message({
        "jsonrpc": "2.0", "id": 8, "method": "resources/read",
        "params": {"uri": "compass://session/big-proj/session_big.md"},
    })
    text = reply["result"]["contents"][0]["text"]
    assert "truncated" in text
    assert len(text) <= mcp_server.RESOURCE_MAX_BYTES + 200  # + truncation marker


# ─── end-to-end via MCPClient over TCP ────────────────────────────


@contextlib.contextmanager
def _tcp_server_with_fake_root(fake_root: Path):
    """Spin a real mcp_server subprocess that uses a fake PROJECTS_ROOT via env."""
    port = _free_port()
    env = {**os.environ, "PYTHONUTF8": "1",
           "COMPASS_PROJECTS_ROOT_OVERRIDE": str(fake_root)}
    # Shim: have the subprocess pick up the override before starting.
    shim = (
        "import os, sys; "
        "sys.path.insert(0, r'" + str(PLUGIN_ROOT) + "'); "
        "import mcp_server; "
        "from pathlib import Path; "
        "mcp_server.PROJECTS_ROOT = Path(os.environ['COMPASS_PROJECTS_ROOT_OVERRIDE']); "
        "sys.argv = ['mcp_server.py','--transport','tcp','--host','127.0.0.1','--port','" + str(port) + "']; "
        "mcp_server.main() if hasattr(mcp_server,'main') else exec(open(r'" + str(PLUGIN_ROOT / 'mcp_server.py') + "').read(), {'__name__':'__main__'})"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", shim],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )
    deadline = time.time() + 5.0
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if b"listening on" in line:
            ready = True
            break
    try:
        if not ready:
            out, err = proc.communicate(timeout=1)
            proc.kill()
            raise RuntimeError(f"server never ready · stderr={err.decode('utf-8', 'replace')}")
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_client_list_and_read_roundtrip(tmp_path):
    proj = tmp_path / "roundtrip-proj" / "memory"
    proj.mkdir(parents=True)
    (proj / "session_20260101-0100_alpha.md").write_text("alpha body", encoding="utf-8")
    (proj / "session_20260101-0200_beta.md").write_text("beta body", encoding="utf-8")

    with _tcp_server_with_fake_root(tmp_path) as port:
        with MCPClient(port=port) as c:
            resources = c.list_resources()
            assert len(resources) == 2
            uri_alpha = next(r["uri"] for r in resources if "alpha" in r["uri"])
            content = c.read_resource(uri_alpha)
            assert content["text"].strip() == "alpha body"
            assert content["mimeType"] == "text/markdown"


def test_client_read_bad_uri_raises(tmp_path):
    (tmp_path / "empty-proj" / "memory").mkdir(parents=True)
    with _tcp_server_with_fake_root(tmp_path) as port:
        with MCPClient(port=port) as c:
            with pytest.raises(MCPClientError) as ei:
                c.read_resource("compass://session/../escape/session_x.md")
            assert "-32602" in str(ei.value) or "traversal" in str(ei.value).lower() or \
                   "project escapes" in str(ei.value)
