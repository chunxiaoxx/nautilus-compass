"""W-D soul scoring poller (platform-soul turf · produced → verdict).

Closes the FDE flywheel's last hop: poll produced tasks (GET /tasks?status=produced),
read each output, score it with the soul RUBRIC checklist_scorer (injected as score_fn),
then POST the verdict to the existing verdict-bus (POST /api/platform/fde/verdict).

source='soul' (compass PoI allowlist) · deterministic verdict_id (idempotent re-score).
V5 scorer-front (source='feishu-expert' human review) writes in parallel — no conflict
(distinct source + verdict_id). Mirrors services/fde_poller.py: Protocol source + injected
effect fns + fail-soft, so the pure orchestration is unit-tested without HTTP/LLM.
"""
from __future__ import annotations

import json

from services.fde_scorer_poll import (
    build_verdict_body,
    is_deterministic_kind,
    is_substantive_output,
    poll_and_score,
    ProducedTaskSource,
)


class StubSource:
    """Stand-in for GET /api/platform/fde/tasks?status=produced."""

    def __init__(self, tasks):
        self._tasks = tasks
        self.calls = 0

    def list_produced_tasks(self):
        self.calls += 1
        return list(self._tasks)


def _passing_score_fn(task):
    """Injected scorer stub: all items pass (full RUBRIC shape)."""
    return {
        "score": 1.0,
        "passed": 3,
        "total": 3,
        "veto_failed": False,
        "overall_pass": True,
        "items": [{"id": "c1", "pass": True, "veto": False, "reason": "ok"}],
        "checklist_uid": f"ck-{task['task_uid']}",
    }


def _recording_verdict():
    posted = []

    def verdict_fn(body):
        posted.append(body)
        return {"verdict_id": body["verdict_id"], "idempotent": False}

    verdict_fn.posted = posted
    return verdict_fn


# ── build_verdict_body (pure) ─────────────────────────────────────────────

def test_build_verdict_body_has_required_fields_and_soul_source():
    scored = _passing_score_fn({"task_uid": "feishu_card_1780832109"})
    body = build_verdict_body(
        {"task_uid": "feishu_card_1780832109", "output": {"text": "..."}}, scored
    )
    # ingest _REQUIRED = verdict_id, task_uid, source, overall_pass, score
    for key in ("verdict_id", "task_uid", "source", "overall_pass", "score"):
        assert key in body and body[key] is not None
    assert body["source"] == "soul"
    assert body["task_uid"] == "feishu_card_1780832109"
    assert body["overall_pass"] is True
    assert body["score"] == 1.0
    assert body["checklist_uid"] == "ck-feishu_card_1780832109"
    assert isinstance(body["items"], list)


def test_build_verdict_body_verdict_id_is_deterministic():
    """Same task + checklist → same verdict_id (ingest is idempotent on it)."""
    scored = _passing_score_fn({"task_uid": "data_001"})
    a = build_verdict_body({"task_uid": "data_001"}, scored)
    b = build_verdict_body({"task_uid": "data_001"}, scored)
    assert a["verdict_id"] == b["verdict_id"]
    assert a["verdict_id"] == "soul|data_001|ck-data_001"


def test_build_verdict_body_propagates_veto_fail():
    scored = {
        "score": 0.5, "passed": 1, "total": 2,
        "veto_failed": True, "overall_pass": False,
        "items": [{"id": "c1", "pass": False, "veto": True, "reason": "编造数据"}],
        "checklist_uid": "ck-x",
    }
    body = build_verdict_body({"task_uid": "x"}, scored)
    assert body["overall_pass"] is False
    assert body["veto_failed"] is True
    assert body["score"] == 0.5


# ── poll_and_score (orchestration) ────────────────────────────────────────

