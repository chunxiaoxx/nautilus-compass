"""R6 TensionMeter smoke test · feel_think = 真实工具失败率"""
from __future__ import annotations
import pytest
from nautilus_core.tension import (
    TensionMeter, TensionReading, StaticToolCallSource,
)


def test_all_success_high_harmony():
    rows = [{"success": True, "elapsed_ms": 1000} for _ in range(10)]
    m = TensionMeter("ag-1", StaticToolCallSource(rows))
    r = m.measure()
    assert r.harmony == 1.0
    assert r.pain == 0.0
    assert r.pace == "fast"
    assert r.sample_size == 10


def test_all_failure_high_pain():
    rows = [{"success": False, "elapsed_ms": 8000} for _ in range(10)]
    m = TensionMeter("ag-1", StaticToolCallSource(rows))
    r = m.measure()
    assert r.harmony == 0.0
    assert r.pain == 1.0
    assert r.pace == "slow"


def test_mixed_returns_correct_ratio():
    rows = (
        [{"success": True, "elapsed_ms": 2000} for _ in range(7)] +
        [{"success": False, "elapsed_ms": 3000} for _ in range(3)]
    )
    m = TensionMeter("ag-1", StaticToolCallSource(rows))
    r = m.measure()
    assert r.harmony == pytest.approx(0.7)
    assert r.pain == pytest.approx(0.3)
    assert r.pace == "normal"  # avg 2300ms 在 1500-5000 之间


def test_no_rows_returns_neutral():
    m = TensionMeter("ag-1", StaticToolCallSource([]))
    r = m.measure()
    assert r.harmony == 0.5
    assert r.pain == 0.5
    assert r.pace == "normal"
    assert r.sample_size == 0


def test_window_limits_sample():
    rows = [{"success": True, "elapsed_ms": 100} for _ in range(100)]
    m = TensionMeter("ag-1", StaticToolCallSource(rows), window=20)
    r = m.measure()
    assert r.sample_size == 20


def test_prompt_hint_format():
    r = TensionReading(harmony=0.82, pain=0.18, pace="fast", sample_size=50, avg_elapsed_ms=1200)
    hint = r.prompt_hint()
    assert "pain 0.18" in hint
    assert "harmony 0.82" in hint
    assert "fast" in hint
    assert "(高)" in hint or "(低)" in hint


def test_prompt_hint_high_pain():
    r = TensionReading(harmony=0.2, pain=0.8, pace="slow", sample_size=50, avg_elapsed_ms=6000)
    hint = r.prompt_hint()
    assert "(高)" in hint  # pain 高
    assert "slow" in hint
