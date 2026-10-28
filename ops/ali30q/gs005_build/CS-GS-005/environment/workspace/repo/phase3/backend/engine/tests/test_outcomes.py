"""Tests for engine.outcomes · Stage 1 metric helpers."""
from dataclasses import dataclass, field

from engine.outcomes import (
    classify,
    compute_composite,
    compute_drift_ratio,
    is_deadletter,
    parse_spec_meta,
)


# ───────── parse_spec_meta ─────────

def test_parse_spec_meta_present():
    task = "do thing\n\nSpec-Meta:\n  expected_added: 2\n  expected_removed: 0\n"
    assert parse_spec_meta(task) == {"expected_added": 2, "expected_removed": 0}


def test_parse_spec_meta_absent():
    assert parse_spec_meta("just a task with no meta") == {
        "expected_added": None,
        "expected_removed": None,
    }


def test_parse_spec_meta_partial():
    task = "x\n\nSpec-Meta:\n  expected_added: 5\n"
    assert parse_spec_meta(task) == {"expected_added": 5, "expected_removed": None}


def test_parse_spec_meta_malformed_permissive():
    task = "x\n\nSpec-Meta:\n  expected_added: not-an-int\n"
    # Permissive: bad int → field stays None · doesn't raise.
    assert parse_spec_meta(task) == {"expected_added": None, "expected_removed": None}


def test_parse_spec_meta_extra_whitespace():
    task = "x\n\nSpec-Meta:\n     expected_added:    2   \n     expected_removed:  0  \n"
    assert parse_spec_meta(task) == {"expected_added": 2, "expected_removed": 0}


def test_parse_spec_meta_empty_string():
    assert parse_spec_meta("") == {"expected_added": None, "expected_removed": None}


def test_parse_spec_meta_unknown_field_ignored():
    task = "x\n\nSpec-Meta:\n  expected_added: 3\n  bogus_key: 99\n"
    assert parse_spec_meta(task) == {"expected_added": 3, "expected_removed": None}


# ───────── compute_composite ─────────

def test_composite_drift_perfect_match_scores_one():
    # drift = 1.0 (actual matches expected) is the optimal point.
    assert compute_composite(semantic=True, tests=True, drift=1.0) == 1.0


def test_composite_drift_zero_means_under_shipped():
    # drift=0 means nothing shipped vs expected something · contribute 0.
    # (1 + 1 + 0) / 3
    assert compute_composite(True, True, drift=0.0) == round((1 + 1 + 0) / 3, 3)


def test_composite_drift_over_two_clamped_to_zero():
    # drift = 2.0 (over-ship 2x · deviation 1.0) → contribute 0
    assert compute_composite(True, True, drift=2.0) == round((1 + 1 + 0) / 3, 3)


def test_composite_drift_half_under_shipped():
    # drift = 0.5 (deviation 0.5) → contribute 0.5
    assert compute_composite(True, True, drift=0.5) == round((1 + 1 + 0.5) / 3, 3)


def test_composite_null_degrade_two_signals():
    # tests unavailable · average over (semantic=1 + drift=1) = 1.0
    assert compute_composite(True, None, drift=1.0) == 1.0


def test_composite_null_degrade_one_signal():
    assert compute_composite(True, None, None) == 1.0


def test_composite_all_null_zero():
    assert compute_composite(None, None, None) == 0.0


def test_composite_mixed():
    # sem=1 · tests=0 · drift=1.5 (deviation 0.5 · contribute 0.5)
    # (1 + 0 + 0.5) / 3
    assert compute_composite(True, False, drift=1.5) == round((1 + 0 + 0.5) / 3, 3)


# ───────── classify ─────────

@dataclass
class FakeShipResult:
    applied: bool = False
    check_result: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    files_planned: list = field(default_factory=list)


def test_classify_success():
    r = FakeShipResult(applied=True, check_result={"passed": True})
    assert classify(r, tests_pass=True, drift=0.5) == "success"


def test_classify_partial_check_fail():
    r = FakeShipResult(
        applied=True, check_result={"passed": False}, errors=["check failed"]
    )
    assert classify(r, tests_pass=True, drift=0.5) == "partial"


def test_classify_partial_tests_fail():
    r = FakeShipResult(applied=True, check_result={"passed": True})
    assert classify(r, tests_pass=False, drift=0.5) == "partial"


def test_classify_partial_drift_excessive():
    r = FakeShipResult(applied=True, check_result={"passed": True})
    assert classify(r, tests_pass=True, drift=2.0) == "partial"


def test_classify_fail_not_applied():
    r = FakeShipResult(
        applied=False, check_result={"passed": False}, errors=["check failed"]
    )
    assert classify(r, tests_pass=None, drift=None) == "fail"


def test_classify_deadletter_no_blocks():
    r = FakeShipResult(
        applied=False,
        errors=["LLM output had no parseable file blocks (after 1 attempt(s))"],
    )
    assert classify(r, tests_pass=None, drift=None) == "deadletter"


def test_classify_tests_none_does_not_block_success():
    # tests_pass=None (no test files found) should not force partial.
    r = FakeShipResult(applied=True, check_result={"passed": True})
    assert classify(r, tests_pass=None, drift=0.5) == "success"


# ───────── compute_drift_ratio ─────────

def test_drift_exact():
    assert compute_drift_ratio(2, 0, 2, 0) == 1.0


def test_drift_over_shipping():
    assert compute_drift_ratio(10, 0, 2, 0) == 5.0


def test_drift_under_shipping():
    assert compute_drift_ratio(1, 0, 2, 0) == 0.5


def test_drift_null_when_expected_missing():
    assert compute_drift_ratio(2, 0, None, None) is None


def test_drift_null_when_actual_missing():
    assert compute_drift_ratio(None, None, 2, 0) is None


def test_drift_div_zero_safe():
    # expected_added=0 + expected_removed=0 → expected_total=0 · max(1, 0) protects div.
    assert compute_drift_ratio(0, 0, 0, 0) == 0.0


# ───────── is_deadletter ─────────

def test_is_deadletter_true():
    r = FakeShipResult(errors=["LLM output had no parseable file blocks"])
    assert is_deadletter(r) is True


def test_is_deadletter_false():
    r = FakeShipResult(errors=["check failed"])
    assert is_deadletter(r) is False