def test_poll_scores_produced_and_posts_verdict():
    src = StubSource([
        {"task_uid": "t1", "output": {"text": "ans1"}},
        {"task_uid": "t2", "output": {"text": "ans2"}},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn)
    assert result["scored"] == ["t1", "t2"]
    assert [b["task_uid"] for b in verdict_fn.posted] == ["t1", "t2"]
    assert all(b["source"] == "soul" for b in verdict_fn.posted)


def test_poll_skips_already_scored():
    src = StubSource([
        {"task_uid": "t3", "output": {"text": "a"}},
        {"task_uid": "t4", "output": {"text": "a"}},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn, already_scored={"t3"})
    assert result["scored"] == ["t4"]
    assert "t3" in result["skipped"]
    assert [b["task_uid"] for b in verdict_fn.posted] == ["t4"]


def test_poll_skips_produced_without_output():
    """A produced task missing output can't be scored → skip, don't crash."""
    src = StubSource([
        {"task_uid": "t5"},                      # no output
        {"task_uid": "t6", "output": {"text": "a"}},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn)
    assert result["scored"] == ["t6"]
    assert "t5" in result["skipped"]


def test_poll_dedupes_within_batch():
    src = StubSource([
        {"task_uid": "t7", "output": {"text": "a"}},
        {"task_uid": "t7", "output": {"text": "dup"}},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn)
    assert result["scored"] == ["t7"]
    assert len(verdict_fn.posted) == 1


def test_score_failure_does_not_abort_batch():
    """One task's scorer raising must not stop the rest (fail-soft)."""
    src = StubSource([
        {"task_uid": "t8", "output": {"text": "a"}},
        {"task_uid": "t9", "output": {"text": "a"}},
    ])

    def flaky_score(task):
        if task["task_uid"] == "t8":
            raise RuntimeError("judge LLM timeout")
        return _passing_score_fn(task)

    verdict_fn = _recording_verdict()
    result = poll_and_score(src, flaky_score, verdict_fn)
    assert result["scored"] == ["t9"]
    assert "t8" in result["failed"]


def test_verdict_post_failure_does_not_abort_batch():
    src = StubSource([
        {"task_uid": "t10", "output": {"text": "a"}},
        {"task_uid": "t11", "output": {"text": "a"}},
    ])

    def flaky_verdict(body):
        if body["task_uid"] == "t10":
            raise RuntimeError("verdict endpoint 500")
        return {"verdict_id": body["verdict_id"]}

    result = poll_and_score(src, _passing_score_fn, flaky_verdict)
    assert result["scored"] == ["t11"]
    assert "t10" in result["failed"]


def test_poll_empty_source_scores_nothing():
    src = StubSource([])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn)
    assert result["scored"] == []
    assert verdict_fn.posted == []


def test_source_protocol_is_exported():
    """ProducedTaskSource is the platform-binding seam (list_produced_tasks)."""
    assert hasattr(ProducedTaskSource, "list_produced_tasks")


# ── is_substantive_output 守卫:防 producer 占位/求输入闲聊被判 pass(6/21 autolab bogus)──

def test_is_substantive_output_true_for_real_deliverable():
    """正常交付(代码/diff/短答案)= 实质 → 该判。"""
    assert is_substantive_output({"task_uid": "x", "output": {"text": "def fix(): return 1"}}) is True
    assert is_substantive_output({"task_uid": "x", "output": "diff --git a/x b/x"}) is True
    assert is_substantive_output({"task_uid": "x", "output": {"text": "ans1"}}) is True  # 短答案不误杀


def test_is_substantive_output_false_for_placeholder_chitchat():
    """6/21 autolab 真样本:producer 没拿到题的占位产出 → 非实质。"""
    out = {"code": "v5-daemon-fde-produce",
           "text": "您好!我已理解您的配置参数。现在需要您提供具体的题目或任务内容,我才能开始作答。"}
    assert is_substantive_output({"task_uid": "compass_autolab_zorder_001", "output": out}) is False


def test_is_substantive_output_false_for_empty_or_missing():
    assert is_substantive_output({"task_uid": "x"}) is False
    assert is_substantive_output({"task_uid": "x", "output": {"text": ""}}) is False
    assert is_substantive_output({"task_uid": "x", "output": "   "}) is False


def test_poll_skips_nonsubstantive_output_no_bogus_verdict():
    """非实质占位产出 → 跳过·不调 score_fn·不写 verdict(防 LLM judge 盖章闲聊)。"""
    calls = []

    def tracking_score(task):
        calls.append(task["task_uid"])
        return _passing_score_fn(task)

    chitchat = {"code": "v5-daemon-fde-produce",
                "text": "您好!现在需要您提供具体的题目或任务内容,我才能开始作答。"}
    src = StubSource([
        {"task_uid": "junk", "output": chitchat},
        {"task_uid": "real", "output": {"text": "实质交付内容:已修复并验证"}},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, tracking_score, verdict_fn)
    assert result["scored"] == ["real"]
    assert "junk" in result["skipped"]
    assert calls == ["real"]  # score_fn 没在 junk 上调(不浪费 LLM·不盖章)
    assert [b["task_uid"] for b in verdict_fn.posted] == ["real"]


# ── should_score 谓词:soul 不双判 deterministic-kind(code-fix)─────────────

def test_is_deterministic_kind_true_for_codefix():
    """code-fix-with-deterministic-verifier 题 = bench_eval turf · soul 不该判。"""
    desc = json.dumps({"fde_class": 3, "kind": "code-fix-with-deterministic-verifier",
                       "starter_inline": "x", "verifier_inline": "y"}, ensure_ascii=False)
    assert is_deterministic_kind({"task_uid": "c", "description": desc}) is True


def test_is_deterministic_kind_true_for_swe_fuel():
    """SWE 燃料(kind=swe-rsi-fuel)= swebench harness 确定性 verifier turf · soul 不该 checklist 判。

    🔴 6/20 facade bug 回归门:requests-2148 被 soul checklist 误判 score=0.857(SWE patch
    正确性只能 swebench 跑)→ soul 必须跳过让 SWE verify-side 权威判。
    """
    desc = json.dumps({"fde_class": 3, "kind": "swe-rsi-fuel",
                       "swe_instance_id": "psf__requests-2148", "verifier": "swebench-harness"},
                      ensure_ascii=False)
    assert is_deterministic_kind({"task_uid": "s", "description": desc}) is True


def test_is_deterministic_kind_true_for_swe_via_instance_id():
    """防御:即便 kind 缺失·desc 有 swe_instance_id 也视为确定性(soul 不判)。"""
    desc = json.dumps({"fde_class": 3, "swe_instance_id": "psf__requests-2148"},
                      ensure_ascii=False)
    assert is_deterministic_kind({"task_uid": "s2", "description": desc}) is True


def test_is_deterministic_kind_false_for_tutorial():
    """第2类教案题 = soul/assembler turf · 该判。"""
    desc = json.dumps({"fde_class": 2, "kind": "knowledge-tutorial"}, ensure_ascii=False)
    assert is_deterministic_kind({"task_uid": "t", "description": desc}) is False


def test_is_deterministic_kind_false_for_nonjson_desc():
    """非 JSON / 无 kind 描述 → 默认非确定性(继续判·不误跳)。"""
    assert is_deterministic_kind({"task_uid": "p", "description": "纯文本题干"}) is False
    assert is_deterministic_kind({"task_uid": "q"}) is False


def test_poll_skips_when_should_score_false():
    """should_score 返回 False 的题被跳过(不调 score_fn·不发 verdict)。"""
    src = StubSource([
        {"task_uid": "det", "output": {"code": "fix"},
         "description": json.dumps({"kind": "code-fix-with-deterministic-verifier"})},
        {"task_uid": "tut", "output": {"text": "教案"},
         "description": json.dumps({"kind": "knowledge-tutorial"})},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn,
                            should_score=lambda t: not is_deterministic_kind(t))
    assert result["scored"] == ["tut"]
    assert "det" in result["skipped"]
    assert [b["task_uid"] for b in verdict_fn.posted] == ["tut"]


def test_poll_should_score_none_scores_all():
    """should_score=None(默认)→ 全判(向后兼容)。"""
    src = StubSource([
        {"task_uid": "a", "output": {"text": "x"},
         "description": json.dumps({"kind": "code-fix-with-deterministic-verifier"})},
    ])
    verdict_fn = _recording_verdict()
    result = poll_and_score(src, _passing_score_fn, verdict_fn)
    assert result["scored"] == ["a"]
