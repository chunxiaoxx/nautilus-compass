"""Unit tests for root feedback.py · audit gap closure (plan §C.3).

feedback.py (300 LOC) had zero unit tests prior to this. Covers the four
pieces of online-learning logic the audit flagged:

  1. _normalize_anchor: legacy-str → dict + dict pass-through + defaults
  2. load_alerts / load_feedback: jsonl parsing + dedup + missing-file
  3. cmd_log: append write + invalid verdict exit
  4. _apply_weight_update (extracted from cmd_retrain): FP/TP weight rule

Layout note: placed at tests/test_feedback_core.py (flat) to avoid the
package-shadow trap that bit C.1+C.2 (tests/drift/ shadowing root drift/).
"""
from __future__ import annotations

import argparse
import json

import pytest

from feedback import (
    _apply_weight_update,
    _normalize_anchor,
    cmd_log,
    load_alerts,
    load_feedback,
)


# ============================================================================
# Group 1 · _normalize_anchor
# ============================================================================

def test_normalize_anchor_from_legacy_str():
    """Legacy string anchor → unified dict with default weight=1.0, tp=0, fp=0."""
    n = _normalize_anchor("some anchor text")
    assert n == {"text": "some anchor text", "weight": 1.0, "tp": 0, "fp": 0}


def test_normalize_anchor_from_dict_preserves_fields():
    n = _normalize_anchor({"text": "x", "weight": 1.5, "tp": 3, "fp": 1})
    assert n == {"text": "x", "weight": 1.5, "tp": 3, "fp": 1}


def test_normalize_anchor_dict_missing_fields_defaults():
    n = _normalize_anchor({"text": "x"})
    assert n["weight"] == 1.0
    assert n["tp"] == 0
    assert n["fp"] == 0


def test_normalize_anchor_dict_string_numbers_coerced():
    n = _normalize_anchor({"text": "x", "weight": "0.5", "tp": "2", "fp": "1"})
    assert n["weight"] == 0.5
    assert n["tp"] == 2
    assert n["fp"] == 1


# ============================================================================
# Group 2 · load_alerts / load_feedback
# ============================================================================

def test_load_alerts_filters_drift_alert_event(tmp_path, monkeypatch):
    log = tmp_path / "usage.jsonl"
    log.write_text(
        '{"event": "drift_alert", "alert_id": "a1", "score": -0.05}\n'
        '{"event": "other", "alert_id": "ignored"}\n'
        '{"event": "drift_alert", "alert_id": "a2"}\n'
        "not-json\n"
        '{"event": "drift_alert"}\n',  # no alert_id · ignored
        encoding="utf-8",
    )
    monkeypatch.setattr("feedback.USAGE_LOG", log)
    alerts = load_alerts()
    assert len(alerts) == 2
    assert {a["alert_id"] for a in alerts} == {"a1", "a2"}


def test_load_alerts_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("feedback.USAGE_LOG", tmp_path / "nonexistent.jsonl")
    assert load_alerts() == []


def test_load_feedback_dedups_to_last_verdict(tmp_path, monkeypatch):
    """If same alert_id appears multiple times · last verdict wins (dict overwrite)."""
    log = tmp_path / "feedback.jsonl"
    log.write_text(
        '{"alert_id": "a1", "verdict": "fp"}\n'
        '{"alert_id": "a1", "verdict": "tp"}\n'
        '{"alert_id": "a2", "verdict": "fp"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("feedback.FEEDBACK_LOG", log)
    fb = load_feedback()
    assert fb == {"a1": "tp", "a2": "fp"}


def test_load_feedback_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("feedback.FEEDBACK_LOG", tmp_path / "nonexistent.jsonl")
    assert load_feedback() == {}


# ============================================================================
# Group 3 · cmd_log
# ============================================================================

def test_cmd_log_appends_record_with_verdict(tmp_path, monkeypatch, capsys):
    log = tmp_path / "feedback.jsonl"
    monkeypatch.setattr("feedback.FEEDBACK_LOG", log)
    args = argparse.Namespace(alert_id="a-test", verdict="fp")
    cmd_log(args)
    assert log.exists()
    rec = json.loads(log.read_text(encoding="utf-8").strip())
    assert rec["alert_id"] == "a-test"
    assert rec["verdict"] == "fp"
    assert rec["ts"]  # ISO timestamp set


def test_cmd_log_invalid_verdict_exits_with_error(tmp_path, monkeypatch):
    monkeypatch.setattr("feedback.FEEDBACK_LOG", tmp_path / "feedback.jsonl")
    args = argparse.Namespace(alert_id="a", verdict="invalid")
    with pytest.raises(SystemExit) as exc:
        cmd_log(args)
    assert exc.value.code == 1


def test_cmd_log_creates_parent_dir(tmp_path, monkeypatch):
    """If .cache/ doesn't exist · cmd_log mkdir -p the parent."""
    log = tmp_path / "deep" / "nested" / "feedback.jsonl"
    monkeypatch.setattr("feedback.FEEDBACK_LOG", log)
    args = argparse.Namespace(alert_id="a-mkdir", verdict="tp")
    cmd_log(args)
    assert log.exists()


# ============================================================================
# Group 4 · _apply_weight_update (extracted from cmd_retrain lines 209-216)
# ============================================================================

def test_weight_update_single_fp_decays_weight_70_percent():
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg, fp_anchor_count={"anchor-x"[:60]: 1}, tp_anchor_count={}
    )
    assert out[0]["weight"] == 0.7
    assert out[0]["fp"] == 1


