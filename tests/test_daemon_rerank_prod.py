#!/usr/bin/env python3
"""Task 1.2/1.3 · production reranker behind COMPASS_PROD_RERANK flag.

Tests the in-process reorder helper `_rerank_top(query, top, top_k)`:
  · flag off  → returns dense/fused order unchanged (default behavior intact)
  · flag on   → reorders top-K by injected cross-encoder predictor
  · model load / predict failure → graceful fallback to dense order (no crash)

Uses a fake reranker (monkeypatched singleton) so no real ~2GB model is loaded.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402


def _mk_top():
    """Build a `top` list of (dense_score, entry) tuples in dense order.

    embed_text crafted so a keyword reranker would prefer 'beta' for the query.
    """
    return [
        (0.90, {"path": "a.md", "embed_text": "alpha gamma unrelated filler",
                "description": "alpha"}),
        (0.80, {"path": "b.md", "embed_text": "beta exact target match keyword",
                "description": "beta"}),
        (0.70, {"path": "c.md", "embed_text": "delta epsilon noise",
                "description": "delta"}),
    ]


class _FakeReranker:
    """Fake CrossEncoder: scores pairs by substring presence of 'target'."""
    def __init__(self, raise_on_predict=False):
        self.raise_on_predict = raise_on_predict
        self.calls = []

    def predict(self, pairs):
        if self.raise_on_predict:
            raise RuntimeError("boom: model predict failed")
        self.calls.append(list(pairs))
        # higher score when doc contains 'target'
        return [10.0 if "target" in doc else 1.0 for _q, doc in pairs]


@pytest.fixture(autouse=True)
def _reset_rerank_state(monkeypatch):
    # ensure each test controls the flag + singleton explicitly
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", False, raising=False)
    monkeypatch.setattr(zmd, "_RERANKER_SINGLETON", None, raising=False)
    yield


def test_rerank_top_exists():
    assert hasattr(zmd, "_rerank_top"), "daemon must expose _rerank_top helper"


def test_flag_off_returns_dense_order(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", False, raising=False)
    top = _mk_top()
    out = zmd._rerank_top("find the target", top, top_k=3)
    assert [e["path"] for _s, e in out] == ["a.md", "b.md", "c.md"]


def test_flag_on_reorders_by_reranker(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", True, raising=False)
    fake = _FakeReranker()
    monkeypatch.setattr(zmd, "_get_reranker", lambda: fake, raising=False)
    top = _mk_top()
    out = zmd._rerank_top("find the target", top, top_k=3)
    # b.md has 'target' in embed_text → should be promoted to rank 1
    assert out[0][1]["path"] == "b.md"
    # reranker saw the full embed_text (not just description)
    assert any("target" in doc for _q, doc in fake.calls[0])


def test_flag_on_respects_top_k(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", True, raising=False)
    monkeypatch.setattr(zmd, "_get_reranker", lambda: _FakeReranker(), raising=False)
    out = zmd._rerank_top("find the target", _mk_top(), top_k=2)
    assert len(out) == 2
    assert out[0][1]["path"] == "b.md"


def test_predict_failure_falls_back_to_dense(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", True, raising=False)
    monkeypatch.setattr(zmd, "_get_reranker",
                        lambda: _FakeReranker(raise_on_predict=True), raising=False)
    top = _mk_top()
    out = zmd._rerank_top("find the target", top, top_k=3)
    # graceful fallback: original dense order, no crash
    assert [e["path"] for _s, e in out] == ["a.md", "b.md", "c.md"]


def test_model_load_failure_falls_back_to_dense(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_RERANK_USE", True, raising=False)

    def _boom():
        raise RuntimeError("model file not found")

    monkeypatch.setattr(zmd, "_get_reranker", _boom, raising=False)
    out = zmd._rerank_top("find the target", _mk_top(), top_k=3)
    assert [e["path"] for _s, e in out] == ["a.md", "b.md", "c.md"]
