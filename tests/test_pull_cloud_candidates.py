"""Tests for ops/pull_cloud_candidates.py · cloud->local candidate dedup-merge."""
from __future__ import annotations

from pathlib import Path
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "pull_cloud", Path(__file__).resolve().parent.parent / "ops" / "pull_cloud_candidates.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def test_merge_dedups_exact_lines():
    existing = ['{"a":1}', '{"b":2}']
    incoming = ['{"b":2}', '{"c":3}']
    out = _MOD.merge_candidate_lines(existing, incoming)
    assert out == ['{"a":1}', '{"b":2}', '{"c":3}']  # order preserved, dup dropped


def test_merge_ignores_blank_lines():
    out = _MOD.merge_candidate_lines(['{"a":1}', ''], ['', '{"d":4}'])
    assert out == ['{"a":1}', '{"d":4}']


def test_merge_empty_existing():
    assert _MOD.merge_candidate_lines([], ['{"x":1}']) == ['{"x":1}']


def test_merge_empty_incoming_keeps_existing():
    assert _MOD.merge_candidate_lines(['{"x":1}'], []) == ['{"x":1}']


def test_merge_strips_whitespace_for_dedup():
    out = _MOD.merge_candidate_lines(['{"a":1}'], ['  {"a":1}  '])
    assert out == ['{"a":1}']
