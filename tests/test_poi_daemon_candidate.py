"""Lock the contract the daemon-path candidate adapter relies on.

try_daemon_recall adapts its recall dict-list to `[(score, entry), ...]` where
entry carries only `path` (a filename, daemon shape — no `fullpath`). This test
verifies emit_poi_candidate accepts that shape and writes candidate lines, so
the L3 candidate stream actually lands on the production (daemon) path.
"""
from __future__ import annotations

import json
from pathlib import Path

from proof.poi_emitter import emit_poi_candidate


def test_daemon_shape_entries_produce_candidates(tmp_path: Path):
    # daemon recall list: dicts with filename-only 'path' (no fullpath)
    recall = [
        {"score": 0.81, "path": "session_a.md", "age_seconds": 100},
        {"score": 0.77, "path": "session_b.md", "age_seconds": 8000},
    ]
    top = [(r.get("score", 0.0), r) for r in recall]
    n = emit_poi_candidate(top, query="some query", agent_id="kairos", cache_dir=tmp_path)
    assert n == 2
    lines = (tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["kind"] == "candidate"
    assert rec["actor"] == "kairos"
    assert rec["memory"] in {"session_a.md", "session_b.md"}
    assert "query_hash" in rec and "score" in rec


def test_empty_recall_writes_nothing(tmp_path: Path):
    n = emit_poi_candidate([], query="q", agent_id="kairos", cache_dir=tmp_path)
    assert n == 0
    assert not (tmp_path / "poi_candidates.jsonl").exists() or \
        (tmp_path / "poi_candidates.jsonl").read_text(encoding="utf-8").strip() == ""
