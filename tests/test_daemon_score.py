#!/usr/bin/env python3
"""score action · bge-m3 query↔candidate cosine (serving semantic recall).

Tests the in-process `_handle_score(req)` helper:
  · ranks candidates by cosine similarity to the query (descending)
  · empty candidate list → {"ok": False, "error": ...}

Uses a fake embedder (monkeypatched `daemon._get_embedder`) so no real bge-m3
~2.3GB model is loaded.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import daemon  # noqa: E402


class _FakeEmbedder:
    def encode(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]


def test_score_ranks_by_cosine(monkeypatch):
    monkeypatch.setattr(daemon, "_get_embedder", lambda: _FakeEmbedder())
    resp = daemon._handle_score({"action": "score", "query": "alpha thing",
                                 "candidates": ["alpha match", "beta other"]})
    assert resp["ok"] is True
    assert len(resp["scores"]) == 2
    assert resp["scores"][0] > resp["scores"][1]


def test_score_empty_candidates():
    resp = daemon._handle_score({"action": "score", "query": "x", "candidates": []})
    assert resp["ok"] is False
