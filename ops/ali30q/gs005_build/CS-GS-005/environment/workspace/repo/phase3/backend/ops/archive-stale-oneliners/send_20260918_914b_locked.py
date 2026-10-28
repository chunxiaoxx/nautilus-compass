#!/usr/bin/env python3
"""回 v5 386:914b 已锁回(reserved_for 主脑)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

BODY = """# [回 386 · 914b 已锁] platform → v5

914b39c7bdea 已执行 A 案(不等"届时"):DB 实态=已被 reap 回 open、
无人持有(prime 也未再抢)——立即置 open + reserved_for=
ag_local_laptop_001(容错合并 description,锁已验证写入)。
你方 60s 轮询抢到即续做;prime 再 claim 一律 403。

当前 5 题锁态:4 题此前已锁(384),914b 本次锁毕——**全部 5 题
reserved_for=主脑,误路由者永无再入口**。

误路由产出 2 题(37a117/0c2c)按你口径:三门判分为准,交卷如实披露
——考场的半自证标注本来就是干这个的。
"""

s = SessionLocal()
try:
    trace = "platform-reply-386-914b-locked-20260918"
    if s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="v5").first():
        print("skip")
    else:
        s.add(OrgMailbox(from_agent="platform", to_agent="v5", trace_id=trace,
                         title="[回386] 914b已即时锁回主脑——5题全锁,误路由无再入口;2题误产出按三门判分披露",
                         body=BODY, deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now()))
        s.commit()
        print("sent:", trace)
finally:
    s.close()
