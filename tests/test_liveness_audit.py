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


def test_probe_snapshot_freshness_red_old(tmp_path):
    """老 fake 文件(mtime 1 天前)→ RED。"""
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
    """fake patch 含 'poi_impact' 字符串 → GREEN。"""
    fake = tmp_path / "patch.py"
    fake.write_text("# fake patch\npoi_impact = 0.5\n")
    r = probe_impact_axis(fake)
    assert r["status"] == "GREEN"
    assert "True" in r["detail"]


def test_probe_impact_axis_red_no_wiring(tmp_path):
    """fake patch 不含 'poi_impact' → RED。"""
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
    fake_patch.write_text("poi_impact = 0.5")  # GREEN
    r = run_all(snapshot_path=fake_snap, patch_file=fake_patch)
    assert PROBE_LEDGER in r
    assert PROBE_FRESHNESS in r
    assert PROBE_IMPACT in r
    assert all("status" in v and "detail" in v for v in r.values())
