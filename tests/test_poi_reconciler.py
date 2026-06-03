"""Tests for proof.poi_reconciler · closes the L3 loop.

Joins recall-time PoI candidates (memory surfaced to actor · no outcome) with
real agent outcomes (from L4 cross-agent data) → settles each match into a full
PoI event (emit_full) that credits cumulative_impact on the cited memory.

Pure matching/mapping is unit-tested here; emit_full integration is exercised
against a temp memory file (verifies cumulative_impact actually lands).
"""
from __future__ import annotations

from pathlib import Path

from proof import poi_reconciler as R


# -------------------------------------------------- outcome -> action_outcome
def test_outcome_success_maps_to_success():
    assert R.outcome_to_action_outcome({"success": True}) == "success"
    assert R.outcome_to_action_outcome({"success": False}) == "failure"


def test_outcome_none_is_pending():
    assert R.outcome_to_action_outcome({"success": None}) == "pending"


# ------------------------------------------------------------ match_outcome
def _cand(ts="2026-06-02T10:00:00+00:00", actor="kairos", memory="m.md", qh="abc"):
    return {"ts": ts, "actor": actor, "memory": memory, "query_hash": qh,
            "rank": 0, "score": 0.8}


def _out(agent_id="kairos", success=True, ts="2026-06-02T10:05:00+00:00"):
    return {"agent_id": agent_id, "success": success, "ts": ts}


def test_match_picks_outcome_for_same_actor_after_candidate():
    cand = _cand()
    outcomes = [_out(ts="2026-06-02T10:05:00+00:00")]
    m = R.match_outcome(cand, outcomes, window_seconds=86400)
    assert m is not None
    assert m["agent_id"] == "kairos"


def test_match_rejects_different_actor():
    cand = _cand(actor="kairos")
    outcomes = [_out(agent_id="v7-telegram")]
    assert R.match_outcome(cand, outcomes, window_seconds=86400) is None


def test_match_rejects_outcome_before_candidate():
    cand = _cand(ts="2026-06-02T10:00:00+00:00")
    outcomes = [_out(ts="2026-06-02T09:00:00+00:00")]  # before the recall
    assert R.match_outcome(cand, outcomes, window_seconds=86400) is None


def test_match_rejects_outside_window():
    cand = _cand(ts="2026-06-02T10:00:00+00:00")
    outcomes = [_out(ts="2026-06-05T10:00:00+00:00")]  # 3 days later
    assert R.match_outcome(cand, outcomes, window_seconds=3600) is None


def test_match_picks_earliest_following_outcome():
    cand = _cand(ts="2026-06-02T10:00:00+00:00")
    outcomes = [
        _out(ts="2026-06-02T12:00:00+00:00", success=False),
        _out(ts="2026-06-02T10:30:00+00:00", success=True),  # earliest after
    ]
    m = R.match_outcome(cand, outcomes, window_seconds=86400)
    assert m["ts"] == "2026-06-02T10:30:00+00:00"
    assert m["success"] is True


# --------------------------------------------------------- candidate_key
def test_candidate_key_stable_and_distinct():
    a = R.candidate_key(_cand(memory="m1.md"))
    b = R.candidate_key(_cand(memory="m1.md"))
    c = R.candidate_key(_cand(memory="m2.md"))
    assert a == b
    assert a != c


# ----------------------------------------------- reconcile (emit_full lands)
def _write_memory(tmp_path: Path, name="m.md", drift="green", creator="someone-else"):
    p = tmp_path / name
    p.write_text(
        f"---\nname: x\ntype: reference\ndrift: {drift}\nagent_type: {creator}\n---\n\nbody\n",
        encoding="utf-8")
    return p


