"""TDD — services.fde_strong_gate(Gate B = 强模型解门·P1 keystone·2026-06-20)。

双门一鱼两吃的 gate B:接 gate-A 的 true_wall 题(doubao 0/k 难倒)→ 遍历强模型
（qwen3.7-max/GLM5.2/deepseek4.0pro）→ 各自 produce+eval → ≥1 解出 = strong_model_passed
=True(有干净 correct trace 可蒸馏=bucket-A 燃料)· 全不解 = False(buyer_stump=护城河)。

纯编排·complete_fn(prompt,model→code) + eval_fn(code,task→{passed}) 注入 → mock 可测·
不碰真 bailian API / GPU。复用 fde_triage.classify_distillation_fuel 出最终桶。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_strong_gate import run_strong_model_gate  # noqa: E402


def _make_fns(solve_map):
    """solve_map: {(task_uid, model): passed_bool} → (complete_fn, eval_fn) + 调用计数。"""
    calls = {"complete": 0, "eval": 0}

    def complete_fn(prompt, model):
        calls["complete"] += 1
        # code 串里编码 model·让 eval_fn 还原(测里不跑真代码）
        return "MODEL=%s\n%s" % (model, prompt[:20])

    def eval_fn(code, task):
        calls["eval"] += 1
        model = code.split("\n")[0].replace("MODEL=", "")
        passed = solve_map.get((task["task_uid"], model), False)
        return {"passed": passed}

    return complete_fn, eval_fn, calls


def test_one_strong_model_solves_marks_fuel():
    # qwen 解出·deepseek 不解 → strong_model_passed=True·which=qwen(短路·不再试 deepseek）
    tasks = [{"task_uid": "kb_p13", "prompt": "fix this"}]
    solve = {("kb_p13", "qwen3.7-max"): True}
    complete_fn, eval_fn, calls = _make_fns(solve)
    out = run_strong_model_gate(tasks, ["qwen3.7-max", "deepseek4.0pro"], complete_fn, eval_fn)
    assert len(out) == 1
    assert out[0]["task_uid"] == "kb_p13"
    assert out[0]["strong_model_passed"] is True
    assert out[0]["which_model"] == "qwen3.7-max"
    assert calls["eval"] == 1  # ≥1 解出即短路·省算力


def test_no_strong_model_solves_is_buyer_stump():
    # 全不解 → strong_model_passed=False(buyer_stump·护城河）·试满所有模型
    tasks = [{"task_uid": "kb_p14", "prompt": "hard"}]
    complete_fn, eval_fn, calls = _make_fns({})
    out = run_strong_model_gate(tasks, ["qwen3.7-max", "deepseek4.0pro"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is False
    assert out[0]["which_model"] is None
    assert calls["eval"] == 2  # 试满


def test_second_model_solves_when_first_fails():
    tasks = [{"task_uid": "t", "prompt": "p"}]
    solve = {("t", "deepseek4.0pro"): True}
    complete_fn, eval_fn, calls = _make_fns(solve)
    out = run_strong_model_gate(tasks, ["qwen3.7-max", "deepseek4.0pro"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is True and out[0]["which_model"] == "deepseek4.0pro"


def test_multiple_tasks_independent():
    tasks = [{"task_uid": "a", "prompt": "x"}, {"task_uid": "b", "prompt": "y"}]
    solve = {("a", "qwen3.7-max"): True}  # a 解出·b 不解
    complete_fn, eval_fn, _ = _make_fns(solve)
    out = run_strong_model_gate(tasks, ["qwen3.7-max"], complete_fn, eval_fn)
    by = {r["task_uid"]: r for r in out}
    assert by["a"]["strong_model_passed"] is True
    assert by["b"]["strong_model_passed"] is False


def test_eval_exception_is_inconclusive_not_buyer_stump():
    # eval_fn 抛错(GPU 崩等）→ 一次都没真评出 → strong_model_passed=None(inconclusive·
    # 🔴 不能当 False=buyer_stump·6/20 OOM facade bug 修正）·fail-soft 不中断
    tasks = [{"task_uid": "t", "prompt": "p"}]

    def complete_fn(prompt, model):
        return "code"

    def eval_fn(code, task):
        raise RuntimeError("gpu oom")

    out = run_strong_model_gate(tasks, ["qwen3.7-max"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is None
    assert "error" in out[0]["per_model"][0]


def test_eval_ok_false_is_inconclusive():
    # eval 返 ok=False(GPU OOM no_json·基础设施错·非真判)→ inconclusive None
    tasks = [{"task_uid": "t", "prompt": "p"}]

    def complete_fn(prompt, model):
        return "code"

    def eval_fn(code, task):
        return {"ok": False, "passed": False, "reason": "no_json"}

    out = run_strong_model_gate(tasks, ["qwen3.7-max"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is None
    assert "no_json" in out[0]["per_model"][0].get("error", "")


def test_genuine_fail_is_false():
    # eval 真跑出结论(ok 缺省=真评）但 passed=False → genuine fail → False(buyer_stump）
    tasks = [{"task_uid": "t", "prompt": "p"}]
    complete_fn, eval_fn, _ = _make_fns({})
    out = run_strong_model_gate(tasks, ["qwen3.7-max"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is False


def test_ok_false_then_pass_is_true():
    # 一模型 OOM(ok=False)·另一模型真解出 → True(真评优先）
    tasks = [{"task_uid": "t", "prompt": "p"}]

    def complete_fn(prompt, model):
        return "MODEL=%s" % model

    def eval_fn(code, task):
        model = code.replace("MODEL=", "")
        if model == "qwen3.7-max":
            return {"ok": False, "reason": "oom"}
        return {"passed": True}

    out = run_strong_model_gate(tasks, ["qwen3.7-max", "deepseek4.0pro"], complete_fn, eval_fn)
    assert out[0]["strong_model_passed"] is True and out[0]["which_model"] == "deepseek4.0pro"


def test_k_samples_per_model():
    # k>1:同模型采 k 次·任一解出即算该模型解出(best-of-k）
    tasks = [{"task_uid": "t", "prompt": "p"}]
    # 用计数让第 2 次采样才解出
    state = {"n": 0}

    def complete_fn(prompt, model):
        state["n"] += 1
        return "attempt%d" % state["n"]

    def eval_fn(code, task):
        return {"passed": code == "attempt2"}

    out = run_strong_model_gate(tasks, ["qwen3.7-max"], complete_fn, eval_fn, k=3)
    assert out[0]["strong_model_passed"] is True
