"""Bridge stdin must decode UTF-8, never the Windows console code page.

Root cause (SSH+repro confirmed 2026-06-05): on a Chinese Windows host
sys.stdin defaults to gbk + surrogateescape. The MCP JSON-RPC stream is ALWAYS
UTF-8, so reading a CJK obs name through gbk turns its UTF-8 bytes into lone
surrogates (\\udcXX), which then crash downstream strict utf-8 re-encoding
(cloud-side: "tool ingest_obs failed: surrogates not allowed"). The 跨设备 obs
ingest bug. Fix: decode stdin bytes as UTF-8 explicitly.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
# the bridge module exits at import if no cloud token env is set (it's a runtime
# guard); set a dummy so we can import and unit-test the pure _decode_line helper.
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "test-dummy-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")


def test_decode_line_exists():
    assert hasattr(bridge, "_decode_line")


def test_cjk_name_decodes_clean():
    # exactly what Claude Code writes to the bridge's stdin pipe
    raw = '{"name":"跨设备测试obs"}\n'.encode("utf-8")
    out = bridge._decode_line(raw)
    assert "跨设备测试obs" in out
    # CRITICAL: no lone surrogates (the bug signature)
    assert not any("\udc80" <= c <= "\udcff" for c in out)
    # and it must round-trip back to utf-8 without crashing (the reported error)
    out.rstrip("\n").encode("utf-8")  # must not raise


def test_middle_dot_and_punctuation_preserved():
    # "·" (U+00B7) was mangled in the live repro; ensure punctuation survives
    raw = '{"description":"marker · 路标 测试"}\n'.encode("utf-8")
    out = bridge._decode_line(raw)
    assert "·" in out and "路标" in out


def test_ascii_unchanged():
    raw = b'{"name":"xdev-probe-9173"}\n'
    assert bridge._decode_line(raw) == '{"name":"xdev-probe-9173"}\n'


def test_invalid_bytes_do_not_crash_or_surrogate():
    # a stray non-utf8 byte must not raise and must not yield a lone surrogate
    raw = b'{"x":"\xae"}\n'
    out = bridge._decode_line(raw)
    assert not any("\udc80" <= c <= "\udcff" for c in out)
    out.encode("utf-8")  # must not raise
