"""frames declare 端点(2026-10-04 · 裁决分级清单配套件)——框卡声明机器可读入队。

设计:声明不直写 registry 文件(git 单主干纪律+生产 clean),落 org_mailbox
(frames_declare: 前缀)由平台/loop 审核合并。鉴权沿 judge/writeback 宽限门同款。
"""
import asyncio
import os
from unittest.mock import MagicMock

import pytest

import models.agent_survival  # noqa: F401  # mapper 顺序坑(先注册再导 api.org)
from api.org import frames_declare, _FrameDeclareReq


class _Req:
    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


def _payload(frame: str = "soul") -> _FrameDeclareReq:
    return _FrameDeclareReq(
        frame=frame, mainline="自改进提案+裁决员", criteria="ack清零+周≥1采纳",
        reach="mailbox", cadence="1h轮")


def _run(req, headers, monkeypatch, key=None):
    if key is None:
        monkeypatch.delenv("WRITEBACK_KEY", raising=False)
    else:
        monkeypatch.setenv("WRITEBACK_KEY", key)
    db = MagicMock()
    resp = asyncio.run(frames_declare(req, _Req(headers), db=db))
    return resp, db


def test_valid_declare_queues_letter(monkeypatch):
    resp, db = _run(_payload(), {}, monkeypatch)
    assert resp["success"] is True
    assert resp["data"]["status"] == "queued_for_review"
    row = db.add.call_args_list[0].args[0]
    assert row.trace_id.startswith("frames_declare:soul:")
    assert "soul" in row.title
    db.commit.assert_called_once()


def test_unknown_frame_400(monkeypatch):
    resp, db = _run(_payload(frame="nonexistent-frame"), {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 400
    db.add.assert_not_called()


def test_blank_field_400(monkeypatch):
    p = _payload()
    p.mainline = "  "
    resp, db = _run(p, {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 400
    db.add.assert_not_called()


def test_field_length_cap_400(monkeypatch):
    p = _payload()
    p.criteria = "x" * 301
    resp, _ = _run(p, {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 400


def test_auth_enforced_when_key_set(monkeypatch):
    resp, _ = _run(_payload(), {}, monkeypatch, key="k-9")
    assert getattr(resp, "status_code", None) == 401  # 与 judge/writeback 门同码
    resp, db = _run(_payload(), {"X-Writeback-Key": "k-9"}, monkeypatch, key="k-9")
    assert resp["success"] is True
    db.add.assert_called_once()
