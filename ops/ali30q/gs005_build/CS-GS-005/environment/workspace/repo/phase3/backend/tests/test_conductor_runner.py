"""Conductor cycle 编排单测(2026-06-22)· 注入 seam·无 IO·fail-soft。

run_conductor_cycle:snapshot_fn → 对齐+检测+判定(纯 conductor_core)→ pulse_fn(写记忆+
alert+触发白名单步)。每动作 fail-soft(一个崩不中断整 cycle·绝不炸常驻进程)。
"""
from __future__ import annotations

from services.conductor_runner import run_conductor_cycle, make_snapshot_fn, make_pulse_fn


def _snap():
    return {
        "gears": {"fuel": "done", "link": "done", "verdict": "done",
                  "memory": "pending", "distill": "pending"},
        "distill_ready": True, "distill_idle_cycles": 5,
        "overdue_contracts": ["cnt_x"],
        "ready_steps": ["run_minting"],
        "fuel_count": 60, "fuel_threshold": 50,
    }


def test_cycle_produces_pulse_with_active_gear_stalls_actions():
    pulses = []
    res = run_conductor_cycle(
        snapshot_fn=_snap,
        pulse_fn=lambda p: pulses.append(p),
    )
    assert len(pulses) == 1
    p = pulses[0]
    assert p["active_gear"] == "memory"            # 序列首个非 done
    assert any(s["gear"] == "distill" for s in p["stalls"])
    kinds = {a["kind"] for a in p["actions"]}
    assert {"surface_overdue", "trigger_ready", "fuel_threshold_met"} <= kinds
    assert res["ok"] is True


def test_cycle_failsoft_when_pulse_raises():
    def boom(p):
        raise RuntimeError("compass memory down")
    # pulse 写崩绝不炸常驻进程
    res = run_conductor_cycle(snapshot_fn=_snap, pulse_fn=boom)
    assert res["ok"] is False
    assert "error" in res


def test_cycle_failsoft_when_snapshot_raises():
    def boom():
        raise RuntimeError("db unreachable")
    res = run_conductor_cycle(snapshot_fn=boom, pulse_fn=lambda p: None)
    assert res["ok"] is False


# ── Phase 2 effect seam:make_snapshot_fn / make_pulse_fn(注入原语) ─────────

def test_make_snapshot_fn_assembles_from_injected_readers():
    fn = make_snapshot_fn(
        gears_reader=lambda: {"fuel": "done", "distill": "pending"},
        loop_reader=lambda: {"fuel_count": 60, "fuel_threshold": 50,
                             "distill_ready": True, "distill_idle_cycles": 5,
                             "ready_steps": ["run_distill_gate"]},
        contracts_reader=lambda: ["cnt_overdue_1"],
    )
    snap = fn()
    assert snap["gears"]["fuel"] == "done"
    assert snap["fuel_count"] == 60
    assert snap["overdue_contracts"] == ["cnt_overdue_1"]


def test_make_pulse_fn_writes_memory_triggers_whitelist_alerts():
    written, triggered, alerted = [], [], []
    pulse_fn = make_pulse_fn(
        memory_writer=lambda p: written.append(p),
        trigger_fn=lambda step: triggered.append(step),
        alert_fn=lambda msg: alerted.append(msg),
    )
    pulse = {
        "active_gear": "distill",
        "stalls": [{"gear": "distill", "idle_cycles": 5}],
        "actions": [
            {"kind": "surface_overdue", "contract": "cnt_x"},
            {"kind": "trigger_ready", "step": "run_distill_gate"},
            {"kind": "fuel_threshold_met", "step": "run_distill_gate", "fuel_count": 60},
        ],
    }
    pulse_fn(pulse)
    assert written == [pulse]                       # pulse 写记忆=连续性
    assert "run_distill_gate" in triggered          # 白名单步触发
    assert len(alerted) >= 1                         # 逾期/停滞 alert


def test_make_pulse_fn_failsoft_per_effect():
    # 一个 effect 崩不中断其余(常驻进程绝不被炸)
    pulse_fn = make_pulse_fn(
        memory_writer=lambda p: (_ for _ in ()).throw(RuntimeError("mem down")),
        trigger_fn=lambda step: None,
        alert_fn=lambda msg: None,
    )
    pulse_fn({"active_gear": "fuel", "stalls": [], "actions": []})  # 不抛
