# -*- coding: utf-8 -*-
"""g2_b1_daily_miner 单测(2026-09-07 定时化):幂等去重 / 锁防重入 / repo_path 规范。

背景:9/7 手动挖矿 58 题一天消化完,矿源=组织自身 commit 增长,故定时化每日增量挖。
幂等键 = (repo_path 规范化, buggy_commit, reference_fix_commit) —— 历史批次里
正斜杠/反斜杠混用(nautilus-compass 两种写法都有),规范化后必须视为同仓。
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
TOOLS = BACKEND / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g2_b1_daily_miner as dm  # noqa: E402


def test_norm_repo_slash_insensitive():
    a = dm.norm_repo("C:/Users/chunx/Projects/nautilus-core")
    b = dm.norm_repo(r"C:\Users\chunx\Projects\nautilus-core")
    assert a == b


def test_norm_repo_case_insensitive():
    assert dm.norm_repo("C:/Users/CHUNX/Projects/x") == dm.norm_repo("C:/Users/chunx/Projects/x")


def test_dedupe_skips_existing_key():
    existing = {(dm.norm_repo("C:/x/repo"), "aaa", "bbb")}
    rows = [
        {"repo_path": r"C:\x\repo", "buggy_commit": "aaa", "reference_fix_commit": "bbb"},
        {"repo_path": "C:/x/repo", "buggy_commit": "ccc", "reference_fix_commit": "ddd"},
    ]
    kept = dm.dedupe(existing, rows)
    assert len(kept) == 1
    assert kept[0]["buggy_commit"] == "ccc"


def test_dedupe_new_rows_get_repo_path():
    rows = [{"buggy_commit": "a", "reference_fix_commit": "b",
             "repo_path": "C:/x/repo"}]
    kept = dm.dedupe(set(), rows)
    assert kept == rows  # 原样保留(executor 逐行读 repo_path)


def test_queue_keys_from_jsonl_rows():
    rows = [
        {"repo_path": "C:/x/repo", "buggy_commit": "a", "reference_fix_commit": "b"},
        {"repo_path": "C:/y/repo", "buggy_commit": "c", "reference_fix_commit": "d"},
        {"buggy_commit": "e", "reference_fix_commit": "f"},  # 历史 row 缺 repo_path
    ]
    keys = dm.queue_keys(rows)
    assert keys == {(dm.norm_repo("C:/x/repo"), "a", "b"),
                    (dm.norm_repo("C:/y/repo"), "c", "d")}


def test_acquire_lock_fresh_blocks(tmp_path):
    p = tmp_path / "l.lock"
    assert dm.acquire_lock(p, now=1000.0) is True
    assert dm.acquire_lock(p, now=1000.0 + 60) is False  # 新鲜锁 → 第二实例退


def test_acquire_lock_stale_preempts(tmp_path):
    p = tmp_path / "l.lock"
    assert dm.acquire_lock(p, now=1000.0) is True
    assert dm.acquire_lock(p, now=1000.0 + dm.LOCK_MAX_AGE + 1) is True


def test_acquire_lock_corrupt_file_preempts(tmp_path):
    p = tmp_path / "l.lock"
    p.write_text("garbage", encoding="utf-8")
    assert dm.acquire_lock(p, now=1000.0) is True


def test_release_lock_allows_reacquire(tmp_path):
    p = tmp_path / "l.lock"
    dm.acquire_lock(p, now=1000.0)
    dm.release_lock(p)
    assert dm.acquire_lock(p, now=1001.0) is True


def test_acquire_lock_writes_pid(tmp_path):
    import os
    p = tmp_path / "l.lock"
    dm.acquire_lock(p, now=1000.0)
    content = p.read_text(encoding="utf-8")
    assert content.endswith(f"|{os.getpid()}")
