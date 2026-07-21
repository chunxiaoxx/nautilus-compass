#!/usr/bin/env python3
"""TDD · runtime lifecycle signal policy defaults and support gates."""
from __future__ import annotations

from recall_pkg.lifecycle_policy import (
    DEFAULT_SIGNAL_POLICY,
    get_recall_signal_policy,
    is_lifecycle_query,
    should_apply_poi_weight,
    should_apply_tier_weight,
)


def _hit(name: str, tier: str = "working") -> tuple:
    return (0.5, {"fullpath": f"/h/.claude/projects/proj/memory/{name}", "tier": tier})


def test_default_recall_signal_policy_is_guarded():
    assert DEFAULT_SIGNAL_POLICY == "flat"
    assert get_recall_signal_policy({}) == "flat"


def test_invalid_policy_falls_back_to_guarded():
    assert get_recall_signal_policy({"COMPASS_RECALL_SIGNAL_POLICY": "unsafe"}) == "flat"


def test_flat_policy_disables_lifecycle_weights():
    top = [_hit("a.md", tier="semantic"), _hit("b.md", tier="episodic"), _hit("c.md", tier="procedural")]
    snapshot = {"proj/a.md": 1.0, "proj/b.md": 1.0, "proj/c.md": 1.0}
    assert should_apply_poi_weight("flat", top, snapshot) is False
    assert should_apply_tier_weight("flat", top) is False


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


def test_routed_policy_applies_only_for_lifecycle_queries_with_support():
    top = [_hit("a.md"), _hit("b.md"), _hit("c.md"), _hit("d.md")]
    snapshot = {"proj/a.md": 1.0, "proj/b.md": 1.0, "proj/c.md": 1.0}

    assert is_lifecycle_query("How did the recall policy gate behave after C5?") is True
    assert is_lifecycle_query("Where is the BioMysteryBench delivery zip?") is False
    assert should_apply_poi_weight("routed", top, snapshot, query="recall policy gate result") is True
    assert should_apply_poi_weight("routed", top, snapshot, query="ordinary delivery question") is False


def test_routed_policy_applies_tier_only_for_lifecycle_queries_with_support():
    tiered = [
        _hit("a.md", tier="semantic"),
        _hit("b.md", tier="episodic"),
        _hit("c.md", tier="procedural"),
        _hit("d.md"),
    ]
    assert should_apply_tier_weight("routed", tiered, query="release preflight outcome") is True
    assert should_apply_tier_weight("routed", tiered, query="normal project status") is False
