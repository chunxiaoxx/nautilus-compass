from metamemory.calibration import calibration_score


def test_calibration_score_perfect():
    """If confidence ≈ correct rate per bucket, score should be close to 1.0."""
    history = [
        {"confidence": 0.92, "correct": True},
        {"confidence": 0.95, "correct": True},
        {"confidence": 0.93, "correct": True},   # high-conf bucket: 3/3 correct · avg 0.933
        {"confidence": 0.05, "correct": False},
        {"confidence": 0.10, "correct": False},
        {"confidence": 0.05, "correct": False},  # low-conf bucket: 0/3 correct · avg 0.067
    ]
    score = calibration_score(history)
    # Expected score ≈ 1 - mean(|0.933 - 1.0|, |0.067 - 0.0|) ≈ 1 - 0.067 ≈ 0.933
    assert score > 0.85


def test_calibration_score_anti_correlated():
    """Confident-but-wrong + low-confident-but-right → poor calibration."""
    history = [
        {"confidence": 0.9, "correct": False},
        {"confidence": 0.85, "correct": False},
        {"confidence": 0.1, "correct": True},
        {"confidence": 0.15, "correct": True},
    ]
    score = calibration_score(history)
    assert score < 0.3


def test_calibration_score_empty_history_returns_zero():
    """No data → uncalibrated → score 0.0 (NOT NaN)."""
    assert calibration_score([]) == 0.0
