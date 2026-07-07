"""compass economy liveness probe tests · fake conn 注入 · 不依赖网络/真 DB。

覆盖每探针的 GREEN/STALE/GAP/RED 分支 + income 独立复现语义 + 引擎停摆诊断 +
agent_survival GRANT 缺口的诚实上报(不 fake-GREEN)。anchor #5 不另造连接。
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from ops.economy_liveness_probe import (  # noqa: E402
    probe_verified_income,
    probe_engine_cycle_liveness,
    probe_income_ground_truth,
    probe_income_growth,
    diff_income,
    run_all,
    GREEN, STALE, GAP, RED,
    GROW, FLAT, DROP, FIRST,
    PROBE_INCOME, PROBE_CYCLE, PROBE_GROUND_TRUTH,
)

_NOW = datetime.now(timezone.utc)
_RECENT = _NOW - timedelta(hours=1)
_OLD = _NOW - timedelta(days=34)


class _FakeCursor:
    """execute 可选抛异常(模拟 permission denied);fetchone 返回预设行。"""
    def __init__(self, row=None, raise_exc=None):
        self._row = row
        self._raise = raise_exc

    def execute(self, sql, params=None):
        if self._raise is not None:
            raise self._raise

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def _conn(row=None, raise_exc=None):
    return _FakeConn(_FakeCursor(row=row, raise_exc=raise_exc))


# ---- probe_verified_income ----

def test_verified_income_green_derives_188():
    """2 条铸币 verdict · sum(round(score))=188 · 新鲜 → GREEN + 独立复现 188。"""
    r = probe_verified_income(_conn(row=(188, 2, _RECENT)))
    assert r["status"] == GREEN
    assert r["derived_income"] == 188
    assert r["minting_count"] == 2


def test_verified_income_stale_no_minting():
    """0 条铸币 → STALE · income 0(不 fake-GREEN)。"""
    r = probe_verified_income(_conn(row=(0, 0, None)))
    assert r["status"] == STALE
    assert r["derived_income"] == 0


def test_verified_income_stale_when_verify_old():
    """有历史铸币但 latest verify 超阈值 → STALE(链停滞)。"""
    r = probe_verified_income(_conn(row=(188, 2, _OLD)))
    assert r["status"] == STALE
    assert r["derived_income"] == 188


def test_verified_income_red_on_read_fail():
    r = probe_verified_income(_conn(raise_exc=RuntimeError("boom")))
    assert r["status"] == RED
    assert "read fail" in r["detail"]


# ---- probe_engine_cycle_liveness ----

def test_engine_cycle_green_when_active():
    """近 24h 有 cycle + 新鲜 → GREEN。"""
    r = probe_engine_cycle_liveness(_conn(row=(_RECENT, 49, 3)))
    assert r["status"] == GREEN
    assert r["cycles_24h"] == 3


def test_engine_cycle_stale_exposes_theater():
    """last cycle 34d 前 + 0 cycles_24h → STALE(引擎自循环停摆 · 独立揭穿剧场)。"""
    r = probe_engine_cycle_liveness(_conn(row=(_OLD, 49, 0)))
    assert r["status"] == STALE
    assert r["cycles_24h"] == 0
    assert "停摆" in r["detail"]


def test_engine_cycle_red_on_read_fail():
    r = probe_engine_cycle_liveness(_conn(raise_exc=RuntimeError("boom")))
    assert r["status"] == RED


# ---- probe_income_ground_truth ----

def test_ground_truth_green_reads_total():
    r = probe_income_ground_truth(_conn(row=(188, "GROWING", "alive")), producer_agent_id=9000009)
    assert r["status"] == GREEN
    assert r["total_income"] == 188


def test_ground_truth_gap_on_permission_denied():
    """compass_sub 无 grant → GAP + needs_grant(诚实缺口 · 绝不 fake-GREEN)。"""
    exc = Exception("permission denied for table agent_survival")
    r = probe_income_ground_truth(_conn(raise_exc=exc))
    assert r["status"] == GAP
    assert "GRANT SELECT ON agent_survival" in r["needs_grant"]


def test_ground_truth_red_on_other_error():
    r = probe_income_ground_truth(_conn(raise_exc=RuntimeError("connection reset")))
    assert r["status"] == RED


def test_ground_truth_stale_when_agent_absent():
    r = probe_income_ground_truth(_conn(row=None))
    assert r["status"] == STALE


# ---- diff_income / probe_income_growth (③ 盯 income 持续涨) ----

def test_diff_income_first_when_no_watermark(tmp_path):
    wm = tmp_path / "wm.json"
    r = diff_income(188, wm)
    assert r["status"] == FIRST
    assert r["current"] == 188
    assert wm.exists()  # 首次也记录


def test_diff_income_grow(tmp_path):
    wm = tmp_path / "wm.json"
    diff_income(188, wm)                 # 先记 188
    r = diff_income(286, wm)             # 涨到 286
    assert r["status"] == GROW
    assert r["delta"] == 98


def test_diff_income_flat_frozen_at_188(tmp_path):
    """当前真态:income 冻在 188(引擎停摆)→ FLAT。"""
    wm = tmp_path / "wm.json"
    diff_income(188, wm)
    r = diff_income(188, wm)
    assert r["status"] == FLAT
    assert r["delta"] == 0


def test_diff_income_drop_flags_rollback(tmp_path):
    wm = tmp_path / "wm.json"
    diff_income(286, wm)
    r = diff_income(188, wm)             # 账修正回滚(SSOT 有此实例)
    assert r["status"] == DROP
    assert r["delta"] == -98


def test_diff_income_record_false_does_not_write(tmp_path):
    wm = tmp_path / "wm.json"
    diff_income(188, wm, record=False)
    assert not wm.exists()


def test_probe_income_growth_reads_conn_then_diffs(tmp_path):
    wm = tmp_path / "wm.json"
    r = probe_income_growth(_conn(row=(188, 2, _RECENT)), watermark_path=wm)
    assert r["status"] == FIRST
    assert r["current"] == 188


def test_probe_income_growth_red_when_income_unreadable(tmp_path):
    wm = tmp_path / "wm.json"
    r = probe_income_growth(_conn(raise_exc=RuntimeError("boom")), watermark_path=wm)
    assert r["status"] == RED


# ---- run_all ----

def test_run_all_returns_three_probes():
    """run_all 用同一 conn 跑 3 探针(fake 每探针同一行 · 只验聚合结构)。"""
    conn = _conn(row=(188, 2, _RECENT))
    out = run_all(conn)
    assert set(out) == {PROBE_INCOME, PROBE_CYCLE, PROBE_GROUND_TRUTH}
    for v in out.values():
        assert v["status"] in {GREEN, STALE, GAP, RED}
