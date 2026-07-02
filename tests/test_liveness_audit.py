"""compass liveness framework tests · 验证 GREEN/RED 切换。

不依赖网络/真路径 · 用临时 snapshot 文件 + 临时 patch 文件 fake · 锚 #5 不另造。
"""
import json
import os
import sys
import time
from pathlib import Path

import pytest

# 加 worktree root 到 sys.path · 方便 import ops.liveness_audit
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))
from ops.liveness_audit import (  # noqa: E402
    probe_ledger_growth,
    probe_snapshot_freshness,
    probe_impact_axis,
    run_all,
    PROBE_LEDGER,
    PROBE_FRESHNESS,
    PROBE_IMPACT,
)


# ---- probe_ledger_growth ----

def test_probe_ledger_growth_green_with_fake_snapshot(tmp_path):
    """fake snapshot 有 > 1 行 → GREEN。"""
    fake = tmp_path / "fake_snapshot.json"
    fake.write_text(json.dumps({"a": 1.0, "b": 2.0, "c": 3.0}))
    r = probe_ledger_growth(fake, min_lines=1)
    assert r["status"] == "GREEN"
    assert "lines = 3" in r["detail"]


def test_probe_ledger_growth_red_missing(tmp_path):
    """snapshot 不存在 → RED。"""
    r = probe_ledger_growth(tmp_path / "nonexistent.json", min_lines=1)
    assert r["status"] == "RED"
    assert "missing" in r["detail"]


def test_probe_ledger_growth_red_too_few_lines(tmp_path):
    """snapshot 存在但行数 ≤ min_lines → RED。"""
    fake = tmp_path / "fake.json"
    fake.write_text(json.dumps({}))
    r = probe_ledger_growth(fake, min_lines=1)
    assert r["status"] == "RED"


# ---- probe_snapshot_freshness ----

def test_probe_snapshot_freshness_green_recent(tmp_path):
    """新 fake 文件 mtime 接近当前 → GREEN。"""
    fake = tmp_path / "fresh.json"
    fake.write_text("{}")
    r = probe_snapshot_freshness(fake, max_age_hours=2.0)
    assert r["status"] == "GREEN"


def test_probe_snapshot_freshness_green_within_dev_tolerance(tmp_path):
    """dev 机器默认 168h 容差:1 天老文件 → GREEN(用默认阈值跑)。"""
    from ops import liveness_audit as LA
    fake = tmp_path / "old.json"
    fake.write_text("{}")
    old_time = time.time() - 86400  # 1 day ago
    os.utime(fake, (old_time, old_time))
    r = probe_snapshot_freshness(fake, max_age_hours=LA.DEFAULT_FRESHNESS_HOURS)
    assert r["status"] == "GREEN"
    assert "168" in r["detail"] or "week" in r["detail"].lower() or "h" in r["detail"]


def test_probe_snapshot_freshness_red_old(tmp_path):
    """老 fake 文件(超过 max_age_hours)→ RED。"""
    fake = tmp_path / "old.json"
    fake.write_text("{}")
    very_old = time.time() - (200 * 3600)  # 200 小时前
    os.utime(fake, (very_old, very_old))
    r = probe_snapshot_freshness(fake, max_age_hours=168.0)
    assert r["status"] == "RED"


def test_probe_snapshot_freshness_red_strict_2h(tmp_path):
    """production 严格 2h 阈值:1 天老文件 → RED(显式传 2h)。"""
    fake = tmp_path / "old.json"
    fake.write_text("{}")
    old_time = time.time() - 86400  # 1 day ago
    os.utime(fake, (old_time, old_time))
    r = probe_snapshot_freshness(fake, max_age_hours=2.0)
    assert r["status"] == "RED"


def test_probe_snapshot_freshness_red_missing(tmp_path):
    """snapshot 缺失 → RED。"""
    r = probe_snapshot_freshness(tmp_path / "nonexistent.json", max_age_hours=2.0)
    assert r["status"] == "RED"


# ---- probe_impact_axis ----

def test_probe_impact_axis_green_with_wiring(tmp_path):
    """fake patch 含 2 个真 wiring 标记 → GREEN。"""
    fake = tmp_path / "patch.py"
    fake.write_text(
        "def _v14_poi_boost(hits): pass\n"
        "x = _v14_poi_boost(_h)\n"
    )
    r = probe_impact_axis(fake)
    assert r["status"] == "GREEN"
    assert "wiring ok" in r["detail"]


def test_probe_impact_axis_red_partial_wiring(tmp_path):
    """fake patch 只含部分标记 → RED(明确报缺哪个)。"""
    fake = tmp_path / "patch.py"
    fake.write_text("def _v14_poi_boost(hits): pass\n")  # 只 fn_def
    r = probe_impact_axis(fake)
    assert r["status"] == "RED"
    assert "call_site" in r["detail"]


def test_probe_impact_axis_red_no_wiring(tmp_path):
    """fake patch 不含任何标记 → RED。"""
    fake = tmp_path / "patch.py"
    fake.write_text("# no wiring here\n")
    r = probe_impact_axis(fake)
    assert r["status"] == "RED"


def test_probe_impact_axis_red_missing(tmp_path):
    """patch 文件不存在 → RED。"""
    r = probe_impact_axis(tmp_path / "nonexistent.py")
    assert r["status"] == "RED"


# ---- run_all ----

def test_run_all_returns_3_probes(tmp_path):
    """run_all 返 3 个探针名(GREEN/RED 任意)。"""
    fake_snap = tmp_path / "snap.json"
    fake_snap.write_text("{}")  # 0 lines → RED
    fake_patch = tmp_path / "patch.py"
    fake_patch.write_text("def _v14_poi_boost(hits): pass\n_v14_poi_boost(_h)")  # GREEN
    r = run_all(snapshot_path=fake_snap, patch_file=fake_patch)
    assert PROBE_LEDGER in r
    assert PROBE_FRESHNESS in r
    assert PROBE_IMPACT in r
    assert all("status" in v and "detail" in v for v in r.values())
