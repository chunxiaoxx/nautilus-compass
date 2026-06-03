"""Tests for metamemory.builder.build_recall_result · the L2 integration glue.

Maps real recall match dicts -> RecallResult (confidence per match + source_trail
+ gaps), with a pluggable LLM backend hook (default None = deterministic, no LLM,
black-box moat preserved).
"""
from __future__ import annotations

from metamemory.builder import build_recall_result, format_metamemory_notice
from metamemory.result import RecallResult


def _match(path, score, age_seconds=0, type_="reference", concept="x", description="d"):
    return {"path": path, "score": score, "age_seconds": age_seconds,
            "type": type_, "concept": concept, "name": path, "description": description}


def test_returns_recall_result_with_per_match_confidence():
    matches = [_match("a.md", 0.9), _match("b.md", 0.7)]
    rr = build_recall_result("what is X", matches)
    assert isinstance(rr, RecallResult)
    assert len(rr.matches) == 2
    assert len(rr.confidence) == 2
    assert {cv.match_id for cv in rr.confidence} == {"a.md", "b.md"}


def test_source_trail_maps_each_match_to_origin():
    matches = [_match("session_20260602_foo.md", 0.8, type_="feedback")]
    rr = build_recall_result("q", matches)
    assert "session_20260602_foo.md" in rr.source_trail
    # origin string carries something identifying (the file / type)
    assert "feedback" in rr.source_trail["session_20260602_foo.md"]


def test_empty_matches_surfaces_gap():
    # the hallucinate-absence cure: no recall -> explicit "no evidence" gap
    rr = build_recall_result("obscure thing", [])
    assert rr.is_empty()
    assert len(rr.gaps) == 1
    assert rr.gaps[0].topic == "obscure thing"


def test_weak_matches_surface_gap():
    # all low score + old -> low composite -> gap
    matches = [_match("a.md", 0.1, age_seconds=365 * 86400)]
    rr = build_recall_result("q", matches, gap_threshold=0.4)
    assert len(rr.gaps) == 1


def test_strong_match_no_gap():
    matches = [_match("a.md", 0.95, age_seconds=0)]
    rr = build_recall_result("q", matches, gap_threshold=0.4)
    assert rr.gaps == []


def test_recent_match_has_higher_recency_than_old():
    fresh = build_recall_result("q", [_match("a.md", 0.8, age_seconds=0)])
    stale = build_recall_result("q", [_match("a.md", 0.8, age_seconds=60 * 86400)])
    assert fresh.confidence[0].recency_factor > stale.confidence[0].recency_factor


def test_score_clamped_to_unit_interval():
    # recall scores can exceed 1 (reranker) or go negative; ConfidenceVector wants [0,1]
    rr = build_recall_result("q", [_match("a.md", 1.7), _match("b.md", -0.3)])
    for cv in rr.confidence:
        assert 0.0 <= cv.score <= 1.0


def test_llm_backend_none_is_deterministic():
    matches = [_match("a.md", 0.95)]
    rr1 = build_recall_result("q", matches, llm_backend=None)
    rr2 = build_recall_result("q", matches, llm_backend=None)
    assert [g.topic for g in rr1.gaps] == [g.topic for g in rr2.gaps]


def test_llm_backend_can_refine_gaps():
    from metamemory.gap import GapStatement

    called = {}

    def fake_backend(query, matches, det_gaps):
        called["yes"] = True
        return [GapStatement(topic="llm-found-gap", reason="semantic")]

    rr = build_recall_result("q", [_match("a.md", 0.95)], llm_backend=fake_backend)
    assert called.get("yes") is True
    assert any(g.topic == "llm-found-gap" for g in rr.gaps)


def test_llm_backend_failure_falls_back_to_deterministic():
    # a flaky LLM backend must never break recall · degrade to deterministic gaps
    def boom(query, matches, det_gaps):
        raise RuntimeError("backend down")

    rr = build_recall_result("obscure", [], llm_backend=boom)
    # deterministic gap (empty matches) survives the backend failure
    assert len(rr.gaps) == 1
    assert rr.gaps[0].topic == "obscure"


# ----------------------------------------------------- format_metamemory_notice
def test_format_notice_empty_when_strong_evidence():
    rr = build_recall_result("q", [_match("a.md", 0.95, age_seconds=0)])
    # strong evidence, no gap -> no noise injected into the agent's context
    assert format_metamemory_notice(rr) == ""


def test_format_notice_warns_on_gap():
    rr = build_recall_result("the X thing", [])
    notice = format_metamemory_notice(rr)
    assert notice != ""
    # must mention the topic and convey absence of evidence
    assert "the X thing" in notice
    assert "没有" in notice and "evidence" in notice.lower()


def test_format_notice_is_string():
    rr = build_recall_result("q", [_match("a.md", 0.1, age_seconds=999 * 86400)])
    assert isinstance(format_metamemory_notice(rr), str)
