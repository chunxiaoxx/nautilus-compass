"""gate B GPU verifier 纯逻辑 TDD(6/17 晚·KernelBench 燃料自动判分·fast1 门)。

V5 produce 出 KernelBench kernel 后,fde_bench_poll 需把它 scp 到 T4 跑 kb_eval
(GPU·非本机 CPU)→ 出 verdict。本测试覆盖纯逻辑:
  - is_kernelbench_task: desc 有 kb_problem_id → 走 GPU 经路
  - fast1_verdict_from_kb_eval: kb_eval 结果 → verify_fn 契约(fast1 门)

fast1 门(soul 6/17 裁定): passed = pass_final AND speedup>1(窗口 1<su≤2·>2× 被 G2 挡)。
GPU scp/ssh 执行是 effect seam(注入·不单测)。
"""
import json

from services.fde_bench_runner import is_kernelbench_task, fast1_verdict_from_kb_eval


def _kb_task(pid=13, level=2):
    desc = json.dumps({"fde_class": 3, "kind": "code-fix-with-deterministic-verifier",
                       "task_family": "kernelbench-stump", "kb_level": level,
                       "kb_problem_id": pid, "fast1": True})
    return {"task_uid": "kb_l%d_p%d_x" % (level, pid), "description": desc, "output": "code"}


def test_is_kernelbench_task_true_when_kb_problem_id():
    assert is_kernelbench_task(_kb_task()) is True


def test_is_kernelbench_task_false_for_cpu_bench():
    cpu = {"task_uid": "huffman_x",
           "description": json.dumps({"fde_class": 3, "verifier_inline": "..."}),
           "output": "code"}
    assert is_kernelbench_task(cpu) is False


def test_fast1_pass_correct_and_fast():
    kb = {"pass_final": True, "speedup_vs_eager": 1.6, "reason": "pass"}
    v = fast1_verdict_from_kb_eval(kb, "h1", fast1=True)
    assert v["ok"] is True and v["passed"] is True and v["reward"] == 1.0


def test_fast1_fail_correct_but_slow():
    kb = {"pass_final": True, "speedup_vs_eager": 0.73, "reason": "pass"}
    v = fast1_verdict_from_kb_eval(kb, "h2", fast1=True)
    assert v["ok"] is True and v["passed"] is False and v["reward"] == 0.0
    assert "slow" in v["reason"].lower() or "0.73" in v["reason"]


def test_fast1_fail_incorrect():
    kb = {"pass_final": False, "speedup_vs_eager": None, "reason": "official_eval_fail"}
    v = fast1_verdict_from_kb_eval(kb, "h3", fast1=True)
    assert v["ok"] is True and v["passed"] is False and v["reward"] == 0.0


def test_gpu_eval_error_is_ok_false_retry():
    kb = {"error": "scp_fail: Connection reset"}
    v = fast1_verdict_from_kb_eval(kb, "h4", fast1=True)
    assert v["ok"] is False and v["passed"] is False


def test_correctness_mode_ignores_speedup():
    kb = {"pass_final": True, "speedup_vs_eager": 0.73, "reason": "pass"}
    v = fast1_verdict_from_kb_eval(kb, "h5", fast1=False)
    assert v["passed"] is True and v["reward"] == 1.0


def test_verdict_carries_sol_hash_and_source():
    kb = {"pass_final": True, "speedup_vs_eager": 1.3}
    v = fast1_verdict_from_kb_eval(kb, "abc123", fast1=True)
    assert v["sol_hash"] == "abc123" and v["source"] == "compass/bench_eval"
