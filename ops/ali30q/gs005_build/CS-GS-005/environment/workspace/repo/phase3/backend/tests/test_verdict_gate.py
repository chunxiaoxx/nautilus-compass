"""verdict-gate 硬门测试(2026-06-25)。

鬼打墙真解的第一个硬门:把"过早下 KILL/PROVEN 结论"从软提醒(anchor/memory·靠自我监控)
升级成 code-enforced 门。本 session 整天代价=反复在测量没闭环时下结论(KILL->正->稀疏)·
n=12 小样本·无异框验证。此门让 runner 代码层拒绝无 enforcement artifact 的强结论。
"""
from __future__ import annotations

from services.verdict_gate import gate_verdict


def test_non_strong_verdict_passes_through():
    r = gate_verdict("INCONCLUSIVE", confound_checked=False, n_samples=2, min_n=12)
    assert r["allowed"] is True
    assert r["verdict"] == "INCONCLUSIVE"


def test_killed_blocked_without_confound_check():
    r = gate_verdict("KILLED", confound_checked=False, n_samples=20, min_n=12)
    assert r["allowed"] is False
    assert "CONFOUND" in r["verdict"]


def test_killed_allowed_with_confound_check_and_enough_n():
    r = gate_verdict("KILLED", confound_checked=True, n_samples=20, min_n=12)
    assert r["allowed"] is True
    assert r["verdict"] == "KILLED"


def test_small_n_forces_inconclusive_even_if_confound_checked():
    r = gate_verdict("KILLED", confound_checked=True, n_samples=11, min_n=12)
    assert r["allowed"] is True
    assert r["verdict"] == "INCONCLUSIVE"
    assert "n" in r["reason"].lower()


def test_proven_blocked_without_cross_frame():
    r = gate_verdict("PROVEN", confound_checked=True, cross_frame_verified=False,
                     n_samples=20, min_n=12)
    assert r["allowed"] is False
    assert "CROSS_FRAME" in r["verdict"]


def test_proven_allowed_with_confound_and_cross_frame():
    r = gate_verdict("PROVEN", confound_checked=True, cross_frame_verified=True,
                     n_samples=20, min_n=12)
    assert r["allowed"] is True
    assert r["verdict"] == "PROVEN"


def test_proven_small_n_forces_inconclusive():
    r = gate_verdict("PROVEN", confound_checked=True, cross_frame_verified=True,
                     n_samples=5, min_n=12)
    assert r["allowed"] is True
    assert r["verdict"] == "INCONCLUSIVE"
