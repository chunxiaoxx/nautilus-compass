"""第3类(RSI 飞轮)确定性 verify poller 单测.

第3类 ≠ 第1/2类 QC: produce 出的修复代码经 compass bench_eval.py(确定性 G 门·
非 LLM judge)判 reward 1.0/0.0 → verdict source='compass/bench_eval' → settled.
这是飞轮缺的一环(没有它 consumer 产出无 reward·棘轮不转).

镜像 test_fde_poller.py: 纯核心 + 注入 seam, 无 HTTP/子进程.
"""
from __future__ import annotations

from services.fde_bench_poll import (
    poll_and_verify,
    build_bench_verdict_body,
    is_t3_bench_task,
    parse_t3_spec,
    ProducedTaskSource,
)


class StubSource:
    def __init__(self, tasks):
        self._tasks = tasks
        self.calls = 0

    def list_produced_tasks(self):
        self.calls += 1
        return list(self._tasks)


def _recording_verdict():
    sent = []

    def verdict_fn(body):
        sent.append(body)
        return {"verdict_id": body["verdict_id"]}

    verdict_fn.sent = sent
    return verdict_fn


def _t3_task(uid, output="def f(): pass"):
    """A produced T3 bench task: description packs fde_class==3 + inlined verifier."""
    import json
    desc = json.dumps({
        "fde_class": 3,
        "kind": "code-fix-with-deterministic-verifier",
        "任务概括": "修 UTF-8 字节截断",
        "verifier_inline": "print('{\"passed\": true}')",
    })
    return {"task_uid": uid, "title": "t", "description": desc, "output": output}


# ── is_t3_bench_task / parse_t3_spec ─────────────────────────────────────────

def test_is_t3_bench_task_detects_fde_class_3():
    assert is_t3_bench_task(_t3_task("c2d_001")) is True


def test_is_t3_bench_task_rejects_non_t3():
    # human 第1/2类 task: description is QC-style JSON without fde_class:3
    import json
    t = {"task_uid": "expert_t2_x", "description": json.dumps({"line": "2", "producer": "human"}),
         "output": "稿"}
    assert is_t3_bench_task(t) is False


def test_is_t3_bench_task_rejects_garbage_description():
    assert is_t3_bench_task({"task_uid": "x", "description": "not json", "output": "o"}) is False


def test_parse_t3_spec_returns_dict():
    spec = parse_t3_spec(_t3_task("c2d_001"))
    assert spec is not None and spec["fde_class"] == 3


# ── build_bench_verdict_body ─────────────────────────────────────────────────

def test_verdict_body_pass_shape():
    task = _t3_task("c2d_001")
    result = {"reward": 1.0, "passed": True, "ok": True, "n_pass": 6, "n_total": 6,
              "reason": "pass", "sol_hash": "abc12345"}
    body = build_bench_verdict_body(task, result)
    assert body["task_uid"] == "c2d_001"
    assert body["source"] == "compass/bench_eval"
    assert body["overall_pass"] is True
    assert body["score"] == 1.0
    assert body["veto_failed"] is False
    # deterministic, solution-hash keyed (per-version ratchet → re-produce = new verdict)
    assert body["verdict_id"] == "bench|c2d_001|abc12345"
    assert body["artifacts"]["n_pass"] == 6


def test_verdict_body_fail_shape():
    task = _t3_task("c2d_001")
    result = {"reward": 0.0, "passed": False, "ok": True, "n_pass": 3, "n_total": 6,
              "reason": "G1 超字节预算", "sol_hash": "deadbeef"}
    body = build_bench_verdict_body(task, result)
    assert body["overall_pass"] is False
    assert body["score"] == 0.0
    assert body["artifacts"]["reason"] == "G1 超字节预算"


# ── poll_and_verify ──────────────────────────────────────────────────────────

def test_poll_writes_pass_verdict():
    src = StubSource([_t3_task("c2d_001")])

    def verify_fn(task):
        return {"reward": 1.0, "passed": True, "ok": True, "n_pass": 6, "n_total": 6,
                "reason": "pass", "sol_hash": "h1"}

    vf = _recording_verdict()
    res = poll_and_verify(src, verify_fn, vf)
    assert res["verified"] == ["c2d_001"]
    assert len(vf.sent) == 1
    assert vf.sent[0]["source"] == "compass/bench_eval"
    assert vf.sent[0]["overall_pass"] is True


