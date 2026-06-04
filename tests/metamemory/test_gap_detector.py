from metamemory import ConfidenceVector
from metamemory.gap_detector import detect_gaps


def test_detect_gap_when_all_confidence_low():
    matches = [{"id": "m1", "text": "weather is nice today"}]
    confidence = [ConfidenceVector("m1", 0.2, 1, 0.5, 0.0)]
    query = "what degree did I graduate with"
    gaps = detect_gaps(query, matches, confidence, threshold=0.4)
    assert len(gaps) == 1
    assert "degree" in gaps[0].topic.lower()


def test_no_gap_when_high_confidence_match():
    matches = [{"id": "m1", "text": "I graduated with BA"}]
    confidence = [ConfidenceVector("m1", 0.85, 4, 0.9, 0.5)]
    query = "what degree did I graduate with"
    gaps = detect_gaps(query, matches, confidence, threshold=0.4)
    assert len(gaps) == 0


def test_detect_gap_when_no_matches():
    """0 matches · always returns 1 gap regardless of threshold."""
    gaps = detect_gaps("anything", matches=[], confidence=[], threshold=0.4)
    assert len(gaps) == 1
    assert gaps[0].topic == "anything"
