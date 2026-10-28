"""第一个常驻 agent · 持续推动力 Conductor 大脑(2026-06-22)· 纯逻辑无 IO。

给 DMAS/SOUL 第一个活体成员:常驻 agent 提供持续推动力(跨框同步+对齐北极星+检测停滞推动)。
治多对话框同步痛 + 狗熊掰玉米(session 间失忆失速)。

🔴 反 drift 铁律:只确定性检测 + surface + 触发**白名单预定义步**。绝不开放判断/自改
(=证伪的 Probe3 self-edit 死路)。判断权留对话框/人;agent 只提供动量。
"""
from __future__ import annotations

from typing import Optional

# 北极星收敛序列(7 齿轮精简到中心环主线·compass+soul 共识)
CONVERGENCE_SEQUENCE = ["fuel", "link", "verdict", "memory", "distill"]

# 🔴 白名单:conductor 只能触发这些预定义步(反 drift·不发明动作)
_TRIGGER_WHITELIST = {"run_minting", "run_distill_gate", "poll_verify", "reap_stale"}


def active_gear(gears: dict) -> Optional[str]:
    """北极星对齐:当前 active 齿轮 = 收敛序列里第一个非 done。全 done → None。"""
    for g in CONVERGENCE_SEQUENCE:
        if gears.get(g) != "done":
            return g
    return None


def detect_stalls(snap: dict, max_idle: int = 3) -> list[dict]:
    """停滞检测:某齿轮**就绪(前置 done)却 pending 且 idle 超阈** = 停滞。

    只标"本可推进却停着"的(就绪+超 idle);前置没好的 pending = 正常等待·不算停滞。
    """
    stalls = []
    gears = snap.get("gears", {})
    for g in CONVERGENCE_SEQUENCE:
        if gears.get(g) == "done":
            continue
        ready = snap.get(f"{g}_ready")
        idle = snap.get(f"{g}_idle_cycles", 0)
        if ready and idle > max_idle:
            stalls.append({"gear": g, "idle_cycles": idle})
    return stalls


def momentum_actions(snap: dict) -> list[dict]:
    """确定性推动动作(白名单)。逾期 ball→surface·就绪步→trigger·燃料达阈→蒸馏 gate。"""
    actions: list[dict] = []

    for cnt in snap.get("overdue_contracts", []) or []:
        actions.append({"kind": "surface_overdue", "contract": cnt})

    for step in snap.get("ready_steps", []) or []:
        if step in _TRIGGER_WHITELIST:   # 反 drift:只触发白名单
            actions.append({"kind": "trigger_ready", "step": step})

    fuel = snap.get("fuel_count", 0) or 0
    threshold = snap.get("fuel_threshold", 0) or 0
    if threshold and fuel >= threshold:
        actions.append({"kind": "fuel_threshold_met", "fuel_count": fuel,
                        "step": "run_distill_gate"})

    return actions


def fuel_poc_status(a_bucket: int, records_seen: int, min_n: int = 12) -> dict:
    """A 类燃料对蒸馏首证的状态(纯)· conductor 替人盯 A 类率风险。

    三阶段精确瓶颈(从模糊"gated V5"进到"A类 N/20"):
      awaiting_records = 还没产(0 records)→ 真瓶颈 = V5 产 records
      short            = 产了但 A 类 < min_n → 真瓶颈 = 燃料率不足(扩题/调margin/换producer)
      ready            = A 类 ≥ min_n → 可装训练 env 跑 distill·blocker=None
    min_n = distill_train PROVEN/KILLED 阈值。
    """
    enough = a_bucket >= min_n
    if records_seen == 0:
        phase, blocker = "awaiting_records", \
            "fuel: 0 records·gated on V5 ALE records(蒸馏管线+GPU 就绪)"
    elif not enough:
        phase, blocker = "short", \
            (f"fuel: A类 {a_bucket}/{min_n} 不够首证(产了 {records_seen} records 率不足)"
             f"→ 扩题/调margin/换producer·别先装训练env")
    else:
        phase, blocker = "ready", None
    return {"phase": phase, "a_bucket": a_bucket, "records_seen": records_seen,
            "min_n": min_n, "enough": enough, "blocker": blocker}
