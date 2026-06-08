"""TDD for ops/recall_fallback.py — T4-primary / CPU-fallback recall (Phase 0 Task 4)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ops"))

import recall_fallback as RF  # noqa: E402

PRIMARY = ("t4.example", 9876)
FALLBACK = ("cpu.example", 9876)


def test_primary_success_no_fallback():
    seen = []

    def caller(host, port, **kw):
        seen.append((host, port))
        return {"ok": True, "recall": ["hit"]}

    res = RF.recall_with_fallback("q", "proj", PRIMARY, FALLBACK, caller=caller)
    assert res["ok"] is True
    assert res["served_by"] == "primary"
    assert seen == [PRIMARY]  # fallback never called


def test_primary_connection_error_uses_fallback():
    def caller(host, port, **kw):
        if (host, port) == PRIMARY:
            raise ConnectionRefusedError("refused")
        return {"ok": True, "recall": ["fallback-hit"]}

    res = RF.recall_with_fallback("q", "proj", PRIMARY, FALLBACK, caller=caller)
    assert res["ok"] is True
    assert res["served_by"] == "fallback"
    assert res["recall"] == ["fallback-hit"]


def test_primary_timeout_uses_fallback():
    import socket

    def caller(host, port, **kw):
        if (host, port) == PRIMARY:
            raise socket.timeout("timed out")
        return {"ok": True, "recall": []}

    res = RF.recall_with_fallback("q", "proj", PRIMARY, FALLBACK, caller=caller)
    assert res["served_by"] == "fallback"


def test_both_down_returns_error_not_raise():
    def caller(host, port, **kw):
        raise ConnectionError("down")

    res = RF.recall_with_fallback("q", "proj", PRIMARY, FALLBACK, caller=caller)
    assert res["ok"] is False
    assert res["served_by"] is None
    assert "error" in res


def test_no_fallback_configured_primary_down():
    def caller(host, port, **kw):
        raise ConnectionRefusedError("refused")

    res = RF.recall_with_fallback("q", "proj", PRIMARY, None, caller=caller)
    assert res["ok"] is False
    assert res["served_by"] is None


def test_primary_ok_false_is_not_a_fallback_trigger():
    """A daemon that is UP but returns ok=False (e.g. query error) is not a connection
    failure -> per plan we do not fall back; return the primary's response."""
    calls = []

    def caller(host, port, **kw):
        calls.append((host, port))
        return {"ok": False, "error": "bad query"}

    res = RF.recall_with_fallback("q", "proj", PRIMARY, FALLBACK, caller=caller)
    assert res["served_by"] == "primary"
    assert res["ok"] is False
    assert calls == [PRIMARY]
