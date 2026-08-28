"""scoped-token 鉴权单测 · 2026-08-28 安全修复（workbuddy 接入暴露的权限洞）"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("mcp_http_server", ROOT / "mcp_http_server.py")
m = importlib.util.module_from_spec(spec)
sys.modules["mcp_http_server"] = m
try:
    spec.loader.exec_module(m)
except Exception:  # 服务器依赖(mcp SDK)缺失时只测纯函数
    src = (ROOT / "mcp_http_server.py").read_text(encoding="utf-8")
    ns = {"os": os, "json": json}
    start = src.index("READ_TOOLS")
    end = src.index("class _BearerAuth")
    exec(src[start:end], ns)
    class M:  # noqa: E999 - plain namespace
        pass
    m = M()
    m._scopes_from_value = staticmethod(ns["_scopes_from_value"])
    m._check_scope = staticmethod(ns["_check_scope"])


def test_scopes_from_value():
    assert m._scopes_from_value({"scopes": ["read:P"]}) == frozenset({"read:P"})
    assert m._scopes_from_value(["tools.read"]) == frozenset({"read:*", "write:*"})
    assert m._scopes_from_value([]) == frozenset()
    assert m._scopes_from_value("garbage") == frozenset()


def test_read_scope():
    s = frozenset({"read:ProjA"})
    assert m._check_scope(s, "recall", {"project": "ProjA"}) is None
    deny = m._check_scope(s, "recall", {"project": "ProjB"})
    assert deny and "lacks read" in deny
    # scope=user 跨项目全域 → 需 read:*
    deny = m._check_scope(s, "recall", {"project": "ProjA", "scope": "user"})
    assert deny and "read:*" in deny
    assert m._check_scope(frozenset({"read:*"}), "recall",
                          {"project": "whatever", "scope": "user"}) is None


def test_write_fail_closed():
    s = frozenset({"read:ProjA"})
    assert "write" in m._check_scope(s, "ingest_obs", {"project": "ProjA"})
    # 未知工具默认 write 级
    assert "write" in m._check_scope(s, "some_new_tool", {"project": "ProjA"})
    assert m._check_scope(frozenset({"write:ProjA"}), "ingest_obs",
                          {"project": "ProjA"}) is None


def test_admin_and_star():
    adm = frozenset({"admin"})
    assert m._check_scope(adm, "recall", {"project": "X", "scope": "user"}) is None
    assert m._check_scope(adm, "ingest_obs", {"project": "X"}) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"  {name} ✓")
    print("ALL PASS")
