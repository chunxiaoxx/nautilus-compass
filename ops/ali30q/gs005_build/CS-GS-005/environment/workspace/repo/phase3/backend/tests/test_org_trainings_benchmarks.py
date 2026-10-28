"""org_state 扩展:trainings/benchmarks 端点(2026-10-04 · 沉淀承载面地基施工)。

沿 frames/rulings/verdicts 零新表同款:每请求读 registry JSON,文件缺失=fail-soft
空列表。数据由提案定稿后填充(字段草案=docs/SEDDIMENT_SURFACE_FOUNDATION_V1.md)。
"""
import asyncio
from unittest.mock import MagicMock

import models.agent_survival  # noqa: F401
from api.org import org_trainings, org_benchmarks


def test_trainings_reads_registry(monkeypatch):
    import api.org as m
    monkeypatch.setattr(m, "_load_json_registry", lambda name: {
        "trainings": [{"round": "r78", "owner": "v5", "negative_result": False}]})
    resp = asyncio.run(org_trainings())
    assert resp["success"] is True
    assert resp["data"][0]["round"] == "r78"
    assert resp["meta"]["count"] == 1


def test_benchmarks_missing_file_fail_soft(monkeypatch):
    import api.org as m
    def _boom(name):
        raise FileNotFoundError(name)
    monkeypatch.setattr(m, "_load_json_registry", _boom)
    resp = asyncio.run(org_benchmarks())
    assert resp["success"] is True
    assert resp["data"] == []
    assert resp["meta"]["count"] == 0