def test_poll_writes_fail_verdict():
    """reward 0 (跑通但没过) IS a legit verdict — the ratchet needs the 0 signal too."""
    src = StubSource([_t3_task("c2d_001")])

    def verify_fn(task):
        return {"reward": 0.0, "passed": False, "ok": True, "n_pass": 3, "n_total": 6,
                "reason": "fail", "sol_hash": "h2"}

    vf = _recording_verdict()
    res = poll_and_verify(src, verify_fn, vf)
    assert res["verified"] == ["c2d_001"]
    assert vf.sent[0]["overall_pass"] is False
    assert vf.sent[0]["score"] == 0.0


def test_poll_verifier_self_failure_writes_no_verdict_and_is_retryable():
    """ok=False (bench 缺失/超时/非JSON) ≠ 合法 reward 0 → 不写 verdict, 可重试."""
    src = StubSource([_t3_task("c2d_001")])

    def verify_fn(task):
        return {"reward": 0.0, "passed": False, "ok": False, "reason": "bench timeout"}

    vf = _recording_verdict()
    res = poll_and_verify(src, verify_fn, vf)
    assert res["errored"] == ["c2d_001"]
    assert vf.sent == []  # no verdict written for a verifier self-failure


def test_poll_skips_non_t3_tasks():
    """第1/2类 human task → 留给 soul scorer, bench poller 不碰."""
    import json
    human = {"task_uid": "expert_t2_x", "description": json.dumps({"line": "2"}), "output": "稿"}
    src = StubSource([human])

    def verify_fn(task):  # pragma: no cover - must not be called
        raise AssertionError("should not verify a non-T3 task")

    vf = _recording_verdict()
    res = poll_and_verify(src, verify_fn, vf)
    assert "expert_t2_x" in res["skipped"]
    assert vf.sent == []


def test_poll_skips_empty_output():
    t = _t3_task("c2d_001", output="")
    src = StubSource([t])
    vf = _recording_verdict()
    res = poll_and_verify(src, lambda task: {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"}, vf)
    assert "c2d_001" in res["skipped"]
    assert vf.sent == []


def test_poll_skips_already_verified():
    src = StubSource([_t3_task("c2d_001")])
    vf = _recording_verdict()
    res = poll_and_verify(
        src,
        lambda task: {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"},
        vf,
        already_verified={"c2d_001"},
    )
    assert "c2d_001" in res["skipped"]
    assert vf.sent == []


def test_poll_failsoft_one_task_does_not_abort_batch():
    src = StubSource([_t3_task("c2d_001"), _t3_task("c2d_002")])

    def flaky(task):
        if task["task_uid"] == "c2d_001":
            raise RuntimeError("verify crashed")
        return {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"}

    vf = _recording_verdict()
    res = poll_and_verify(src, flaky, vf)
    assert "c2d_001" in res["failed"]
    assert res["verified"] == ["c2d_002"]


def test_poll_dedupes_within_batch():
    src = StubSource([_t3_task("c2d_001"), _t3_task("c2d_001")])
    vf = _recording_verdict()
    res = poll_and_verify(src, lambda task: {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"}, vf)
    assert res["verified"] == ["c2d_001"]
    assert len(vf.sent) == 1


def test_source_protocol_exported():
    assert hasattr(ProducedTaskSource, "list_produced_tasks")


# ── capability_fn 钩子(verify-side 能力回写注入 seam) ──────────────────────

def test_capability_fn_called_on_verified():
    src = StubSource([_t3_task("c2d_001")])
    calls = []
    poll_and_verify(
        src,
        lambda task: {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"},
        _recording_verdict(),
        capability_fn=lambda task, result: calls.append((task["task_uid"], result["ok"])),
    )
    assert calls == [("c2d_001", True)]


def test_capability_fn_called_on_errored_format_fail():
    # ok=False(格式失败)也调 capability_fn(单写点·覆盖 errored 路)·但不写 verdict
    src = StubSource([_t3_task("c2d_002")])
    calls = []
    vf = _recording_verdict()
    res = poll_and_verify(
        src,
        lambda task: {"ok": False, "reward": 0.0, "reason": "non-diff patch"},
        vf,
        capability_fn=lambda task, result: calls.append(result["ok"]),
    )
    assert calls == [False]          # 能力钩子拿到了格式失败
    assert "c2d_002" in res["errored"]
    assert len(vf.sent) == 0         # errored 不写 verdict


def test_capability_fn_failure_does_not_break_verify():
    src = StubSource([_t3_task("c2d_003")])
    def boom(task, result):
        raise RuntimeError("capability db down")
    vf = _recording_verdict()
    res = poll_and_verify(
        src,
        lambda task: {"ok": True, "passed": True, "reward": 1.0, "sol_hash": "h"},
        vf,
        capability_fn=boom,
    )
    assert res["verified"] == ["c2d_003"]   # 主链不受影响
    assert len(vf.sent) == 1
