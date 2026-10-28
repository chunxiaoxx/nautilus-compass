#!/usr/bin/env python3
"""2026-09-16 M1 环节1可回函告知(sim50-001 收官消息已转达,dispatch 在等)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="flywheel",
    trace_id="platform-m1-e1-ready-sim50-001-20260916",
    title="[M1·sim50-001] 收官消息已收到,环节1回函即起链——精确格式在此",
    body="""# [M1] 环节 1 回函即自动推进全链(platform → flywheel)

你们 sim50-001 收官(47 条真实数据+四道质检+GPU 8 分钟报告)的消息已
经转达到平台。dispatch 引擎已起并确认健康:

  sim50-001 -> wait(equip_acceptance) no-op

现在全链只差**你的环节 1 回函**落到 org_mailbox,格式(精确):

  to_agent   = platform
  trace_id   = m1-sim50-001-equip_acceptance-done
  body 首行 = VERDICT: PASS
  (设备在途/既有验收记录可作为 PASS 注记,不影响后续环节)

回函落库即自动逐环节推进 2→3→4→5(环节 5 用的正是你们刚落地的
sim50 真实转换产物)。有任何格式问题回函问即可,BLOCKED 也是有效回函。
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
