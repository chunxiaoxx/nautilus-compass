"""discrimination_jaccard 纯函数门(无 IO)。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops" / "ali30q"))
from discrimination_jaccard import (  # noqa: E402
    fail_set,
    jaccard_distance,
    pair_mean_distance,
    qwen_point_gate,
    signature_gates,
    sota_gap_gate,
)


def test_fail_set_empty_is_allpass() -> None:
    assert fail_set({"a": 1, "b": 1}) == frozenset()
    assert fail_set({"a": 1, "b": 0}) == frozenset({"b"})
    assert fail_set(None) is None
    assert fail_set({}) is None


def test_jaccard_distance_basic() -> None:
    a, b, c = frozenset("ab"), frozenset("ac"), frozenset()
    assert abs(jaccard_distance(a, a) - 0.0) < 1e-12
    # {a,b} vs {a,c}: intersect 1 union 3 → dist 2/3
    assert abs(jaccard_distance(a, b) - (2 / 3)) < 1e-12
    assert jaccard_distance(a, c) == 1.0
    assert jaccard_distance(c, c) == 0.0


def test_qwen_point_only_25_or_50() -> None:
    assert qwen_point_gate(0.25, 4)["status"] == "PASS"
    assert qwen_point_gate(0.50, 4)["status"] == "PASS"
    assert qwen_point_gate(0.0, 4)["status"] == "FAIL"
    assert qwen_point_gate(0.75, 4)["status"] == "FAIL"
    assert qwen_point_gate(1.0, 4)["status"] == "FAIL"
    assert qwen_point_gate(0.25, 2)["status"] == "UNVERIFIED"


def test_sota_gap_requires_two_legs() -> None:
    g = sota_gap_gate(0.25, {"opus5.5": (0.75, 4), "gpt-6-astra": (0.50, 4)})
    assert g["status"] == "PASS"  # mean 0.625-0.25=0.375>0.20
    g2 = sota_gap_gate(0.50, {"opus5.5": (0.50, 4), "gpt-6-astra": (0.50, 4)})
    assert g2["status"] == "FAIL"
    g3 = sota_gap_gate(0.0, {"opus5.5": (0.75, 4), "gpt-6-astra": (None, 0)})
    assert g3["status"] == "UNVERIFIED"


def _run(model: str, fails: set[str]) -> dict:
    return {
        "model": model,
        "usable": True,
        "fail_set": frozenset(fails),
        "binary": 0 if fails else 1,
    }


def test_signature_diversity_and_ratio() -> None:
    # 同模型失败集相近(intra 低)、跨模型相远(cross≈1) → ratio≥1.25
    runs = [
        _run("qwen3.8max", {"t1", "t2"}),
        _run("qwen3.8max", {"t1"}),
        _run("opus5.5", {"t9"}),
        _run("opus5.5", {"t8"}),
    ]
    g = signature_gates(runs)
    assert g["diversity_pass"] is True
    assert g["max_share_pass"] is True
    assert g["n_non_allpass"] == 4
    assert g["jaccard_status"] == "PASS"
    assert g["status"] == "PASS"


def test_signature_same_fail_collapses() -> None:
    runs = [_run("qwen3.8max", {"t1"}) for _ in range(4)]
    g = signature_gates(runs)
    assert g["diversity_pass"] is False  # 1/4 < 0.5
    assert g["max_share_pass"] is False  # 4/4 > 0.5
    assert g["status"] == "FAIL"


def test_allpass_skipped_unverifiable() -> None:
    runs = [_run("opus5.5", set()) for _ in range(4)]
    g = signature_gates(runs)
    assert g["status"] == "UNVERIFIED"
    assert g["n_non_allpass"] == 0


def test_pair_mean_needs_two() -> None:
    assert pair_mean_distance([frozenset("a")]) is None
    d = pair_mean_distance([frozenset("a"), frozenset("a")])
    assert d == 0.0
