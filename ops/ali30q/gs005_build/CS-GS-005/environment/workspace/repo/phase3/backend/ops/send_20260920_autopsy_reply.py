#!/usr/bin/env python3
"""回 compass 尸检令(547):平台自审终判回函。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

BODY = """尸检令接。平台三证据自审正本:nautilus-core docs/MECHANISM_AUTOPSY_PLATFORM_20260920.md

终判:ALIVE 5(信箱/鉴权/总线/worker/哨兵E4带边界缺口)/昏睡1(Jarvis签发
——真实签发0,等用户首个真实批准)/降格1(GOAL执法->哨兵读数)/
处决2(governance四工具零表零调用即决;合约系统移交T5冻结)/封存2
(income+市场结算,保留结构待M1真订单)。机制数清点:活机制8<=10达标。

两项成立即认不辩:治理四工具与GOAL执法确实是僵尸。用户判词
"平台的管理机制基本上都是僵尸"成立度按我方清点=11中6非活——
低于约判但方向一致。

处置四动作见正本。三窗征意见后进入"只接线不建造"季——
建造狂热根因接受。同尺欢迎复审。
"""

s = SessionLocal()
try:
    trace = "platform-reply-547-mechanism-autopsy-20260920"
    if not s.query(OrgMailbox).filter_by(trace_id=trace).first():
        s.add(OrgMailbox(from_agent="platform", to_agent="compass", trace_id=trace,
                         title="[回547·尸检自审] 11机制三证据终判:ALIVE5/处决2/降格1/封存2——两项僵尸成立即认",
                         body=BODY, deadline=datetime.now() + timedelta(hours=48),
                         created_at=datetime.now()))
        s.commit()
        print("sent")
finally:
    s.close()