def test_weight_update_single_tp_boosts_weight_10_percent():
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg, fp_anchor_count={}, tp_anchor_count={"anchor-x"[:60]: 1}
    )
    assert round(out[0]["weight"], 3) == 1.1
    assert out[0]["tp"] == 1


def test_weight_update_clamps_at_lower_bound():
    """5 consecutive FPs · 1.0 × 0.7^5 = 0.16807 → 0.168 after round.

    The 0.05 hard clamp does NOT bind here; 0.168 > 0.05. The 0.17
    'deprecated' threshold (cmd_retrain line 229) is a user-facing
    semantic gate, not enforced by clamp.
    """
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg, fp_anchor_count={"anchor-x"[:60]: 5}, tp_anchor_count={}
    )
    assert out[0]["weight"] == 0.168  # 1.0 × 0.7^5 rounded to 3 decimals
    assert out[0]["fp"] == 5


def test_weight_update_clamps_at_upper_bound():
    """Many TPs · weight × 1.1 cannot exceed 2.0."""
    neg = [{"text": "anchor-x", "weight": 1.9, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg, fp_anchor_count={}, tp_anchor_count={"anchor-x"[:60]: 10}
    )
    # 1.9 × 1.1^10 ≈ 4.93 · capped at 2.0
    assert out[0]["weight"] == 2.0


def test_weight_update_clamps_at_extreme_lower_bound():
    """Many FPs · weight cannot fall below 0.05 hard floor.

    1.0 × 0.7^20 ≈ 0.000798 → clamped at 0.05.
    """
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg, fp_anchor_count={"anchor-x"[:60]: 20}, tp_anchor_count={}
    )
    assert out[0]["weight"] == 0.05
    assert out[0]["fp"] == 20


def test_weight_update_combined_fp_and_tp_per_anchor():
    """Both signals applied multiplicatively."""
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(
        neg,
        fp_anchor_count={"anchor-x"[:60]: 2},
        tp_anchor_count={"anchor-x"[:60]: 1},
    )
    # 1.0 × 0.7^2 × 1.1^1 = 0.539
    assert out[0]["weight"] == 0.539
    assert out[0]["fp"] == 2
    assert out[0]["tp"] == 1


def test_weight_update_anchor_not_in_count_unchanged():
    """Anchor with no fp/tp count · weight + counters untouched."""
    neg = [{"text": "anchor-y", "weight": 0.8, "tp": 5, "fp": 2}]
    out = _apply_weight_update(
        neg, fp_anchor_count={"other-anchor": 3}, tp_anchor_count={}
    )
    assert out[0]["weight"] == 0.8
    assert out[0]["tp"] == 5
    assert out[0]["fp"] == 2


def test_weight_update_anchor_keyed_by_first_60_chars():
    """Anchor lookup uses text[:60] · long text matches truncated key."""
    long_text = "a" * 100  # 100 chars
    neg = [{"text": long_text, "weight": 1.0, "tp": 0, "fp": 0}]
    key = long_text[:60]
    out = _apply_weight_update(
        neg, fp_anchor_count={key: 1}, tp_anchor_count={}
    )
    assert out[0]["weight"] == 0.7
    assert out[0]["fp"] == 1


def test_weight_update_returns_same_list_object():
    """Helper mutates in place AND returns the list for chaining."""
    neg = [{"text": "z", "weight": 1.0, "tp": 0, "fp": 0}]
    out = _apply_weight_update(neg, fp_anchor_count={}, tp_anchor_count={})
    assert out is neg


def test_weight_update_accumulates_existing_counters():
    """Prior tp/fp counters are accumulated · not overwritten."""
    neg = [{"text": "anchor-x", "weight": 1.0, "tp": 4, "fp": 2}]
    out = _apply_weight_update(
        neg,
        fp_anchor_count={"anchor-x"[:60]: 1},
        tp_anchor_count={"anchor-x"[:60]: 1},
    )
    assert out[0]["fp"] == 3  # 2 + 1
    assert out[0]["tp"] == 5  # 4 + 1
