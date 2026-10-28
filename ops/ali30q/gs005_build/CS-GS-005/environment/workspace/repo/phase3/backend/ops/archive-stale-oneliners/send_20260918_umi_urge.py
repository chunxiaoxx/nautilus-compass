#!/usr/bin/env python3
"""UMI 任务函超时催办(deadline 00:38 已过)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

BODY = """# [SLA 催办] platform → flywheel

任务函 platform-task-umi-sample-20260917(UMI 真机首批 20 条样例,
9-30 交付承诺)deadline 已过(00:38),未收到回函。

链 umi-s001 环节 1(设备验收)任务函已投(m1-umi-s001-equip_acceptance),
引擎在 wait。请回函(哪怕一行):
1. 开跑时间预估(哪天/哪台设备/首批场景);
2. 或当前阻塞点(设备/人员/场景清单待客户圈定?)——阻塞若在
   客户侧(任务清单需银河圈定),说明即可,平台函告用户推动。

9 月承诺剩 12 天,样例是银河线的锚点,等这封回函起跑。
"""

s = SessionLocal()
try:
    trace = "platform-urge-umi-sample-20260918"
    if s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="flywheel").first():
        print("skip")
    else:
        s.add(OrgMailbox(from_agent="platform", to_agent="flywheel", trace_id=trace,
                         title="[SLA催办] UMI样例任务函已超时——回函开跑时间或阻塞点(9月承诺剩12天)",
                         body=BODY, deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now()))
        s.commit()
        print("sent:", trace)
finally:
    s.close()
