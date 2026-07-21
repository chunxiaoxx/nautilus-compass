#!/usr/bin/env python3
"""TDD · runtime lifecycle signal policy defaults and support gates."""
from __future__ import annotations

from recall_pkg.lifecycle_policy import (
    DEFAULT_SIGNAL_POLICY,
    get_recall_signal_policy,
    should_apply_poi_weight,
    should_apply_tier_weight,
)


def _hit(name: str, tier: str = "working") -> tuple:
    return (0.5, {"fullpath": f"/h/.claude/projects/proj/memory/{name}", "tier": tier})


def test_default_recall_signal_policy_is_guarded():
    assert DEFAULT_SIGNAL_POLICY == "guarded"
    assert get_recall_signal_policy({}) == "guarded"


def test_invalid_policy_falls_back_to_guarded():
    assert get_recall_signal_policy({"COMPASS_RECALL_SIGNAL_POLICY": "unsafe"}) == "guarded"


def test_raw_policy_applies_lifecycle_weights_without_support_gate():
    top = [_hit("a.md")]
    assert should_apply_poi_weight("raw", top, {"proj/a.md": 1.0}) is True
    assert should_apply_tier_weight("raw", [_hit("a.md", tier="semantic")]) is True


def test_guarded_policy_skips_sparse_lifecycle_signals():
    top = [_hit("a.md"), _hit("b.md")]
    assert should_apply_poi_weight("guarded", top, {"proj/a.md": 1.0}) is False
    assert should_apply_tier_weight("guarded", [_hit("a.md", tier="semantic"), _hit("b.md")]) is False


def test_guarded_policy_applies_lifecycle_weights_when_support_is_sufficient():
    top = [_hit("a.md"), _hit("b.md"), _hit("c.md"), _hit("d.md")]
    snapshot = {"proj/a.md": 1.0, "proj/b.md": 1.0, "proj/c.md": 1.0}
    assert should_apply_poi_weight("guarded", top, snapshot) is True

    tiered = [
        _hit("a.md", tier="semantic"),
        _hit("b.md", tier="episodic"),
        _hit("c.md", tier="procedural"),
        _hit("d.md"),
    ]
    assert should_apply_tier_weight("guarded", tiered) is True
