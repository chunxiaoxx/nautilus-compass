"""judge_writeback 端点双门测试(2026-10-03)——场分离变更门 + 鉴权门。

不依赖数据库:直接以 stub 调函数(db 用 Mock 截获 add/commit)。
背景:外网零鉴权实测洞(任何人可写 org_mailbox)+ lab:* 前缀门(3dd17d00a)。
"""
import os
from unittest.mock import MagicMock

import pytest

import models.agent_survival  # noqa: F401  # 先注册 AgentSurvival mapper,再导 api.org(既有顺序坑)
from api.org import judge_writeback, _WritebackReq


class _Req:
    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


def _payload(judge_type: str = "w42") -> _WritebackReq:
    return _WritebackReq(
        agent_id="test-judge",
        judge_type=judge_type,
        items=[{"id": "t1", "label": "用例甲"}],
    )


def _run(req, headers, monkeypatch, key=None):
    if key is None:
        monkeypatch.delenv("WRITEBACK_KEY", raising=False)
    else:
        monkeypatch.setenv("WRITEBACK_KEY", key)
    db = MagicMock()
    import asyncio
    # asyncio.run(不依赖全局 loop;旧式 get_event_loop 在他文件 asyncio.run 关闭
    # loop 后会 RuntimeError,2026-10-03 合跑污染实测)
    return asyncio.run(judge_writeback(req, _Req(headers), db=db)), db


def test_lab_prefix_marks_title_and_strips(monkeypatch):
    """lab:* 前缀 → title 带 [lab·] 标记且 judge_type 剥前缀。"""
    resp, db = _run(_payload("lab:exp9"), {}, monkeypatch)
    assert resp is None or getattr(resp, "status_code", 200) == 200  # dict 返回=放行
    added = db.add.call_args_list[0].args[0]
    assert added.title.startswith("[lab·exp9]")
    assert added.trace_id == "writeback:exp9:t1"
    db.commit.assert_called_once()


def test_prod_judge_type_unmarked(monkeypatch):
    resp, db = _run(_payload("w42"), {}, monkeypatch)
    added = db.add.call_args_list[0].args[0]
    assert added.title.startswith("[writeback:w42]")


def test_auth_enforced_when_key_set(monkeypatch):
    """设 WRITEBACK_KEY:无头/错头 401,对头放行。"""
    resp, _ = _run(_payload(), {}, monkeypatch, key="k-123")
    assert getattr(resp, "status_code", None) == 401
    resp, _ = _run(_payload(), {"X-Writeback-Key": "wrong"}, monkeypatch, key="k-123")
    assert getattr(resp, "status_code", None) == 401
    resp, db = _run(_payload(), {"X-Writeback-Key": "k-123"}, monkeypatch, key="k-123")
    assert getattr(resp, "status_code", 200) == 200
    db.add.assert_called()


def test_grace_mode_when_key_unset(monkeypatch, caplog):
    """未设 WRITEBACK_KEY:宽限放行+warn 日志(48h 接线期)。"""
    import logging
    with caplog.at_level(logging.WARNING, logger="org.writeback"):
        resp, db = _run(_payload(), {}, monkeypatch)
    assert getattr(resp, "status_code", 200) == 200
    assert "grace mode" in caplog.text


def test_empty_items_400(monkeypatch):
    resp, _ = _run(_WritebackReq(agent_id="x", judge_type="w", items=[]), {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 400


def test_all_items_without_id_422(monkeypatch):
    """flywheel 10/3 inserted:0 假绿根修:items 全缺 id → 422 拒收,零落库零 commit。"""
    req = _WritebackReq(agent_id="flywheel", judge_type="four_gate_acceptance",
                        items=[{"label": "f006"}, {"case": "x"}])
    resp, db = _run(req, {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 422
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_mixed_items_counts_inserted_and_skipped(monkeypatch):
    """混合 items:有 id 的落库,无 id 的计入 skipped 显式返回。"""
    req = _WritebackReq(agent_id="j", judge_type="w",
                        items=[{"id": "ok1", "label": "甲"}, {"label": "缺id"}])
    resp, db = _run(req, {}, monkeypatch)
    assert getattr(resp, "status_code", 200) == 200
    assert db.add.call_count == 1
    body = resp if isinstance(resp, dict) else {}
    assert body.get("data", {}).get("inserted") == 1
    assert body.get("data", {}).get("skipped") == 1
