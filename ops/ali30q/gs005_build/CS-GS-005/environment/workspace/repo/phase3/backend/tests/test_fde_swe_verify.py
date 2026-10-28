"""P1.3b SWE verify-side 纯逻辑 TDD(2026-06-20)。

SWE 燃料(kind=swe-rsi-fuel)的 produce(patch)→ swebench harness(GPU box·非 T4)→ verdict。
is_swe_task 路由 + swe_verdict_from_report 报告→verify_fn 契约。ssh/Docker 是 effect seam(不单测)。

三态诚实(同 gate B):harness 没出 report(parsed=False·超时/崩)=ok=False(retry·非真fail);
patch 没 apply / 部分过 = genuine 结果(ok=True·reward=f2p_passed/total·overall_pass=resolved)。
"""
import json

from services.fde_bench_runner import is_swe_task, swe_verdict_from_report, extract_swe_patch


def _swe_task():
    desc = json.dumps({"fde_class": 3, "kind": "swe-rsi-fuel",
                       "swe_instance_id": "psf__requests-2148", "swe_repo": "psf/requests",
                       "verifier": "swebench-harness"})
    return {"task_uid": "psf__requests-2148_fuel_x", "description": desc, "output": "diff..."}


def test_is_swe_task_true():
    assert is_swe_task(_swe_task()) is True


def test_is_swe_task_false_for_kernelbench():
    desc = json.dumps({"fde_class": 3, "kind": "code-fix-with-deterministic-verifier",
                       "kb_problem_id": 13})
    assert is_swe_task({"task_uid": "kb", "description": desc}) is False


def test_is_swe_task_false_for_non_t3():
    assert is_swe_task({"task_uid": "x", "description": "纯文本"}) is False


# ---- extract_swe_patch:只接受真 unified diff(防 V5 annotated-block garbage-apply) ----

_DIFF = "diff --git a/requests/adapters.py b/requests/adapters.py\n--- a/requests/adapters.py\n+++ b/requests/adapters.py\n@@ -1 +1 @@\n-old\n+new\n"


def test_extract_swe_patch_from_patch_field():
    assert extract_swe_patch({"patch": _DIFF}).startswith("diff --git")


def test_extract_swe_patch_from_diff_field():
    assert extract_swe_patch({"diff": _DIFF}).startswith("diff --git")


def test_extract_swe_patch_text_that_is_diff():
    assert extract_swe_patch({"text": _DIFF}).startswith("diff --git")


def test_extract_swe_patch_annotated_block_returns_empty():
    # V5 当前格式(```python + # ... existing code ...)非 diff → "" (清晰信号·不 garbage-apply)
    v5 = {"code": "v5-daemon-fde-produce",
          "text": "```python\n# requests/adapters.py\n# ... existing code ...\n        raise Timeout(err)\n```"}
    assert extract_swe_patch(v5) == ""


def test_swe_verdict_resolved_full_pass():
    rep = {"parsed": True, "applied": True, "resolved": True,
           "f2p_total": 10, "f2p_passed": 10, "f2p_fail_tests": []}
    v = swe_verdict_from_report(rep, "h1")
    assert v["ok"] is True and v["passed"] is True and v["reward"] == 1.0
    assert v["n_pass"] == 10 and v["n_total"] == 10


def test_swe_verdict_partial_is_genuine_gradient():
    # 部分过(turn-1-ish)= genuine·reward=梯度·overall_pass=False(未全 resolved)
    rep = {"parsed": True, "applied": True, "resolved": False,
           "f2p_total": 10, "f2p_passed": 6, "f2p_fail_tests": ["t1", "t2"]}
    v = swe_verdict_from_report(rep, "h2")
    assert v["ok"] is True and v["passed"] is False
    assert v["reward"] == 0.6 and v["n_pass"] == 6


def test_swe_verdict_patch_not_applied_is_genuine_fail():
    # patch 没 apply = 坏 patch = genuine fail(ok=True·reward 0)·非 infra error
    rep = {"parsed": True, "applied": False, "resolved": False,
           "f2p_total": 10, "f2p_passed": None}
    v = swe_verdict_from_report(rep, "h3")
    assert v["ok"] is True and v["passed"] is False and v["reward"] == 0.0


def test_swe_verdict_no_report_is_infra_error_retry():
    # harness 没出 report(超时/崩)= ok=False(不写 verdict·retry·非真 fail)
    v = swe_verdict_from_report({"parsed": False}, "h4")
    assert v["ok"] is False and v["passed"] is False
    v2 = swe_verdict_from_report({"error": "ssh_fail"}, "h5")
    assert v2["ok"] is False


def test_swe_verdict_carries_source_and_hash():
    v = swe_verdict_from_report({"parsed": True, "applied": True, "resolved": True,
                                 "f2p_total": 2, "f2p_passed": 2}, "abc")
    assert v["sol_hash"] == "abc" and v["source"] == "compass/bench_eval"
