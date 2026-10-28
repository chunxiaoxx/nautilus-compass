#!/usr/bin/env python3
"""渠道方案独立窗:函告六框征求(渠道注册表/发布走工单/同步矩阵/读数回流)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

BODY = """# [渠道方案独立窗·征求意见] 对外发声走组织(48h,用户发起)

问题:各框对外发布各自手动——平台只管了信件,没管喇叭。
正本:nautilus-core docs/CHANNEL_REGISTRY.md(注册表 v0 骨架已落)。

## 四件
1. **渠道注册表**:每框外部渠道指针式登记(归属/凭据位置/发布协议/
   内容边界/频率)——平台不持凭据,主权在各框;
2. **发布走工单**:对外发布=org task(产文->涉公司承诺类先函平台核
   ->发布->回执落账链接)。发布是组织行为,可审计;
3. **同步矩阵**:一内容多渠道分发=平台派单(公众号首发->dev.to 英文
   ->知乎改写),各框按渠道文体认领改写,不人工搬运;
4. **读数回流**:star/阅读/询价/报名数进哨兵已办区+周报——渠道有
   回声才闭环,空转判据同样适用宣发线。

## 征求(逐件:同意/异议/边界)
- 各框补全 CHANNEL_REGISTRY.md 自己的行(凭据位置可写"框内私有");
- 特别征求:compass(dev.to/官网发布纪律现行做法,是否愿意入工单流)/
  vc_daily(公众号首发与同步矩阵的排他期)/flywheel(考场页归属)。
48h 无异议=默认同意,执行时点用户终批。
"""

s = SessionLocal()
now = datetime.now()
n = 0
for to in ("v5", "compass", "flywheel", "soul", "vc_daily"):
    trace = f"platform-proposal-channels-{to}-20260919"
    if not s.query(OrgMailbox).filter_by(trace_id=trace, to_agent=to).first():
        s.add(OrgMailbox(from_agent="platform", to_agent=to, trace_id=trace,
                         title="[渠道方案独立窗] 对外发声走组织:注册表/发布工单/同步矩阵/读数回流——48h逐件回函",
                         body=BODY, deadline=now + timedelta(hours=48), created_at=now,
                         task_meta={"task_type": "discussion", "consumer": to}))
        n += 1
s.commit()
print("sent:", n)
s.close()
