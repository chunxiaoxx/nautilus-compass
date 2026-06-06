"""CJK-surrogate ingest crash fix (cross-device ingest prerequisite).

Root cause (reproduced 2026-06-06): the Windows MCP client gbk-decodes a CJK obs
name/text as UTF-8 with errors='surrogateescape', producing lone surrogates
(\\udc80-\\udcff). handle_ingest's `out_path.write_text(content, encoding="utf-8")`
then crashes `UnicodeEncodeError: surrogates not allowed`, killing the whole obs
(Chinese obs all crash, ASCII passes · session_20260605 Finding 1).

The single cloud-substrate ingest path must NEVER crash on one bad-encoded obs.
`_recover_surrogates` sanitizes at the boundary: a surrogate-escaped string is
re-encoded to its original bytes and decoded as gbk (the Windows default ·
round-trips the CJK); if that fails it falls back to 'replace' so ingest degrades
gracefully. Valid input (ASCII / real CJK) passes through untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import daemon as d  # noqa: E402


# the exact shape Finding 1 saw: gbk bytes decoded utf-8/surrogateescape
def _mangle(s: str) -> str:
    return s.encode("gbk").decode("utf-8", "surrogateescape")


# ── RED 1 · surrogate-escaped gbk CJK is recovered to the original CJK ────────
def test_recovers_gbk_cjk():
    mangled = _mangle("中文测试")
    assert "\udc00" <= mangled[0] <= "\udfff"  # precondition: it IS a lone surrogate
    assert d._recover_surrogates(mangled) == "中文测试"


# ── RED 2 · valid input is never mangled ─────────────────────────────────────
def test_valid_cjk_and_ascii_unchanged():
    assert d._recover_surrogates("中文") == "中文"      # real CJK has no surrogates
    assert d._recover_surrogates("hello_123") == "hello_123"
    assert d._recover_surrogates("") == ""


# ── RED 3 · the GUARANTEE · output is always UTF-8 writable (never crashes) ──
def test_output_is_utf8_writable(tmp_path):
    for bad in [_mangle("噪音服务延迟"), "\udcae\udcff lone", "x\udcaey"]:
        out = d._recover_surrogates(bad)
        # this is the operation that crashed in production — must not raise now
        (tmp_path / "t.md").write_text(out, encoding="utf-8")


# ── RED 4 · unrecoverable surrogate degrades to replacement, no crash ────────
def test_unrecoverable_degrades_not_crash():
    # a lone high surrogate that is not a valid gbk byte sequence
    out = d._recover_surrogates("good\udca0\udca0text")
    out.encode("utf-8")  # must be encodable (no raise)
    assert "good" in out and "text" in out
