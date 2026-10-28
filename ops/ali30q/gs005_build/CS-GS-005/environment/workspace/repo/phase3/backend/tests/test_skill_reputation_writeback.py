"""技能信誉回写端点(2026-10-04 · v5 #2626 信誉飞轮配套)——交付数据回写 agent_skills。

设计:全量快照式幂等更新(total_hires/avg_rating/success_rate),鉴权沿
X-Writeback-Key 宽限门;行不存在 404(不自动建行,上架走平台审核通道)。
"""
import asyncio
import os
from unittest.mock import MagicMock

import models.agent_survival  # noqa: F401  # mapper 顺序坑
from api.org import skill_reputation_writeback, _SkillRepReq


class _Req:
    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


def _payload(slug: str = "fuel-trajectory-verify") -> _SkillRepReq:
    return _SkillRepReq(slug=slug, total_hires=3, avg_rating=4.7, success_rate=0.94)


def _run(req, headers, monkeypatch, key=None, rowcount=1):
    if key is None:
        monkeypatch.delenv("WRITEBACK_KEY", raising=False)
    else:
        monkeypatch.setenv("WRITEBACK_KEY", key)
    db = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    db.execute.return_value = result
    resp = asyncio.run(skill_reputation_writeback(req, _Req(headers), db=db))
    return resp, db


def test_update_existing_skill(monkeypatch):
    resp, db = _run(_payload(), {}, monkeypatch)
    assert resp["success"] is True
    assert resp["data"]["slug"] == "fuel-trajectory-verify"
    sql = str(db.execute.call_args.args[0])
    assert "UPDATE agent_skills" in sql
    db.commit.assert_called_once()


def test_unknown_slug_404(monkeypatch):
    resp, db = _run(_payload(slug="no-such-skill"), {}, monkeypatch, rowcount=0)
    assert getattr(resp, "status_code", None) == 404
    db.commit.assert_not_called()


def test_negative_values_400(monkeypatch):
    p = _Payload = _SkillRepReq(slug="x", total_hires=-1, avg_rating=5.0, success_rate=0.5)
    resp, db = _run(p, {}, monkeypatch)
    assert getattr(resp, "status_code", None) == 400
    db.execute.assert_not_called()


def test_auth_enforced_when_key_set(monkeypatch):
    resp, _ = _run(_payload(), {}, monkeypatch, key="k-9")
    assert getattr(resp, "status_code", None) == 401
    resp, db = _run(_payload(), {"X-Writeback-Key": "k-9"}, monkeypatch, key="k-9")
    assert resp["success"] is True
