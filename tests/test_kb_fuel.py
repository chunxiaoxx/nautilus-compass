"""TDD for kernelbench/kb_fuel.py · 纯函数·无需 live KernelBench / GPU。

镜像 tests/test_ale_eval.py 的导入约定。契约逐键匹配 V5
nautilus-v5/fde_capsule/ale_fuel_batch.py(下游 ingest_fuel_records 零改)。
GPU seam(真 eval)后续单独加,本套只覆盖纯函数部分。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kernelbench"))
import kb_fuel  # noqa: E402


def test_build_sample_has_6_keys_and_maps_speedup():
    s = kb_fuel.build_kb_fuel_sample(
        task_id="kb_attention",
        problem_statement="fused attention kernel ...",
        strong_result={"solution": "class ModelNew...", "speedup": 1.727, "verified": True},
        doubao_speedup=0.0,
    )
    assert s["task_id"] == "kb_attention"
    assert s["strong_score"] == 1.727
    assert s["doubao_score"] == 0.0
    assert s["strong_verified"] is True
    assert s["score_type"] == "maximize"
    assert s["strong_solution"].startswith("class ModelNew")
    for k in ("task_id", "problem_statement", "strong_solution", "strong_score", "doubao_score", "strong_verified"):
        assert k in s


def test_a_class_true_when_strong_beats_doubao():
    s = kb_fuel.build_kb_fuel_sample("t", "p", {"solution": "x", "speedup": 1.727, "verified": True}, 0.747)
    assert kb_fuel.is_a_class(s) is True


def test_a_class_false_double_fail_same_score():
    s = kb_fuel.build_kb_fuel_sample("t", "p", {"solution": "x", "speedup": 0.0, "verified": True}, 0.0)
    assert kb_fuel.is_a_class(s) is False


def test_a_class_false_strong_zero():
    s = kb_fuel.build_kb_fuel_sample("t", "p", {"solution": "x", "speedup": 0.0, "verified": True}, -1.0)
    assert kb_fuel.is_a_class(s) is False


def test_a_class_false_not_verified():
    s = kb_fuel.build_kb_fuel_sample("t", "p", {"solution": "x", "speedup": 2.0, "verified": False}, 0.5)
    assert kb_fuel.is_a_class(s) is False


def test_a_class_false_margin_too_small():
    s = kb_fuel.build_kb_fuel_sample("t", "p", {"solution": "x", "speedup": 1.05, "verified": True}, 1.0)
    assert kb_fuel.is_a_class(s) is False


def test_accumulate_dedup_keeps_higher_speedup():
    a = kb_fuel.build_kb_fuel_sample("t1", "p", {"solution": "v1", "speedup": 1.2, "verified": True}, 0.5)
    b = kb_fuel.build_kb_fuel_sample("t1", "p", {"solution": "v2", "speedup": 1.8, "verified": True}, 0.5)
    c = kb_fuel.build_kb_fuel_sample("t2", "p", {"solution": "x", "speedup": 1.0, "verified": True}, 0.5)
    out = kb_fuel.accumulate_kb_fuel([b, c], existing=[a])
    by = {s["task_id"]: s for s in out}
    assert by["t1"]["strong_score"] == 1.8
    assert by["t2"]["strong_score"] == 1.0
    assert len(out) == 2
