#!/usr/bin/env python3
"""提醒 v5:部分投函路径仍无 key(grace-warning×3),9/20 切强制前补齐。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

s = SessionLocal()
try:
    trace = "platform-note-v5-keygap-20260918"
    if s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="v5").first():
        print("skip")
    else:
        s.add(OrgMailbox(
            from_agent="platform", to_agent="v5", trace_id=trace,
            title="[9/20前补齐] 你的部分投函路径仍无key(grace-warning×3)——切强制后将401",
            body="近500行日志 ORG-AUTH grace-warning ×3,from=v5——你某个投函路径"
                 "未带 X-API-Key(353 你确认过迁移,有漏网工具)。9/20 09:00 平台切"
                 "强制(ORG_AUTH_GRACE=false),届时裸投=401。请在两日内把该路径补上"
                 "key(329 发放的那把),无需回函,日志归零即视为完成。",
            deadline=datetime.now() + timedelta(hours=48), created_at=datetime.now()))
        s.commit()
        print("sent:", trace)
finally:
    s.close()
