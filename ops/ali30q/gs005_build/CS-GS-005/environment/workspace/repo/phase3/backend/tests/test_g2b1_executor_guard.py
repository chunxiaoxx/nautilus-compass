# -*- coding: utf-8 -*-
"""g2b1 executor 守卫逻辑单测(9/5 空转修复:单实例锁+残留清扫)。

背景:schtasks 25min 叠加 --loop-minutes 15 常驻实例 → 几百并发互踩,
fail_streak 54 连败+2.7 万泄漏目录。守卫=进程模型修复,见
g2_b1_executor_agent.acquire_single_instance / sweep_stale_workdirs。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.g2_b1_executor_agent import (  # noqa: E402
    LOCK_PATH,
    acquire_single_instance,
    release_single_instance,
    sweep_stale_workdirs,
)


def _alive_pid() -> int:
    return os.getpid()


def _dead_pid() -> int:
    """挑一个几乎不可能活的 PID(2=系统会话管理器之下,通常空)。"""
    for pid in range(4, 400):
        try:
            os.kill(pid, 0)
        except OSError:
            return pid
    return 399


def test_lock_blocks_when_holder_alive(tmp_path, monkeypatch):
    lock = tmp_path / "guard.pid"
    monkeypatch.setattr("tools.g2_b1_executor_agent.LOCK_PATH", lock)
    assert acquire_single_instance() is True
    try:
        # 持有者(本进程)还活着 → 第二次获取必须被拒
        assert acquire_single_instance() is False
    finally:
        release_single_instance()
    # 释放后可重新获取
    assert acquire_single_instance() is True
    release_single_instance()


def test_lock_reclaims_stale_dead_pid(tmp_path, monkeypatch):
    lock = tmp_path / "guard.pid"
    monkeypatch.setattr("tools.g2_b1_executor_agent.LOCK_PATH", lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"pid": _dead_pid(), "ts": time.time()}),
                    encoding="utf-8")
    # 持有进程已死 → 锁应被回收
    assert acquire_single_instance() is True
    release_single_instance()


def test_sweep_respects_age_threshold(tmp_path):
    old = tmp_path / "g2b1_exec_old"
    new = tmp_path / "g2b1_exec_new"
    other = tmp_path / "unrelated"
    for d in (old, new, other):
        d.mkdir()
        (d / "x.txt").write_text("x", encoding="utf-8")
    old_ts = time.time() - 7200 - 60
    os.utime(old, (old_ts, old_ts))
    removed = sweep_stale_workdirs(max_age_s=7200, tmp=tmp_path)
    assert removed == 1
    assert not old.exists()
    assert new.exists() and other.exists()  # 新目录与无关目录不动


def test_lock_path_points_outside_repo():
    # 凭据纪律:锁文件与凭据同级,必须在 ~/.nautilus 下(仓库外)
    assert ".nautilus" in str(LOCK_PATH)
