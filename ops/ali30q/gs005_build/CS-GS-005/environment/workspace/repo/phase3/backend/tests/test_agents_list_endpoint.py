# -*- coding: utf-8 -*-
"""GET /api/agents 500 修复回归(9/5)。

根因:a4c39c1d 恢复 agent_service(9a226eaa 误删后)时 get_agents_list_cached
返回 list,而端点 list_agents 按 result["agents"] 取值 → list 下标 TypeError。
单 agent 端点(/{agent_id})同文件同病系已由 a2126a91 修过,此处锁列表形状。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.agent_service import get_agents_list_cached  # noqa: E402


class _FakeQuery:
    def offset(self, _o):
        return self

    def limit(self, _l):
        return self

    def all(self):
        return [
            SimpleNamespace(id=1, agent_id=9000010, name="a"),
            SimpleNamespace(id=2, agent_id=9000011, name="b"),
        ]


class _FakeDB:
    def query(self, _model):
        return _FakeQuery()


def test_service_returns_dict_with_agents_key():
    result = asyncio.run(get_agents_list_cached(limit=5, db=_FakeDB()))
    assert isinstance(result, dict), (
        f"服务必须返回 dict,否则端点 result['agents'] 抛 TypeError(9/5 500 根因);"
        f"实际 {type(result)}"
    )
    agents = result["agents"]  # 修复前此行 TypeError: list indices must be integers
    assert isinstance(agents, list) and len(agents) == 2
    assert agents[0]["agent_id"] == 9000010  # _sa 前缀私有键已滤除


def test_endpoint_value_path_yields_list():
    """复刻端点取值路径:return result['agents']。"""
    result = asyncio.run(get_agents_list_cached(limit=5, db=_FakeDB()))
    returned = result["agents"]
    assert isinstance(returned, list)
