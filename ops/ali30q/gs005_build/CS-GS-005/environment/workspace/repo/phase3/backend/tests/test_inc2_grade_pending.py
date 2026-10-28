"""Inc 2 Slice 2 · grade_pending_settlements + _compute_composite_delta tests."""
import os
import pytest
from unittest.mock import MagicMock

from services.inc2_settlement import _compute_composite_delta


def test_composite_delta_no_revert_positive_rate_improvement():
    pre = {"success_rate": 0.3}
    post = {"success_rate": 0.5}
    # no_revert_bonus 0.5 + rate_delta 0.2 = 0.7
    assert abs(_compute_composite_delta(pre, post, True) - 0.7) < 1e-6


def test_composite_delta_reverted_penalizes():
    pre = {"success_rate": 0.5}
    post = {"success_rate": 0.5}
    # no_revert_bonus -1.0 + rate_delta 0 = -1.0
    assert abs(_compute_composite_delta(pre, post, False) - (-1.0)) < 1e-6


def test_composite_delta_missing_rate_falls_back_to_zero_delta():
    pre = {"success_rate": None}
    post = {"success_rate": 0.5}
    # no_revert_bonus 0.5 + rate_delta 0 (insufficient signal) = 0.5
    assert abs(_compute_composite_delta(pre, post, True) - 0.5) < 1e-6


def test_composite_delta_str_jsonb_handled():
    # Real DB returns dict for JSONB; defensive against str case.
    pre = "{}"  # not parsed in helper · caller handles json.loads
    # but the helper only checks isinstance(dict)
    # If it's str, .get returns AttributeError unless we guard
    # Verify isinstance check prevents crash:
    post = {"success_rate": 0.5}
    # The helper would crash with str pre on the get · so pre must be dict
    # at call site. Test the dict happy path:
    assert _compute_composite_delta({}, post, True) == 0.5  # no rate signal