def test_reconcile_settles_match_and_updates_cumulative_impact(tmp_path):
    mem = _write_memory(tmp_path, name="m.md")
    cands = [_cand(memory="m.md", actor="kairos")]
    outs = [_out(agent_id="kairos", success=True)]
    res = R.reconcile(cands, outs, settled_keys=set(), window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 1
    # cumulative_impact frontmatter now present + positive (success outcome)
    txt = mem.read_text(encoding="utf-8")
    assert "cumulative_impact:" in txt
    assert "impact_event_count: 1" in txt


def test_reconcile_idempotent_via_settled_keys(tmp_path):
    _write_memory(tmp_path, name="m.md")
    cands = [_cand(memory="m.md", actor="kairos")]
    outs = [_out(agent_id="kairos", success=True)]
    seen = set()
    r1 = R.reconcile(cands, outs, settled_keys=seen, window_seconds=86400,
                     memory_root=tmp_path, cache_dir=tmp_path)
    assert r1["settled"] == 1
    # second pass with the same settled_keys must not re-settle
    r2 = R.reconcile(cands, outs, settled_keys=seen, window_seconds=86400,
                     memory_root=tmp_path, cache_dir=tmp_path)
    assert r2["settled"] == 0
    assert r2["skipped_already"] == 1


def test_reconcile_no_match_does_not_settle(tmp_path):
    _write_memory(tmp_path, name="m.md")
    cands = [_cand(memory="m.md", actor="kairos")]
    outs = [_out(agent_id="v7-telegram", success=True)]  # different actor
    res = R.reconcile(cands, outs, settled_keys=set(), window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 0
    assert res["skipped_no_match"] == 1


def test_match_handles_naive_outcome_ts_without_crashing():
    # H1: a platform outcome may carry a naive ts (no tz). Must not raise
    # "can't compare offset-naive and offset-aware".
    cand = _cand(ts="2026-06-02T10:00:00+00:00")
    outcomes = [{"agent_id": "kairos", "success": True,
                 "ts": "2026-06-02T10:05:00"}]  # naive, no +00:00
    m = R.match_outcome(cand, outcomes, window_seconds=86400)
    assert m is not None  # treated as UTC, matches in-window


def test_reconcile_with_naive_outcome_does_not_crash(tmp_path):
    _write_memory(tmp_path, name="m.md")
    cands = [_cand(memory="m.md", actor="kairos", ts="2026-06-02T10:00:00+00:00")]
    outs = [{"agent_id": "kairos", "success": True, "ts": "2026-06-02T10:05:00"}]
    res = R.reconcile(cands, outs, settled_keys=set(), window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 1


def test_reconcile_missing_memory_file_not_settled(tmp_path):
    # M1: if the cited memory file doesn't exist, emit_full updates nothing →
    # must NOT count as settled (no fake closed loop) and stay retryable.
    cands = [_cand(memory="does_not_exist.md", actor="kairos")]
    outs = [_out(agent_id="kairos", success=True)]
    seen = set()
    res = R.reconcile(cands, outs, settled_keys=seen, window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 0
    assert len(seen) == 0  # key not burned → retryable later


def test_candidate_key_ignores_second_level_ts(tmp_path):
    # M2: same (actor, memory, query) recalled in different seconds must share a
    # key so one outcome can't double-credit the memory.
    a = R.candidate_key(_cand(ts="2026-06-02T10:00:00+00:00", memory="m.md"))
    b = R.candidate_key(_cand(ts="2026-06-02T10:00:05+00:00", memory="m.md"))
    assert a == b


def test_reconcile_no_double_count_across_seconds(tmp_path):
    mem = _write_memory(tmp_path, name="m.md")
    cands = [
        _cand(memory="m.md", actor="kairos", ts="2026-06-02T10:00:00+00:00"),
        _cand(memory="m.md", actor="kairos", ts="2026-06-02T10:00:05+00:00"),
    ]
    outs = [_out(agent_id="kairos", success=True, ts="2026-06-02T10:30:00+00:00")]
    res = R.reconcile(cands, outs, settled_keys=set(), window_seconds=86400,
                      memory_root=tmp_path, cache_dir=tmp_path)
    assert res["settled"] == 1  # not 2


def test_reconcile_failure_outcome_gives_negative_impact(tmp_path):
    mem = _write_memory(tmp_path, name="m.md")
    cands = [_cand(memory="m.md", actor="kairos")]
    outs = [_out(agent_id="kairos", success=False)]
    R.reconcile(cands, outs, settled_keys=set(), window_seconds=86400,
                memory_root=tmp_path, cache_dir=tmp_path)
    txt = mem.read_text(encoding="utf-8")
    # failure outcome -> negative cumulative_impact
    line = [l for l in txt.splitlines() if l.startswith("cumulative_impact:")][0]
    val = float(line.split(":", 1)[1])
    assert val < 0
