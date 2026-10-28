"""W-5 临时 poller (platform turf · dispatch decision).

compass read_buyer_tasks → 派单决策(平台 own) → POST /api/platform/fde/dispatch.
这是 V7 连接器没就位时的平台侧兜底. compass 的 read 是注入 source(就位即接),
平台**不**重造 feishu 读 (G-turf). 派单决策归平台,不让 compass 主动派.
"""
from __future__ import annotations

from services.fde_poller import poll_and_dispatch, should_dispatch, BuyerTaskSource


class StubSource:
    """Stand-in for compass read_buyer_tasks (which ships on compass turf)."""

    def __init__(self, tasks):
        self._tasks = tasks
        self.calls = 0

    def read_buyer_tasks(self):
        self.calls += 1
        return list(self._tasks)


def _recording_dispatch():
    sent = []

    def dispatch_fn(task):
        sent.append(task["task_uid"])
        return {"task_uid": task["task_uid"], "status": "open"}

    dispatch_fn.sent = sent
    return dispatch_fn


def test_poll_dispatches_new_tasks():
    src = StubSource([
        {"task_uid": "buyer_001", "title": "题1", "description": "d1"},
        {"task_uid": "buyer_002", "title": "题2", "description": "d2"},
    ])
    dispatch_fn = _recording_dispatch()
    result = poll_and_dispatch(src, dispatch_fn)
    assert result["dispatched"] == ["buyer_001", "buyer_002"]
    assert dispatch_fn.sent == ["buyer_001", "buyer_002"]


def test_poll_skips_already_dispatched():
    """idempotent: tasks already dispatched (by task_uid) are not re-sent."""
    src = StubSource([
        {"task_uid": "buyer_003", "title": "t", "description": "d"},
        {"task_uid": "buyer_004", "title": "t", "description": "d"},
    ])
    dispatch_fn = _recording_dispatch()
    result = poll_and_dispatch(src, dispatch_fn, already_dispatched={"buyer_003"})
    assert result["dispatched"] == ["buyer_004"]
    assert "buyer_003" in result["skipped"]
    assert dispatch_fn.sent == ["buyer_004"]


def test_poll_skips_tasks_without_uid():
    src = StubSource([
        {"title": "no uid", "description": "d"},
        {"task_uid": "buyer_005", "title": "t", "description": "d"},
    ])
    dispatch_fn = _recording_dispatch()
    result = poll_and_dispatch(src, dispatch_fn)
    assert result["dispatched"] == ["buyer_005"]
    assert dispatch_fn.sent == ["buyer_005"]


def test_poll_dedupes_within_single_batch():
    """same task_uid twice in one read → dispatched once."""
    src = StubSource([
        {"task_uid": "buyer_006", "title": "t", "description": "d"},
        {"task_uid": "buyer_006", "title": "dup", "description": "d"},
    ])
    dispatch_fn = _recording_dispatch()
    result = poll_and_dispatch(src, dispatch_fn)
    assert result["dispatched"] == ["buyer_006"]
    assert dispatch_fn.sent == ["buyer_006"]


def test_dispatch_decision_is_platform_side():
    """派单决策归平台: a task without a task_uid is not dispatchable."""
    assert should_dispatch({"task_uid": "x"}) is True
    assert should_dispatch({"title": "no uid"}) is False


def test_poll_empty_source_dispatches_nothing():
    src = StubSource([])
    dispatch_fn = _recording_dispatch()
    result = poll_and_dispatch(src, dispatch_fn)
    assert result["dispatched"] == []
    assert dispatch_fn.sent == []


def test_dispatch_failure_does_not_abort_batch():
    """one task's dispatch raising must not stop the rest (fail-soft)."""
    src = StubSource([
        {"task_uid": "buyer_007", "title": "t", "description": "d"},
        {"task_uid": "buyer_008", "title": "t", "description": "d"},
    ])

    def flaky_dispatch(task):
        if task["task_uid"] == "buyer_007":
            raise RuntimeError("dispatch endpoint down")
        return {"task_uid": task["task_uid"], "status": "open"}

    result = poll_and_dispatch(src, flaky_dispatch)
    assert result["dispatched"] == ["buyer_008"]
    assert "buyer_007" in result["failed"]


def test_source_protocol_is_exported():
    """BuyerTaskSource is the compass-binding seam (read_buyer_tasks)."""
    assert hasattr(BuyerTaskSource, "read_buyer_tasks")
