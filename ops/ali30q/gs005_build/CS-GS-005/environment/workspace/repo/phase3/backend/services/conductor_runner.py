"""Conductor cycle 编排(2026-06-22)· 注入 seam·effect 在工厂里。

run_conductor_cycle:snapshot_fn(读跨框状态)→ 纯大脑(conductor_core 对齐+检测+判定)
→ pulse_fn(写 compass 记忆 + alert + 触发白名单步)。fail-soft:绝不炸常驻进程。

effect 工厂(make_snapshot_fn / make_pulse_fn:读 md/contract/DB·写记忆·触发)= Phase 2
gated 实跑;本编排核纯可单测。systemd 常驻 = Phase 3 gated。
"""
from __future__ import annotations

import logging
from typing import Callable

from services.conductor_core import active_gear, detect_stalls, momentum_actions

logger = logging.getLogger(__name__)


def run_conductor_cycle(
    snapshot_fn: Callable[[], dict],
    pulse_fn: Callable[[dict], None],
    max_idle: int = 3,
) -> dict:
    """一个 conductor cycle:盘点 → 对齐+检测+判定 → 持久化 pulse。fail-soft。

    pulse = ``{active_gear, stalls, actions}``(写 compass 记忆 = 下个对话框 session 起手即读到
    当前状态 = 连续性·治 session 间失忆)。
    """
    try:
        snap = snapshot_fn()
        pulse = {
            "active_gear": active_gear(snap.get("gears", {})),
            "stalls": detect_stalls(snap, max_idle=max_idle),
            "actions": momentum_actions(snap),
        }
        pulse_fn(pulse)
        return {"ok": True, "pulse": pulse}
    except Exception as exc:  # noqa: BLE001 — 常驻进程绝不能被一个 cycle 炸死
        logger.warning("conductor cycle failed (non-fatal): %s", str(exc)[:200])
        return {"ok": False, "error": str(exc)[:200]}


# 触发白名单(与 conductor_core 一致·反 drift)
_TRIGGER_KINDS = {"trigger_ready", "fuel_threshold_met"}


def make_snapshot_fn(gears_reader, loop_reader, contracts_reader):
    """组装 snapshot_fn:注入原语(齿轮态/loop态/逾期contract)→ conductor_core 期望的快照。

    gears_reader()->{gear:status} · loop_reader()->{fuel_count,...ready,idle,ready_steps} ·
    contracts_reader()->[overdue_contract_id]。
    """
    def snapshot_fn() -> dict:
        snap = dict(loop_reader() or {})
        snap["gears"] = gears_reader() or {}
        snap["overdue_contracts"] = contracts_reader() or []
        return snap
    return snapshot_fn


def make_pulse_fn(memory_writer, trigger_fn, alert_fn):
    """组装 pulse_fn:写 compass 记忆(连续性)+ 触发白名单步 + alert 逾期/停滞。

    每 effect fail-soft(一个崩不中断其余·常驻进程绝不被炸)。
    """
    def _safe(fn, *a):
        try:
            fn(*a)
        except Exception as exc:  # noqa: BLE001
            logger.warning("conductor effect failed (non-fatal): %s", str(exc)[:160])

    def pulse_fn(pulse: dict) -> None:
        _safe(memory_writer, pulse)                       # 写记忆 = 下个 session 连续性
        for s in pulse.get("stalls", []) or []:
            _safe(alert_fn, f"stall: gear={s.get('gear')} idle={s.get('idle_cycles')}")
        for a in pulse.get("actions", []) or []:
            kind = a.get("kind")
            if kind == "surface_overdue":
                _safe(alert_fn, f"overdue contract: {a.get('contract')}")
            elif kind in _TRIGGER_KINDS and a.get("step"):
                _safe(trigger_fn, a["step"])             # 白名单步(core 已过滤)
    return pulse_fn
