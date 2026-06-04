from metamemory import ConfidenceVector, GapStatement, RecallResult


def test_recall_result_with_gaps():
    rr = RecallResult(
        matches=[{"id": "m1", "text": "..."}],
        confidence=[ConfidenceVector("m1", 0.8, 2, 0.9, 0.5)],
        gaps=[GapStatement(topic="degree", reason="no session mentions any degree")],
        source_trail={"m1": "session_20260507_x.md"},
        calibration_score=0.0,
    )
    assert rr.has_evidence_for("degree") is False
    assert rr.has_evidence_for("m1") is True


def test_recall_result_empty_matches_returns_no_evidence():
    rr = RecallResult(
        matches=[],
        confidence=[],
        gaps=[GapStatement(topic="anything", reason="recall returned 0 results")],
        source_trail={},
        calibration_score=0.0,
    )
    assert rr.is_empty()
