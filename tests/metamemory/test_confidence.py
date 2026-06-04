from metamemory.confidence import ConfidenceVector


def test_confidence_vector_basic():
    cv = ConfidenceVector(
        match_id="m1",
        score=0.82,
        evidence_count=3,
        recency_factor=0.9,
        source_diversity=0.5,
    )
    assert 0.0 <= cv.composite() <= 1.0
    assert cv.score == 0.82


def test_confidence_composite_monotonic():
    """Higher inputs should not decrease composite."""
    low = ConfidenceVector("m1", 0.5, 1, 0.5, 0.5)
    high = ConfidenceVector("m2", 0.9, 5, 0.9, 0.9)
    assert high.composite() > low.composite()
