"""Tests for proof.local_outcomes · Path B (local self-closing loop).

The platform L4 outcomes only credit platform agents. Most recall traffic is the
local user (actor 'unknown'/anon), whose actions have no platform outcome. Path B
derives a LOCAL outcome signal from the user's own session_*.md files (their
`drift` frontmatter: green = success, yellow/red = not), attributed to the local
actor, so local recalls can settle into cumulative_impact without any platform
agent. NO LLM · pure frontmatter + filename parse.
"""
from __future__ import annotations

from pathlib import Path

from proof import local_outcomes as LO


def _session(tmp: Path, name: str, drift: str = "green") -> Path:
    p = tmp / name
    p.write_text(f"---\nname: x\ntype: session\ndrift: {drift}\n---\n\nbody\n",
                 encoding="utf-8")
    return p


def test_parse_ts_from_session_filename():
    # session_YYYYMMDD-HHMM_... -> iso ts
    ts = LO.ts_from_filename("session_20260602-1430_foo.md")
    assert ts is not None and ts.startswith("2026-06-02T14:30")


def test_parse_ts_underscore_variant():
    ts = LO.ts_from_filename("session_20260602_foo.md")
    assert ts is not None and ts.startswith("2026-06-02")


def test_parse_ts_returns_none_for_non_session():
    assert LO.ts_from_filename("reference_thing.md") is None


def test_green_session_is_success(tmp_path: Path):
    _session(tmp_path, "session_20260602-1000_a.md", drift="green")
    outs = LO.local_outcomes(tmp_path, actor="unknown")
    assert len(outs) == 1
    assert outs[0]["agent_id"] == "unknown"
    assert outs[0]["success"] is True


def test_yellow_and_red_sessions_are_failure(tmp_path: Path):
    _session(tmp_path, "session_20260602-1000_y.md", drift="yellow")
    _session(tmp_path, "session_20260602-1100_r.md", drift="red")
    outs = LO.local_outcomes(tmp_path, actor="unknown")
    assert all(o["success"] is False for o in outs)
    assert len(outs) == 2


def test_non_session_files_skipped(tmp_path: Path):
    _session(tmp_path, "session_20260602-1000_a.md", drift="green")
    (tmp_path / "reference_x.md").write_text("---\ndrift: green\n---\nbody\n", encoding="utf-8")
    outs = LO.local_outcomes(tmp_path, actor="unknown")
    assert len(outs) == 1  # only the session_ file


def test_since_filter(tmp_path: Path):
    _session(tmp_path, "session_20260601-1000_old.md", drift="green")
    _session(tmp_path, "session_20260603-1000_new.md", drift="green")
    outs = LO.local_outcomes(tmp_path, actor="unknown", since_iso="2026-06-02T00:00:00")
    assert len(outs) == 1
    assert outs[0]["ts"].startswith("2026-06-03")


def test_missing_drift_defaults_skipped_or_pending(tmp_path: Path):
    p = tmp_path / "session_20260602-1000_nodrift.md"
    p.write_text("---\nname: x\ntype: session\n---\nbody\n", encoding="utf-8")
    outs = LO.local_outcomes(tmp_path, actor="unknown")
    # no drift field -> no usable outcome signal -> skipped
    assert outs == []


def test_reconcile_with_local_outcomes_settles(tmp_path: Path):
    # end-to-end: a local candidate + a later green local session -> settles
    from proof import poi_reconciler as R
    mem = tmp_path / "session_20260602-0900_cited.md"
    mem.write_text("---\nname: cited\ntype: reference\ndrift: green\nagent_type: other\n---\nbody\n",
                   encoding="utf-8")
    _session(tmp_path, "session_20260602-1000_outcome.md", drift="green")
    cand = {"ts": "2026-06-02T09:30:00+00:00", "actor": "unknown",
            "memory": "session_20260602-0900_cited.md", "query_hash": "h", "rank": 0, "score": 0.8}
    outs = LO.local_outcomes(tmp_path, actor="unknown")
    res = R.reconcile([cand], outs, settled_keys=set(), window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 1
    assert "cumulative_impact:" in mem.read_text(encoding="utf-8")
