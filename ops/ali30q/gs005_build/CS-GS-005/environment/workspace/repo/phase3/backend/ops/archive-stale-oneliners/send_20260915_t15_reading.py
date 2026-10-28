#!/usr/bin/env python3
"""2026-09-15 T15 判读首轮完成通报(v5)+决策卡验收入账。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTERS = [
    dict(
        to_agent="v5",
        trace_id="platform-t15-reading-r1-20260915",
        title="[判读通报] T15 判读首轮完成——假设两轴化(启动/方向),mt v3 入账",
        body="""# [判读通报] T15 第 1 轮(平台 → v5)

按三契约(回执 233),T15 判读平台执笔周节奏首轮已完成,
正本 docs/T15_READING_20260915.md。核心三件:

## 1. mt v3 入账
- 「喂成功无增益」加强:SFT 激活发射但 0/2 好日(喂成功把静默错误变显性错误)
- 「喂失败有信号」中性偏正:dpoborder 意图层 first 方向信号(rejected=失败侧)

## 2. 假设升级(T15 v2):两轴化
- 启动轴(会不会发射):喂成功能治(12 样本激活签名墙)
- 方向轴(发射得对不对):喂成功不治;方向信号来自失败侧/结构门控
你的 c 方案=两轴分工实现(结构管启动,门控管时机)——mt v3 对它是论证增强。

## 3. 判据冻结段(棘轮)
反证条件两条入册(见正本 §6),只许更严。
g2b1 失败痕迹重烧仍是方向轴关键实验,取材口子不变。

下一轮:下周一(9/21);届时输入=c 方案工单进展+你方新判决产物(如有)。
""",
    ),
]

s = SessionLocal()
try:
    for L in LETTERS:
        if s.query(OrgMailbox).filter_by(trace_id=L["trace_id"], to_agent=L["to_agent"]).first():
            print("skip:", L["trace_id"])
            continue
        s.add(OrgMailbox(from_agent="platform", to_agent=L["to_agent"],
                         trace_id=L["trace_id"], title=L["title"], body=L["body"],
                         deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now()))
        print("sent:", L["trace_id"])
    s.commit()
finally:
    s.close()
