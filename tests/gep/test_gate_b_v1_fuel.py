"""Gate B real-fuel spec: compass_exp_v1 (data freshness / staleness boundary).

Fuel provenance: cloud /home/ubuntu/auto-mint/fuel/v1_data_freshness_staleness/
(task_spec + buggy_ingest.py + deterministic bench_eval), ledger row 2 (consumed 2026-08-22).
Headroom design: the boundary caliber (exactly-at-age == fresh, strictly older == stale)
is stated ONLY in the source experience; the transfer prompt deliberately omits it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gep.live_coding_adapter import (
    _valid_v1_source_rule,
    _valid_v1_transfer,
    load_value_suite,
)

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite_v1_fuel_v1.json"


class TestV1SourceRule:
    def test_accepts_full_rule(self) -> None:
        assert _valid_v1_source_rule(
            "Compare now - ts against max_age: records exactly at max_age are still fresh; "
            "strictly older (now - ts > max_age) are stale and must be rejected, never "
            "accepted just because payload is non-empty."
        )

    def test_rejects_missing_boundary(self) -> None:
        assert not _valid_v1_source_rule("check that data is fresh before accepting it")

    def test_rejects_non_string(self) -> None:
        assert not _valid_v1_source_rule(None)


class TestV1Transfer:
    def test_accepts_correct_boundary(self) -> None:
        assert _valid_v1_transfer("now - ts <= max_age")

    def test_rejects_off_by_one(self) -> None:
        assert not _valid_v1_transfer("now - ts < max_age")

    def test_rejects_wrong_direction(self) -> None:
        assert not _valid_v1_transfer("ts - now <= max_age")

    def test_rejects_abs_form(self) -> None:
        assert not _valid_v1_transfer("abs(now - ts) <= max_age")

    def test_rejects_non_expression(self) -> None:
        assert not _valid_v1_transfer("def f(now, ts, max_age): return True")

    def test_rejects_non_string(self) -> None:
        assert not _valid_v1_transfer(1)


class TestV1Suite:
    def test_suite_loads(self) -> None:
        suite = load_value_suite(SUITE)
        assert suite.suite_id == "compass-exp-v1-freshness-v1"
        assert suite.loop_plan["task"]["cases"]["transfer"]["prompt"]
        # headroom design: transfer prompt must NOT leak the boundary caliber
        tp = suite.loop_plan["task"]["cases"]["transfer"]["prompt"].lower()
        # 泄漏 = 给出边界口径;泛词 exactly(如 "True exactly when")不算
        for leak in ("exactly at", "恰好到龄", "at the age", "boundary caliber", "== max_age", "equal to max_age"):
            assert leak not in tp, leak
