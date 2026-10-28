"""P1.2 双门自治编排 TDD(2026-06-20)。

run_double_gate 纯编排:候选 → gate A(诊断分桶)→ gate B(仅对 true_wall·省算力)
→ classify_distillation_fuel → route_bucket。gate_a_fn/gate_b_fn/mint_fn/write_delivery_fn 注入。
load_fuel_candidate 从燃料目录(task_spec.md + buggy_*.py + bench_eval.py + task_family.txt)读候选。
"""
import json
import os
import tempfile

from services.fde_double_gate_poll import run_double_gate, load_fuel_candidate


def _cand(uid, pid=13):
    return {"task_uid": uid, "title": "t-%s" % uid, "spec": "spec", "starter": "code",
            "verifier": "v", "bench_family": "kernelbench-stump",
            "kb_level": 2, "kb_problem_id": pid, "fast1": True, "prompt": "p"}


class _Harness:
    """注入式 effect 记录器 + 可编程 gate 结果。"""

    def __init__(self, a_diag, strong_map):
        self.a_diag = a_diag          # {uid: diag}
        self.strong_map = strong_map  # {uid: bool}
        self.gate_a_calls, self.gate_b_calls = [], []
        self.mints, self.delivers = [], []

    def gate_a_fn(self, cand):
        self.gate_a_calls.append(cand["task_uid"])
        return self.a_diag[cand["task_uid"]]

    def gate_b_fn(self, true_wall):
        self.gate_b_calls.append([c["task_uid"] for c in true_wall])
        return [{"task_uid": c["task_uid"],
                 "strong_model_passed": self.strong_map.get(c["task_uid"]),
                 "which_model": "qwen3.7-max" if self.strong_map.get(c["task_uid"]) else None}
                for c in true_wall]

    def mint_fn(self, uid, title, desc):
        self.mints.append({"uid": uid, "desc": desc})
        return {"status": "open"}

    def write_delivery_fn(self, payload):
        self.delivers.append(payload)
        return {"record_id": "r%d" % len(self.delivers)}

    def go(self, cands):
        return run_double_gate(cands, gate_a_fn=self.gate_a_fn, gate_b_fn=self.gate_b_fn,
                               mint_fn=self.mint_fn, write_delivery_fn=self.write_delivery_fn)


_TRUE_WALL = {"n_samples": 50, "n_passed": 0, "n_correct_but_gated": 0}
_TOO_EASY = {"n_samples": 50, "n_passed": 40, "n_correct_but_gated": 0}
_GATE_ART = {"n_samples": 50, "n_passed": 0, "n_correct_but_gated": 7}


def test_true_wall_plus_strong_pass_mints_fuel():
    h = _Harness({"a": _TRUE_WALL}, {"a": True})
    out = h.go([_cand("a")])
    res = out["results"][0]
    assert res["action"] == "mint+deliver" and res["bucket"] == "distillation_fuel"
    assert len(h.mints) == 1 and len(h.delivers) == 1
    assert json.loads(h.mints[0]["desc"])["task_family"] == "distillation_fuel"


def test_true_wall_strong_fail_is_buyer_stump():
    h = _Harness({"a": _TRUE_WALL}, {"a": False})
    out = h.go([_cand("a")])
    res = out["results"][0]
    assert res["action"] == "deliver" and res["bucket"] == "buyer_stump"
    assert len(h.mints) == 0 and len(h.delivers) == 1


def test_too_easy_drops_and_skips_gate_b():
    h = _Harness({"a": _TOO_EASY}, {})
    out = h.go([_cand("a")])
    assert out["results"][0]["action"] == "drop"
    assert h.gate_b_calls == []          # gate B 不对 non-true_wall 跑(省算力)
    assert len(h.mints) == 0 and len(h.delivers) == 0


def test_gate_artifact_drops():
    h = _Harness({"a": _GATE_ART}, {})
    out = h.go([_cand("a")])
    assert out["results"][0]["action"] == "drop"
    assert h.gate_b_calls == []


def test_gate_b_only_called_for_true_wall_subset():
    h = _Harness({"a": _TRUE_WALL, "b": _TOO_EASY, "c": _TRUE_WALL},
                 {"a": True, "c": False})
    out = h.go([_cand("a"), _cand("b"), _cand("c")])
    # gate B 一次·只含 true_wall 的 a,c(不含 too_easy 的 b)
    assert len(h.gate_b_calls) == 1
    assert set(h.gate_b_calls[0]) == {"a", "c"}
    acts = out["summary"]["actions"]
    assert acts.get("mint+deliver") == 1 and acts.get("deliver") == 1 and acts.get("drop") == 1


def test_summary_totals():
    h = _Harness({"a": _TRUE_WALL}, {"a": True})
    out = h.go([_cand("a")])
    assert out["summary"]["total"] == 1


def test_load_fuel_candidate_parses_dir():
    with tempfile.TemporaryDirectory() as d:
        fuel = os.path.join(d, "kernelbench-stump-p13")
        os.makedirs(fuel)
        open(os.path.join(fuel, "task_spec.md"), "w", encoding="utf-8").write(
            "# KernelBench L2 p13 · ConvTranspose3d\n正文")
        open(os.path.join(fuel, "buggy_starter.py"), "w", encoding="utf-8").write("class Model: pass")
        open(os.path.join(fuel, "bench_eval.py"), "w", encoding="utf-8").write("print('{}')")
        open(os.path.join(fuel, "task_family.txt"), "w", encoding="utf-8").write("kernelbench-stump\n")
        c = load_fuel_candidate(fuel)
        assert c["bench_family"] == "kernelbench-stump"
        assert c["kb_problem_id"] == 13 and c["kb_level"] == 2
        assert c["starter"].strip() and c["verifier"].strip() and c["spec"].strip()
        assert c["task_uid"] == "kb_l2_p13"
