"""ZERO→派单翻译器(P0 dry-run)测试 — 死因分类+触发条件+幂等。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops"))

from supervisor import classify_cause, should_dispatch, build_dispatch_rec  # noqa: E402


def test_cause_yielded_when_experiment_commits():
    assert classify_cause([("feat(dpo): 轮", 2), ("fix: x", 1)]) == "YIELDED"
    assert classify_cause([("feat(v5-P3): DPO轮升级SFT+RL涡轮增压", 1)]) == "YIELDED"


def test_cause_crashed_when_quiet():
    assert classify_cause([("docs: readme", 1)]) == "CRASHED"


def test_cause_unknown_when_no_repo():
    assert classify_cause(None) == "UNKNOWN"


def test_dispatch_only_on_zero_entry():
    assert should_dispatch(prev="CLAIM_ONLY", state="ZERO", already=False) is True
    assert should_dispatch(prev="ZERO", state="ZERO", already=False) is False  # 持续期不重发
    assert should_dispatch(prev="ZERO", state="ZERO", already=True) is False
    assert should_dispatch(prev="CLAIM_ONLY", state="ZERO", already=True) is False  # 已派过
    assert should_dispatch(prev="ACTIVE", state="ACTIVE", already=True) is False


def test_rec_contains_cause_specific_instructions():
    r = build_dispatch_rec(cause="YIELDED", run_id="r1", detail={"commits": 3})
    assert "ETA" in r["instruction"] and "函件" in r["instruction"]
    assert r["cause"] == "YIELDED" and r["mode"] == "dry-run"
    r2 = build_dispatch_rec(cause="CRASHED", run_id="r2", detail={})
    assert "重启" in r2["instruction"]
    r3 = build_dispatch_rec(cause="UNKNOWN", run_id="r3", detail={})
    assert "诊断" in r3["instruction"] and "重启" not in r3["instruction"]
