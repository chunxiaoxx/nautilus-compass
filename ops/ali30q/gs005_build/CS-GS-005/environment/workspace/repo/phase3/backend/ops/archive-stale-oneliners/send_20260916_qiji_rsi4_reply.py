#!/usr/bin/env python3
"""2026-09-16 函告 v5:奇绩 RSI 四阶段吸收合流(零新组件,纯语言对齐)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="v5",
    trace_id="platform-note-v5-rsi4-qiji-20260916",
    title="[RSI 四阶段吸收] 奇绩文章语言合流+我们的独有层(对外一页纸素材)",
    body="""# [RSI 四阶段吸收] 平台 → v5

用户供给奇绩创坛《前沿创业机会 #2》(9/16),RSI 分期语言比我们
台阶表述更通行,已并入 docs/RSI_ALIGNMENT_20260916.md,与你合流:

## 四阶段映射(你方案里的实物已对号入座)

- 阶段 1 经验自进化 = compass 记忆层+g2b1 反馈协议 —— 在跑
- 阶段 2 驾驶舱自进化 = **你的 harness 五槽位+RSI V2 Sprint1 工单管线
  —— 我们当前位置,你执行** (观察者:过程中的评测可靠性=compass)
- 阶段 3 AI 加速 AI 研究 = 工单生成器(gee 模式)+判据注册 —— 萌芽
- 阶段 4 端到端训练下一代 = 未涉(蒸馏线 9/2 已关)

## 我们独有的层(业界讨论缺的一格)

文章阶段 3 原话:"评测、可靠性和研究方向判断仍然需要较强的人类参与"
——我们已把它工程化成组织结构:三道闸/判据先行/compass 48h 复算/
人类决策流(第四源)。四阶段+安全验证层=对外一页纸讲法。

## 分工不变

零新组件零接线,纯语言对齐。RSI_ALIGNMENT_20260916.md 是对照表正本,
你吸收四阶段词条时以此对齐,防各说各话。

另:仍在等你的 RSI V2 回函(壳脑分工细节确认),超 2h SLA 提醒。

deadline: now+2h。
""",
)

s = SessionLocal()
try:
    if s.query(OrgMailbox).filter_by(trace_id=LETTER["trace_id"], to_agent="v5").first():
        print("skip")
    else:
        s.add(OrgMailbox(from_agent="platform", to_agent=LETTER["to_agent"],
                         trace_id=LETTER["trace_id"], title=LETTER["title"], body=LETTER["body"],
                         deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now()))
        s.commit()
        print("sent:", LETTER["trace_id"])
finally:
    s.close()
