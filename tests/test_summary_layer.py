"""Cross-session summary layer (preregistration 2026-09-02) unit tests.

Covers: chronological card ordering, soft fallback when cards are missing,
default-off gate, and routing precedence (summary > ssu-utterance > session).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HARNESS = Path(__file__).parent / "eval_longmemeval_accuracy.py"


def _load():
    spec = importlib.util.spec_from_file_location("eval_lm_harness", _HARNESS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_sessions():
    return [
        [{"role": "user", "content": "I bought a lemon tree yesterday"}],
        [{"role": "user", "content": "I need to pick up my navy blazer"}],
    ]


def test_timeline_chronological_and_sections():
    h = _load()
    h._SUMMARY_CARDS = {
        "sB": "USER FACTS:\n- bought lemon tree\nTOPICS: garden",
        "sA": "USER FACTS:\n- pick up navy blazer\nTOPICS: errands",
    }
    ctx = h.build_summary_context(
        _fake_sessions(), ["sB", "sA"],
        ["2023-01-22", "2023-01-15"], "what errands?", reranker=None)
    assert ctx.startswith("=== Session Timeline")
    assert ctx.find("sA") < ctx.find("sB"), "older session must come first"
    assert "=== Evidence Extracts ===" in ctx


def test_fallback_when_no_cards():
    h = _load()
    h._SUMMARY_CARDS = {}
    ctx = h.build_summary_context(
        _fake_sessions(), ["sB", "sA"], None, "q", reranker=None)
    assert "Session Timeline" not in ctx
    assert "Utterance" in ctx, "must degrade to utterance path, not crash"


def test_partial_cards_degrade_to_remaining():
    h = _load()
    h._SUMMARY_CARDS = {"sA": "USER FACTS:\n- x\nTOPICS: t"}
    ctx = h.build_summary_context(
        _fake_sessions(), ["sB", "sA"], ["2023-01-22", "2023-01-15"],
        "q", reranker=None)
    # sB missing from cards: timeline has sA only, evidence still present
    assert "sA" in ctx and "sB" not in ctx.split("Evidence")[0]
    assert "Evidence Extracts" in ctx


def test_gate_defaults_off():
    h = _load()
    assert h.ZMM_SUMMARY_LAYER is False
    assert h.SUMMARY_TYPES == {
        "multi-session", "temporal-reasoning", "single-session-assistant"}
    # ssu/ssp/ku are NOT in the routed set — near-ceiling types untouched
    assert "single-session-user" not in h.SUMMARY_TYPES
    assert "knowledge-update" not in h.SUMMARY_TYPES


def test_none_dates_sort_last():
    h = _load()
    h._SUMMARY_CARDS = {
        "sN": "USER FACTS:\n- no date\nTOPICS: t",
        "sA": "USER FACTS:\n- dated\nTOPICS: t",
    }
    ctx = h.build_summary_context(
        _fake_sessions(), ["sN", "sA"], [None, "2023-01-01"],
        "q", reranker=None)
    assert ctx.find("sA") < ctx.find("sN"), "dated cards first, undated last"
