"""TCP 版项目级 scope 单测 · 2026-08-30(workbuddy 跨框记忆暴露修复)

背景:8/28 scoped-token 体系只落在 HTTP 版(mcp_http_server.py),
TCP 版(mcp_server.py·workbuddy 与各框桥的主通道)只有工具级
tools.read/tools.write——持有效 token 可跨全部 project 读写。
本测试钉住 TCP 版新增的项目级 scope 语义(与 HTTP 版 _check_scope 同构)。
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("mcp_server", ROOT / "mcp_server.py")
m = importlib.util.module_from_spec(spec)
sys.modules["mcp_server"] = m
try:
    spec.loader.exec_module(m)
except Exception:  # 服务端依赖缺失时只测 RBAC 纯函数段
    src = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    ns = {"os": os, "json": json}
    start = src.index('TOOL_SCOPE_MAP = {')
    end = src.index("# ─── per-token rate limit")
    exec(src[start:end], ns)
    class M:  # noqa: E999 - plain namespace
        pass
    m = M()
    for k in ("TOOL_SCOPE_MAP", "ALL_SCOPES", "_scope_is_known",
              "_parse_token_spec", "_load_token_table", "_has_scope",
              "_has_project_scopes", "_check_project_scope"):
        setattr(m, k, ns[k])


def test_scope_is_known():
    assert m._scope_is_known("tools.read")
    assert m._scope_is_known("admin")
    assert m._scope_is_known("read:C--Users-chunx")
    assert m._scope_is_known("write:nautilus-core")
    assert m._scope_is_known("read:*")
    assert not m._scope_is_known("read:")
    assert not m._scope_is_known("garbage")
    assert not m._scope_is_known("write")


def test_parse_token_spec_accepts_project_scopes():
    tok, sc = m._parse_token_spec("cmp_x:read:ProjA,write:ProjA")
    assert tok == "cmp_x" and sc == {"read:ProjA", "write:ProjA"}


def test_load_token_table_new_format():
    import tempfile
    data = {
        "cmp_workbuddy__abc": {"scopes": ["read:C--Users-chunx", "write:C--Users-chunx"]},
        "cmp_legacy_true": True,                       # 旧格式 bool = 全权
        "cmp_legacy_list": ["tools.read", "tools.write"],  # 旧 list = 工具级集合(现状语义)
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        table = m._load_token_table(None, path)
        assert table["cmp_workbuddy__abc"] == {"read:C--Users-chunx", "write:C--Users-chunx"}
        assert "*" in table["cmp_legacy_true"]
        assert table["cmp_legacy_list"] == {"tools.read", "tools.write"}
    finally:
        os.unlink(path)


def test_project_scopes_detection():
    assert m._has_project_scopes({"read:C--Users-chunx", "write:C--Users-chunx"})
    assert m._has_project_scopes({"admin"})
    assert not m._has_project_scopes({"*"})                    # 旧全权
    assert not m._has_project_scopes({"tools.read", "tools.write"})  # 旧工具级
    assert not m._has_project_scopes(None)                     # 无鉴权模式


def test_scoped_token_read_boundary():
    s = {"read:ProjA"}
    assert m._check_project_scope(s, "recall", {"project": "ProjA"}) is None
    deny = m._check_project_scope(s, "recall", {"project": "ProjB"})
    assert deny and "read" in deny
    # scope=user 跨项目全域 → 需 read:*
    deny = m._check_project_scope(s, "recall", {"project": "ProjA", "scope": "user"})
    assert deny and "read:*" in deny
    # session_search 无 project 参数 → 只有 read:* 放行
    deny = m._check_project_scope(s, "session_search", {})
    assert deny


def test_scoped_token_write_fail_closed():
    s = {"read:ProjA"}
    assert "write" in m._check_project_scope(s, "ingest_obs", {"project": "ProjA"})
    # 未知工具按写级(与 HTTP 版 fail-closed 一致)
    assert "write" in m._check_project_scope(s, "some_new_tool", {"project": "ProjA"})
    assert m._check_project_scope({"write:ProjA"}, "ingest_obs", {"project": "ProjA"}) is None


def test_admin_and_legacy_pass():
    assert m._check_project_scope({"admin"}, "recall", {"project": "X", "scope": "user"}) is None
    assert m._check_project_scope({"*"}, "ingest_obs", {"project": "X"}) is None
    assert m._check_project_scope({"tools.read", "tools.write"},
                                  "recall", {"project": "whatever"}) is None
    assert m._check_project_scope(None, "recall", {"project": "whatever"}) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"  {name} ✓")
    print("ALL PASS")
