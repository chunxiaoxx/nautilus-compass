"""C.1 · Measure current drift FP rate baseline before specificity fix.

This test is intentionally a measurement gate · it should PASS today
(reproducing the 5/27 finding that fire count is high) and continue to
pass after C.2 fix (because we only narrow firing · we don't change
existing logged events). The metric to track over time is the
month-over-month fire-rate trend in production.

Reference: memory/session_20260527_drift_loop_open_tuneout.md
  · 457 alerts fired · only 2 manually marked FP (0.4%)
  · estimated true FP rate ~90% · agents tune out → detection ≈ 0
    behavior impact (detection ≠ intervention).
"""
import pytest
from pathlib import Path


CACHE = Path.home() / ".claude/plugins/nautilus-compass/.cache"
DRIFT_LOG = CACHE / "drift_mitigation_log.jsonl"
VERIFY_LOG = CACHE / "verification_log.jsonl"
FEEDBACK_LOG = CACHE / "feedback.jsonl"


def test_drift_mitigation_log_has_significant_fires():
    """5/27 finding · drift fired hundreds of times in observation window.

    Gates at >100 (not == 715) so the test survives normal log churn
    but catches a wipe-regression (would drop to 0).
    """
    if not DRIFT_LOG.exists():
        pytest.skip("drift_mitigation_log not present · fresh install or wiped")
    lines = DRIFT_LOG.read_text(encoding="utf-8").splitlines()
    fires = [l for l in lines if l.strip()]
    assert len(fires) > 100, f"Expected >100 fire events · got {len(fires)}"


def test_fp_marker_rate_in_feedback_under_five_percent():
    """5/27 finding · only ~0.4% of fires explicitly marked FP by user.

    This proves the cry-wolf problem: low explicit FP marking + high fire
    count + user tune-out = detection signal has zero intervention value.
    Track as observability gate · NOT a regression test (if user starts
    marking FPs actively after C.2 ships, ratio may climb, and that's a
    *good* signal · adjust gate then).
    """
    if not FEEDBACK_LOG.exists() or not DRIFT_LOG.exists():
        pytest.skip("logs not present")
    fb_lines = [l for l in FEEDBACK_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    drift_lines = [l for l in DRIFT_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    fp_count = sum(1 for l in fb_lines if '"fp"' in l or '"false_positive"' in l)
    ratio = fp_count / max(1, len(drift_lines))
    assert ratio < 0.05, (
        f"FP marker rate {ratio:.3%} unexpectedly high · "
        f"maybe user started marking actively · revisit gate"
    )
