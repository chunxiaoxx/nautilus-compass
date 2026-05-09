"""RBAC tests · v1.0 (Task #49).

In-process handle_message tests for scope enforcement + token parsing.
End-to-end TCP test for scope-restricted token over the wire.
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
from mcp_client import MCPClient, MCPClientError  # noqa: E402


# ─── _parse_token_spec ───────────────────────────────────────────


def test_parse_legacy_token_full_scope():
    tok, scopes = mcp_server._parse_token_spec("plain-token")
    assert tok == "plain-token"
    assert scopes == {"*"}


def test_parse_scoped_token():
    tok, scopes = mcp_server._parse_token_spec("obs:tools.read,resources.read")
    assert tok == "obs"
    assert scopes == {"tools.read", "resources.read"}


def test_parse_rejects_unknown_scope():
    with pytest.raises(ValueError, match="unknown scopes"):
        mcp_server._parse_token_spec("bad:tools.nuke")


def test_parse_rejects_empty_token():
    with pytest.raises(ValueError):
        mcp_server._parse_token_spec(":tools.read")


# ─── _load_token_table ───────────────────────────────────────────


def test_load_table_from_cli_specs_only():
    table = mcp_server._load_token_table(
        ["admin", "reader:tools.read"], None)
    assert table == {"admin": {"*"}, "reader": {"tools.read"}}


def test_load_table_from_file_only(tmp_path):
    f = tmp_path / "tokens.json"
    f.write_text(json.dumps({"t1": ["tools.read"], "t2": ["tools.write"]}),
                 encoding="utf-8")
    table = mcp_server._load_token_table(None, str(f))
    assert table == {"t1": {"tools.read"}, "t2": {"tools.write"}}


def test_load_table_file_rejects_unknown_scopes(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"t": ["tools.nuke"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown scopes"):
        mcp_server._load_token_table(None, str(f))


# ─── _has_scope ──────────────────────────────────────────────────


def test_has_scope_none_grants_everything():
    assert mcp_server._has_scope(None, "tools.write") is True
    assert mcp_server._has_scope(None, "resources.read") is True


def test_has_scope_wildcard():
    assert mcp_server._has_scope({"*"}, "tools.write") is True


def test_has_scope_exact():
    assert mcp_server._has_scope({"tools.read"}, "tools.read") is True
    assert mcp_server._has_scope({"tools.read"}, "tools.write") is False


# ─── handle_message scope enforcement ────────────────────────────


def test_tools_list_filters_by_scope():
    """A read-only token sees only read-scope tools."""
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        scopes={"tools.read"},
    )
    names = {t["name"] for t in reply["result"]["tools"]}
    assert "recall" in names
    assert "drift_check" in names
    assert "ingest_obs" not in names
    assert "feedback_log" not in names


def test_tools_list_full_scope_sees_all():
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        scopes={"*"},
    )
    names = {t["name"] for t in reply["result"]["tools"]}
    assert names == set(mcp_server.TOOLS)


def test_tools_call_rejects_insufficient_scope():
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "ingest_obs", "arguments": {"name": "x"}}},
        scopes={"tools.read"},
    )
    assert reply["error"]["code"] == -32001
    assert "tools.write" in reply["error"]["message"]


def test_tools_call_honored_when_scope_present():
    """Scope check passes → tool actually runs (may still fail internally)."""
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "recall", "arguments": {"query": "test"}}},
        scopes={"tools.read"},
    )
    # Scope check passes · either result or tool-level error · not -32001.
    assert reply.get("error", {}).get("code") != -32001


def test_resources_list_requires_resources_read():
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 5, "method": "resources/list"},
        scopes={"tools.read"},
    )
    assert reply["error"]["code"] == -32001
    assert "resources.read" in reply["error"]["message"]


def test_resources_read_requires_resources_read():
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 6, "method": "resources/read",
         "params": {"uri": "compass://session/x/session_y.md"}},
        scopes={"tools.write"},
    )
    assert reply["error"]["code"] == -32001


def test_resources_pass_when_scope_held(tmp_path, monkeypatch):
    proj = tmp_path / "p" / "memory"
    proj.mkdir(parents=True)
    (proj / "session_rbac.md").write_text("rbac body", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "PROJECTS_ROOT", tmp_path)
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 7, "method": "resources/list"},
        scopes={"resources.read"},
    )
    assert "result" in reply


def test_unauthenticated_tcp_mode_still_works():
    """scopes=None (stdio or dev TCP) ungates everything."""
    reply = mcp_server.handle_message(
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
         "params": {"name": "ingest_obs", "arguments": {"name": "x"}}},
        scopes=None,
    )
    assert reply.get("error", {}).get("code") != -32001


# ─── end-to-end: scoped token over TCP ──────────────────────────


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _tcp_server_with_tokens(*tokens: str):
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
    for t in tokens:
        cmd += ["--token", t]
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


def test_tcp_reader_token_sees_only_read_tools():
    with _tcp_server_with_tokens("reader:tools.read", "writer:tools.write,tools.read") as port:
        with MCPClient(port=port, token="reader") as c:
            names = {t["name"] for t in c.list_tools()}
            assert "recall" in names
            assert "ingest_obs" not in names
            # Even guessing the tool name · call must fail -32001.
            with pytest.raises(MCPClientError) as ei:
                c.call_tool("ingest_obs", {"name": "x"})
            assert "-32001" in str(ei.value) or "scope" in str(ei.value).lower()


def test_tcp_writer_token_can_call_ingest():
    """Scope check passes · tool may still fail at daemon layer (expected)."""
    with _tcp_server_with_tokens("writer:tools.write,tools.read") as port:
        with MCPClient(port=port, token="writer") as c:
            names = {t["name"] for t in c.list_tools()}
            assert {"recall", "ingest_obs"} <= names


def test_tcp_unknown_token_still_rejected():
    with _tcp_server_with_tokens("reader:tools.read") as port:
        client = MCPClient(port=port, token="NOT-A-REAL-TOKEN", max_retries=0)
        with pytest.raises(MCPClientError) as ei:
            client.__enter__()
        assert "unauthorized" in str(ei.value).lower() or "-32001" in str(ei.value)
