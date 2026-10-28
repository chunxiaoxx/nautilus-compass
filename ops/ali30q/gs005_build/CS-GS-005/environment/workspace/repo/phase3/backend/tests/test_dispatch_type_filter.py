"""dispatch_public 按类型过滤(2026-10-04 · prime 分流①平台配合件,v5 #2586)。

任务类型路由最小落地:公开单列表支持 ?task_type=fuel 过滤,认领方按类拉单。
"""
import asyncio
from unittest.mock import MagicMock

import models.agent_survival  # noqa: F401
from api.org import dispatch_public


class _FakeResult:
    def __init__(self):
        self.rows = []

    def mappings(self):
        return self

    def all(self):
        return self.rows


def _run(monkeypatch, task_type=None):
    db = MagicMock()
    db.execute.return_value = _FakeResult()
    kwargs = {"db": db}
    if task_type:
        kwargs["task_type"] = task_type
    resp = asyncio.run(dispatch_public(**kwargs))
    sql = str(db.execute.call_args.args[0])
    params = db.execute.call_args.kwargs.get("params") or db.execute.call_args.args[1]
    return resp, sql, params


def test_filter_by_task_type():
    _, sql, params = _run(None, task_type="fuel")
    assert "task_type = :tt" in sql
    assert params["tt"] == "fuel"


def test_no_filter_backcompat():
    _, sql, params = _run(None)
    assert "task_type = :tt" not in sql
    assert params["s"] == "open"
