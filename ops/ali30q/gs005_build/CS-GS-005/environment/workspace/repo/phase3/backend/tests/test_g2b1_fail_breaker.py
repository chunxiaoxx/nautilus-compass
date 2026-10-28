# -*- coding: utf-8 -*-
"""g2_b1 executor fail-breaker 单测(2026-08-30 · 治 3 题硬失败循环 136 次空烧 token)

口径:同题连续失败 ≥FAIL_BREAKER_N 次 → 跳过;24h 冷却后半开重试一次。
"""
import json
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
TOOLS = BACKEND / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g2_b1_executor_agent as ex  # noqa: E402

H = 3600


def test_never_failed_not_skipped():
    assert ex.fail_should_skip("06fe5322ee", now=time.time(), state={}) is False


def test_under_threshold_not_skipped():
    st = {"06fe5322ee": [4, time.time()]}
    assert ex.fail_should_skip("06fe5322ee", now=time.time(), state=st) is False


def test_over_threshold_in_cooldown_skipped():
    st = {"06fe5322ee": [5, time.time() - 1 * H]}
    assert ex.fail_should_skip("06fe5322ee", now=time.time(), state=st) is True


def test_over_threshold_cooldown_elapsed_halfopen():
    st = {"06fe5322ee": [7, time.time() - 25 * H]}
    assert ex.fail_should_skip("06fe5322ee", now=time.time(), state=st) is False


def test_custom_threshold():
    st = {"06fe5322ee": [2, time.time()]}
    assert ex.fail_should_skip("06fe5322ee", now=time.time(), state=st, n=2) is True


def test_bump_increments_and_stamps(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "FAIL_STREAK_PATH", tmp_path / "streak.json")
    ex.fail_bump("06fe5322ee", now=1000.0)
    ex.fail_bump("06fe5322ee", now=2000.0)
    d = json.loads((tmp_path / "streak.json").read_text(encoding="utf-8"))
    assert d["06fe5322ee"] == [2, 2000.0]


def test_reset_removes_key(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "FAIL_STREAK_PATH", tmp_path / "streak.json")
    ex.fail_bump("98c8c8f549", now=1.0)
    ex.fail_reset("98c8c8f549")
    d = json.loads((tmp_path / "streak.json").read_text(encoding="utf-8"))
    assert "98c8c8f549" not in d


def test_corrupt_state_loads_empty(tmp_path, monkeypatch):
    p = tmp_path / "streak.json"
    p.write_text("not-json{", encoding="utf-8")
    monkeypatch.setattr(ex, "FAIL_STREAK_PATH", p)
    assert ex._fail_streak_load() == {}


# 9/6 盘满事故(Errno 28):write_text('w') 先截断再写,写不进=0 字节文件,
# 37 个熔断任务冷却记录一夜丢失。原子写=tmp 先写满+os.replace,失败原文件不动。
def test_save_is_atomic_no_tmp_left(tmp_path, monkeypatch):
    import os as _os
    monkeypatch.setattr(ex, "FAIL_STREAK_PATH", tmp_path / "streak.json")
    ex._fail_streak_save({"a": [1, 1.0]})
    d = json.loads((tmp_path / "streak.json").read_text(encoding="utf-8"))
    assert d == {"a": [1, 1.0]}
    assert not list(tmp_path.glob("streak.json.tmp"))  # 成功后无 tmp 残留


def test_save_failure_never_truncates_original(tmp_path, monkeypatch):
    import os as _os
    p = tmp_path / "streak.json"
    p.write_text('{"saved": [5, 123.0]}', encoding="utf-8")
    monkeypatch.setattr(ex, "FAIL_STREAK_PATH", p)

    real_replace = _os.replace

    def _fail_replace(src, dst):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(_os, "replace", _fail_replace)
    monkeypatch.setattr(ex.os, "replace", _fail_replace)
    ex._fail_streak_save({"b": [1, 2.0]})  # 盘满:replace 失败

    # 原文件必须原封不动(未被截断、未被半写)
    assert json.loads(p.read_text(encoding="utf-8")) == {"saved": [5, 123.0]}
