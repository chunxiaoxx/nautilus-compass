"""第一个常驻 agent · 持续推动力 Conductor 纯逻辑单测(2026-06-22)。

反 drift 铁律:只确定性检测 + surface + 触发白名单预定义步·绝不开放判断/自改。
本模块=大脑(北极星对齐 + 停滞检测 + 推动动作判定)·无 IO·本地可 TDD。
effect(读 md/DB·写 compass 记忆·alert·触发)在 conductor_runner(注入 seam)。
"""
from __future__ import annotations

from services.conductor_core import (
    CONVERGENCE_SEQUENCE,
    active_gear,
    detect_stalls,
    fuel_poc_status,
    momentum_actions,
)


# ── A 类燃料对首证的三阶段状态(conductor 替人盯 A 类率风险)──────────────

def test_fuel_status_awaiting_records():
    s = fuel_poc_status(a_bucket=0, records_seen=0, min_n=20)
    assert s["phase"] == "awaiting_records"
    assert s["enough"] is False
    assert "V5 ALE records" in s["blocker"]


def test_fuel_status_short_records_produced_but_rate_low():
    # 产了 40 records 但只 5 条 A 类 → 真瓶颈 = 率不足(非"等 records")
    s = fuel_poc_status(a_bucket=5, records_seen=40, min_n=20)
    assert s["phase"] == "short"
    assert s["enough"] is False
    assert "5/20" in s["blocker"]
    assert "换producer" in s["blocker"]


def test_fuel_status_default_min_n_is_12():
    # 默认阈值降 20→12(首证·ALE+qwen A类产率低)
    s = fuel_poc_status(a_bucket=12, records_seen=48)   # 用默认 min_n
    assert s["min_n"] == 12
    assert s["enough"] is True


def test_fuel_status_ready_no_blocker():
    s = fuel_poc_status(a_bucket=22, records_seen=40, min_n=20)
    assert s["phase"] == "ready"
    assert s["enough"] is True
    assert s["blocker"] is None


# ── 北极星对齐:当前 active 齿轮 = 序列里第一个非 done ──────────────────────

def test_convergence_sequence_order():
    # ①燃料→②LINK→③verdict→⑤记忆→⑦蒸馏(收敛序列)
    assert CONVERGENCE_SEQUENCE == ["fuel", "link", "verdict", "memory", "distill"]


def test_active_gear_first_incomplete():
    gears = {"link": "done", "verdict": "done", "fuel": "building",
             "memory": "pending", "distill": "pending"}
    assert active_gear(gears) == "fuel"   # fuel 在序列最前且非 done


def test_active_gear_skips_done_returns_next():
    gears = {"fuel": "done", "link": "done", "verdict": "done",
             "memory": "pending", "distill": "pending"}
    assert active_gear(gears) == "memory"


def test_active_gear_all_done_returns_none():
    gears = {g: "done" for g in CONVERGENCE_SEQUENCE}
    assert active_gear(gears) is None


# ── 停滞检测:就绪(前置 done)却 pending 超 idle = stall ──────────────────

def test_detect_stalls_flags_ready_but_idle():
    snap = {"gears": {"fuel": "done", "distill": "pending"},
            "distill_ready": True, "distill_idle_cycles": 5}
    stalls = detect_stalls(snap, max_idle=3)
    assert any(s["gear"] == "distill" for s in stalls)


def test_detect_stalls_none_when_within_idle():
    snap = {"gears": {"fuel": "done", "distill": "pending"},
            "distill_ready": True, "distill_idle_cycles": 1}
    assert detect_stalls(snap, max_idle=3) == []


def test_detect_stalls_none_when_not_ready():
    # 前置没好(distill_ready=False)→ 不算停滞(是正常等待)
    snap = {"gears": {"fuel": "building", "distill": "pending"},
            "distill_ready": False, "distill_idle_cycles": 9}
    assert detect_stalls(snap, max_idle=3) == []


# ── 推动动作判定:确定性·白名单 ──────────────────────────────────────────

def test_momentum_surfaces_overdue_and_triggers_ready_and_fuel_threshold():
    snap = {"overdue_contracts": ["cnt_x"], "ready_steps": ["run_minting"],
            "fuel_count": 60, "fuel_threshold": 50}
    acts = momentum_actions(snap)
    kinds = {a["kind"] for a in acts}
    assert "surface_overdue" in kinds
    assert "trigger_ready" in kinds
    assert "fuel_threshold_met" in kinds


def test_momentum_quiet_no_action():
    assert momentum_actions({"fuel_count": 0, "fuel_threshold": 50}) == []


def test_momentum_trigger_only_whitelisted_steps():
    # 非白名单 step 不触发(反 drift:不发明/不执行任意动作)
    snap = {"ready_steps": ["rm_rf_everything", "run_minting"],
            "fuel_count": 0, "fuel_threshold": 50}
    acts = momentum_actions(snap)
    triggered = [a["step"] for a in acts if a["kind"] == "trigger_ready"]
    assert "run_minting" in triggered
    assert "rm_rf_everything" not in triggered   # 不在白名单=拒
