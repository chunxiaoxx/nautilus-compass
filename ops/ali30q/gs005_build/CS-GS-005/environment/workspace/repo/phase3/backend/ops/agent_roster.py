# -*- coding: utf-8 -*-
"""组织 agent 名册读数(U16 · 2026-09-26 用户批四件之①)——治"名册失联无人知"。

四源合并:①org_mailbox 发函(最强活性)②platform_audit 台账 ③云 systemd 服务探活
(仅 v5 内部件计为信号)④云仓 git 最近提交。每身份一行 {最近信号源,时龄 h,status}:
>48h=RED,>24h=WARN,无任何信号=RED(fail-loud)。

死轨道(agent_dispatch_log 死于 5/29 / agent_survival 空表 / agent_messages 死于
9/21 / 注册表 last_heartbeat 停更 9/1)显式标注 deprecated,禁作活性源——9/25 平台
两度凭死轨道误判"agent 全红"的根治。

本地可测:纯函数无云依赖;DB/进程探针全部懒加载(同 auto_ack 配方)。
用法:python3 ops/agent_roster.py            # 只读打印 JSON(验证模式)
     python3 ops/agent_roster.py --emit     # 额外写 platform_audit 台账行(timer 用)
部署窗后由 nautilus-agent-roster.timer 每 2h 调用(emit 模式)。
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

# 名册正本(9/25 深度普查定稿;改这里=改名册,须留 commit 痕)
ROSTER: dict[str, dict] = {
    "platform": {"kind": "dialog", "services": ["nautilus-backend.service"],
                 "repo": "/home/ubuntu/nautilus-mvp"},
    "compass": {"kind": "dialog",
                "services": ["compass.service", "compass-mcp-http.service",
                             "compass-bge-daemon.service"], "repo": None},
    "v5": {"kind": "dialog",
           "services": ["nautilus-v5-api.service", "feishu-callback.service"],
           "repo": "/home/ubuntu/nautilus-v5"},
    "flywheel": {"kind": "dialog", "services": ["flywheel-console.service"],
                 "repo": None},
    "soul": {"kind": "timer", "services": [],
             "repo": "/home/ubuntu/nautilus-soul-workspace"},
    "vc_daily": {"kind": "dialog", "services": [], "repo": None},  # 无居所,仅信箱面
    "kairos": {"kind": "v5-part", "services": ["nautilus-kairos.service"], "repo": None},
    "v7-telegram": {"kind": "v5-part", "services": ["fde-runner@v7-telegram.service"], "repo": None},  # 实际unit名(216b527b1前旧名查不到进程)
    "ag_local_laptop_001": {"kind": "worker", "services": [], "repo": None},
    "zenmind": {"kind": "dialog", "services": [], "repo": None},  # U20 用户批 9/26:台式机个人助理框(第六框),活性=mail_out(每日 22:00 digest)
}
DEPRECATED_TRACKS = {
    "agent_dispatch_log": "死于 2026-05-29",
    "agent_survival": "空表(从未启用)",
    "agent_messages": "死于 2026-09-21",
    "platform_agents.last_heartbeat": "停更 2026-09-01",
}
WARN_H, RED_H = 24.0, 48.0


def status_from_age(h_ago: float | None) -> str:
    """无信号=RED(fail-loud);>48h RED;>24h WARN;否则 GREEN。"""
    if h_ago is None:
        return "RED"
    return "RED" if h_ago > RED_H else ("WARN" if h_ago > WARN_H else "GREEN")


def merge_signals(signals: dict, now_epoch: float) -> tuple:
    """signals: {source: epoch|None} → (best_source, h_ago)。取最近者;全 None → (None, None)。"""
    cand = [(src, ts) for src, ts in signals.items() if ts is not None]
    if not cand:
        return None, None
    src, ts = max(cand, key=lambda x: x[1])
    return src, round((now_epoch - ts) / 3600, 1)


def build_row(agent: str, cfg: dict, signals: dict, services_state: dict,
              now_epoch: float) -> dict:
    """组装单行。v5-part 以服务活性为信号(进程活=0h);dialog/worker 只认产出信号。"""
    if cfg["kind"] == "v5-part":
        live = all(services_state.get(s) == "active" for s in cfg["services"]) \
            and bool(cfg["services"])
        sig = dict(signals)
        sig["service"] = now_epoch if live else None
        best_src, h = merge_signals(sig, now_epoch)
    else:
        best_src, h = merge_signals(signals, now_epoch)
    return {"agent": agent, "kind": cfg["kind"],
            "status": status_from_age(h),
            "best_source": best_src, "h_ago": h,
            "signals": {k: (round((now_epoch - v) / 3600, 1)
                            if v is not None else None)
                        for k, v in signals.items()},
            "services": services_state}


# --- 云上探针(懒加载;本地单测不触达) ---


def _svc_state(svc: str) -> str:
    r = subprocess.run(["systemctl", "is-active", svc],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip() or "unknown"


def _repo_epoch(path: str):
    r = subprocess.run(["git", "-C", path, "log", "-1", "--format=%ct"],
                       capture_output=True, text=True, timeout=30)
    return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def _probe_all() -> dict:
    sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
    import models.agent_survival  # noqa: F401 — mapper dependency
    from sqlalchemy import text
    from utils.database import SessionLocal

    now_epoch = datetime.now(CST).timestamp()
    s = SessionLocal()
    try:
        mail = {a: ts.replace(tzinfo=CST).timestamp() for a, ts in s.execute(
            text("SELECT from_agent, max(created_at) FROM org_mailbox GROUP BY 1"))}
        audit = {a: (ts.timestamp() if ts.tzinfo else ts.replace(tzinfo=CST).timestamp())
                 for a, ts in s.execute(
                     text("SELECT actor, max(ts) FROM platform_audit GROUP BY 1"))}
        # 行为探针(U32 20261001 宿主心跳:治"活着无行为"三例病族——kairos/v7 心跳
        # 写 platform_agents(9/28 由 v5 重接活,旧 deprecated 标注作废);进程活+行为死=RED
        heartbeat = {a: (ts.replace(tzinfo=CST).timestamp() if not ts.tzinfo else ts.timestamp())
                     for a, ts in s.execute(
                         text("SELECT agent_id, max(last_heartbeat) FROM platform_agents GROUP BY 1")) if ts is not None}
    finally:
        s.close()

    rows = []
    for agent, cfg in ROSTER.items():
        services_state = {svc: _svc_state(svc) for svc in cfg["services"]}
        signals = {"mail_out": mail.get(agent),
                   "audit": audit.get(agent),
                   "git_commit": _repo_epoch(cfg["repo"]) if cfg["repo"] else None,
                   "heartbeat": heartbeat.get(agent)}  # 行为层:心跳新鲜度
        row = build_row(agent, cfg, signals, services_state, now_epoch)
        # 活着无行为检测(v5-part 类:进程活但心跳>2h 未写=行为死,RED)
        if cfg.get("kind") == "v5-part":
            hb = heartbeat.get(agent)
            proc_alive = any(v == "active" for v in services_state.values()) if services_state else False
            if proc_alive and (hb is None or now_epoch - hb > 2 * 3600):
                row["status"] = "RED"
                row["note"] = (row.get("note") or "") + " 行为死:进程活+心跳>" + (
                    "无记录" if hb is None else f"{(now_epoch - hb) / 3600:.1f}h")
        rows.append(row)
    rows.sort(key=lambda r: (r["status"] != "RED", r["status"] != "WARN",
                             -(r["h_ago"] or 999)))
    return {"generated_at": datetime.now(CST).isoformat(timespec="seconds"),
            "window": {"WARN_h": WARN_H, "RED_h": RED_H},
            "agents": rows, "deprecated_tracks": DEPRECATED_TRACKS}


def _emit_audit(summary: dict) -> None:
    sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
    from datetime import datetime
    import models.agent_survival  # noqa: F401 — mapper dependency
    from models.platform_audit import PlatformAudit
    from utils.database import SessionLocal
    s = SessionLocal()
    try:
        s.add(PlatformAudit(
            ts=datetime.now(),  # 表列 NOT NULL 无默认(9/26 首跑 NotNullViolation 实证)
            actor="agent-roster", actor_type="system", action="roster_scan",
            target="org", target_type="roster",
            outcome="red" if any(r["status"] == "RED" for r in summary["agents"])
            else "ok", ip="127.0.0.1",
            meta={"n": len(summary["agents"]),
                  "red": [r["agent"] for r in summary["agents"]
                          if r["status"] == "RED"][:5]}))
        s.commit()
    finally:
        s.close()


if __name__ == "__main__":
    out = _probe_all()
    if "--emit" in sys.argv:
        _emit_audit(out)
    print(json.dumps(out, ensure_ascii=False, indent=1), flush=True)
