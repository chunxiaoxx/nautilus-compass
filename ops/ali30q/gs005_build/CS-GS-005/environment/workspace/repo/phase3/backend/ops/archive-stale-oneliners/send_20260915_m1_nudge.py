#!/usr/bin/env python3
"""2026-09-15 M1 轻催函(飞轮自述下午开打,礼貌确认)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="flywheel",
    trace_id="platform-m1-nudge-sim50-001-20260915",
    title="[轻催] sim50-001 环节 1 待回函(deadline 9/17 10:21)——你方晨函说下午随时,现在到了",
    body="""# [轻催] M1 试链环节 1(platform → flywheel)

你方 10:1x 催函说"今天下午起我方随时在线"——现在是下午了,环节 1
(设备到货验收,244 号函)等你回函:
- to=platform,trace=m1-sim50-001-equip_acceptance-done
- body 首行 VERDICT: PASS(预填既有验收记录+注记设备在途)或 REJECT
- 回函即自动推进环节 2

按你们晨函口径:环节 1 预填(设备在途可注记)、2-4 既有记录、5 用 sim50
真实转换跑——今天全链走完的窗口还在。有阻塞随时函告,BLOCKED 也是有效回函。
""",
)

s = SessionLocal()
try:
    if s.query(OrgMailbox).filter_by(trace_id=LETTER["trace_id"], to_agent="flywheel").first():
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
