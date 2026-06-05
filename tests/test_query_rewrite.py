"""Gemini query-rewrite · opt-in recall enhancement.

rewrite_query is identity unless BOTH the query_rewrite flag
(COMPASS_PROD_QUERY_REWRITE) AND the gemini provider (COMPASS_USE_GEMINI_FLASH)
are on. Any gemini failure → original query (recall must never break/degrade).
Uses an injectable judge so no live Gemini API is touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import query_rewrite as qr  # noqa: E402


class _FakeJudge:
    def __init__(self, out):
        self.out = out
        self.calls = []

    def generate(self, prompt, max_tokens=120, temperature=0.1):
        self.calls.append(prompt)
        if isinstance(self.out, Exception):
            raise self.out
        return self.out


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("COMPASS_PROD_QUERY_REWRITE", raising=False)
    monkeypatch.delenv("COMPASS_USE_GEMINI_FLASH", raising=False)
    yield


def _on(monkeypatch):
    monkeypatch.setenv("COMPASS_PROD_QUERY_REWRITE", "1")
    monkeypatch.setenv("COMPASS_USE_GEMINI_FLASH", "1")


def test_flag_off_is_identity(monkeypatch):
    assert qr.rewrite_query("residual insurance", judge=_FakeJudge("X")) == "residual insurance"


def test_provider_off_is_identity(monkeypatch):
    monkeypatch.setenv("COMPASS_PROD_QUERY_REWRITE", "1")  # rewrite on, provider off
    assert qr.rewrite_query("foo", judge=_FakeJudge("X")) == "foo"


def test_on_rewrites(monkeypatch):
    _on(monkeypatch)
    fake = _FakeJudge("residual insurance levy 残保金 disability employment quota")
    out = qr.rewrite_query("残保金", judge=fake)
    assert out == "residual insurance levy 残保金 disability employment quota"
    assert fake.calls and "残保金" in fake.calls[0]  # query passed into prompt


def test_gemini_none_falls_back(monkeypatch):
    _on(monkeypatch)
    assert qr.rewrite_query("q", judge=_FakeJudge(None)) == "q"


def test_gemini_empty_falls_back(monkeypatch):
    _on(monkeypatch)
    assert qr.rewrite_query("q", judge=_FakeJudge("   ")) == "q"


def test_gemini_exception_falls_back(monkeypatch):
    _on(monkeypatch)
    assert qr.rewrite_query("q", judge=_FakeJudge(RuntimeError("boom"))) == "q"


def test_overlong_output_falls_back(monkeypatch):
    _on(monkeypatch)
    assert qr.rewrite_query("q", judge=_FakeJudge("x" * 5000)) == "q"


def test_takes_first_line_and_strips(monkeypatch):
    _on(monkeypatch)
    out = qr.rewrite_query("q", judge=_FakeJudge("  expanded q terms  \nignored second line"))
    assert out == "expanded q terms"


def test_empty_query_identity(monkeypatch):
    _on(monkeypatch)
    assert qr.rewrite_query("   ", judge=_FakeJudge("X")) == "   "


def test_flag_registered():
    import llm_opt_in
    assert hasattr(llm_opt_in, "QUERY_REWRITE")
    assert llm_opt_in.QUERY_REWRITE in llm_opt_in._FLAGS
