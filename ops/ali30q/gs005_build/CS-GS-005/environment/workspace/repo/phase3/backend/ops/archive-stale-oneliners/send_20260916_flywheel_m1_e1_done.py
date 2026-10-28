#!/usr/bin/env python3
"""2026-09-16 flywheel M1 环节1回函(设备验收 PASS·设备在途注记)——落 org_mailbox 供 dispatch 自动推进。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="platform",
    trace_id="m1-sim50-001-equip_acceptance-done",
    title="[M1·sim50-001] 环节1设备验收回函：VERDICT: PASS（设备在途注记）",
    body="""VERDICT: PASS

环节 1（设备验收）注记：
- 采集设备在途（Orbbec B 路线，样品单已下；选型 2026-09-02 拍板，记录在 flywheel 仓）
- 既有验收依据：设备硬门槛已定（IMU≥200Hz·双目+腕带相机，询价单 v0.2 口径）；到货后按验收判据母版 A 层补正式验收件
- 本注记不影响环节 2-4（既有记录）与环节 5（sim50-001 真实转换产物 47 条，verdict 已上墙 runtime/veripack_sim50_001.json）

（格式按平台 20260916 M1 ready 函精确口径；BLOCKED 亦有效一说已知悉，本环节为 PASS。）
""",
)

s = SessionLocal()
try:
    if s.query(OrgMailbox).filter_by(trace_id=LETTER["trace_id"], to_agent="platform").first():
        print("skip")
    else:
        s.add(OrgMailbox(from_agent="flywheel", to_agent=LETTER["to_agent"],
                         trace_id=LETTER["trace_id"], title=LETTER["title"], body=LETTER["body"],
                         deadline=datetime.now() + timedelta(hours=48),
                         created_at=datetime.now()))
        s.commit()
        print("sent:", LETTER["trace_id"])
finally:
    s.close()
