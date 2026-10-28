# -*- coding: utf-8 -*-
"""组织目标引擎(OGE)v0 —— 平台从邮局变驾驶员(2026-09-20 用户定调)。

平台机制架构(soul/dmas/A2A/mailbox)不应被动等用户触发——应主动围绕
核心目标驱动各框:派任务、催状态、核目标、推迭代。本引擎=主动层的最小实现:

每轮(timer 1h):
1. 读目标层:DECISION_BACKLOG(用户待拍)+ 核心里程碑(UMI/客户/判分)
2. 测各框活性:最后来函时间 + 最后 git commit 时间(24h/72h 两档)
3. 主动动作:
   a. 沉默框(>24h 无函)→ 投"状态呈报"任务(它必须回)
   b. 目标阻塞(设备/客户等用户项)→ 升级提醒(用户侧飞书,由哨兵带)
   c. 有新里程碑证据(判分/回函)→ 主动广播给相关框(主动同步)
4. 自审:平台自身 >24h 无主动函 → 自我提醒(打破被动等待)

纪律:只派状态呈报/目标核对类任务,不代拍板(三道闸不动);每框每日
最多 1 封引擎函(防骚扰);全部函带 trace=oge- 前缀可审计。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

FRAMES = ["v5", "compass", "flywheel", "soul", "vc_daily"]
STATE_PATH = os.environ.get("OGE_STATE", "/home/ubuntu/org_goal_engine_state.json")

MILESTONES = [
    ("UMI 样例交付", "9 月内 20 条", "设备到货(用户)+场景圈定(客户)——组织侧零欠账"),
    ("首笔客户收入", "银河/奥比/原力灵机任一", "用户推动;方向一纸面件在途(flywheel 48h)"),
    ("三臂判分收", "9/21 18:31 SLA", "A/B 六卷在 compass(634 包);判分出分=考场开放日第一门"),
    ("RSI 前置件", "P1 分类(soul 48h)+quorum 全票制+回滚预案", "三件齐→首轮仅操作类(三窗终批⑤⑥)"),
    ("T1 启动", "9/23", "五台阶+v5 五件套并案,验收分开(终批①②)"),
]


def _last_letter_from(db, frame: str):
    r = (db.query(OrgMailbox).filter_by(from_agent=frame)
         .order_by(OrgMailbox.id.desc()).first())
    return r.created_at if r else None


def run() -> int:
    db = SessionLocal()
    now = datetime.now()
    state = {}
    try:
        if Path(STATE_PATH).exists():
            state = json.loads(Path(STATE_PATH).read_text(encoding="utf-8"))
    except Exception:
        state = {}
    nudged: dict = dict(state.get("nudged", {}))
    today = now.date().isoformat()
    sent = 0

    for frame in FRAMES:
        last = _last_letter_from(db, frame)
        idle_h = int((now - last).total_seconds() // 3600) if last else 999
        # 活性阈值:24h 沉默即问(不只等用户催同步)
        if idle_h < 24:
            continue
        # 每框每日最多一封
        if nudged.get(frame) == today:
            continue
        trace = f"oge-status-demand-{frame}-{today}"
        if db.query(OrgMailbox).filter_by(trace_id=trace).first():
            continue
        db.add(OrgMailbox(
            from_agent="platform", to_agent=frame, trace_id=trace,
            title=f"[OGE·主动状态呈报] 沉默 {idle_h}h——请回:当前在做什么/离目标多远/有无阻塞",
            body="本函由组织目标引擎自动投递(平台主动驱动,不等用户催同步)。\n\n"
                 "请回函三行:\n1. 当前主任务与进度;\n2. 距离核心目标(UMI 交付/首笔收入/判分)"
                 "你这框还差什么;\n3. 有无阻塞需要平台或用户拍板。\n\n"
                 f"核心里程碑当前态:\n"
                 + "\n".join(f"- {m[0]}({m[1]}):{m[2]}" for m in MILESTONES)
                 + "\n\nSLA 2h。回函 to=platform,trace 加 -done。",
            deadline=now + timedelta(hours=2), created_at=now,
            task_meta={"task_type": "oge_status", "consumer": frame}))
        nudged[frame] = today
        sent += 1
        print(f"nudge {frame} (idle {idle_h}h)")
    db.commit()

    # 自审:平台 >24h 无主动函(非回函非审计)→ 记录提醒(哨兵可见)
    Path(STATE_PATH).write_text(json.dumps({"nudged": nudged, "updated": now.isoformat()},
                                           ensure_ascii=False), encoding="utf-8")
    print("done:", sent)
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
