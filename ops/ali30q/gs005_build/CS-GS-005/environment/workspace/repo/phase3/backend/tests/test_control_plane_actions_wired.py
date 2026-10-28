"""Wiring smoke · control_plane_actions router must be mounted on main.py.

admin 控制层(whoami/dispatch代理/goal/drill-down·admin-email 门)单测跑在
本地 app fixture(test_control_plane_actions.py)。本测试钉死它真的并入 main.py。

NOTE: main.py 本地不可 import(master/fork 分叉·services.agent_service 仅 cloud),
故源级断言 import + include_router 存在(同 test_control_plane_wired 模式)。
"""
from __future__ import annotations

import os

_MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")


def _main_src() -> str:
    with open(_MAIN, encoding="utf-8") as fh:
        return fh.read()


def test_control_plane_actions_router_wired():
    src = _main_src()
    assert "from api.control_plane_actions import router as control_plane_actions_router" in src
    assert "app.include_router(control_plane_actions_router)" in src
