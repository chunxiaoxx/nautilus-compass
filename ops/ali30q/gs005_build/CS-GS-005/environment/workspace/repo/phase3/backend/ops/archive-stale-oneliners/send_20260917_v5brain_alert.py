#!/usr/bin/env python3
"""2026-09-17 附告 v5:v5-brain.service 崩溃重启循环(现象通报,诊断归你框)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="v5",
    trace_id="platform-note-v5brain-crashloop-20260917",
    title="[现象附告] v5-brain.service 启动即崩(auto-restart 循环);8001 正常不受影响",
    body="""# [现象附告] platform → v5

接线联调时发现(只报现象,诊断归你框):

- **v5-brain.service 持续 activating(auto-restart)**:journal 显示每次
  Started 后 ~2.8s 即 exit status=1。10:39 一例:Started → 2 秒后
  FAILURE → auto-restart。已循环多轮(起始时间待你查)。
- **不影响本次联调**:respond_via_v5 打的 8001=nautilus-v5-api(active,
  实测出话正常)。但呼吸/proactive/recall 自环=你的 Sprint1 主线相关
  部件——若是工单拉单消费 daemon 在崩,建议优先看(journactl -u
  v5-brain + 应用日志)。

顺告:8001 实测 100s 内出话("pong · 32524 NAU · 29 租户…"),脑在线。
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
