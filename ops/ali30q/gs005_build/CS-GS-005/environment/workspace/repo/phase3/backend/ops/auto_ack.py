# -*- coding: utf-8 -*-
"""通报类函自动 ack(断奶第二刀,U13 · 2026-09-25)。

规则:title 前缀命中通报类 → 置 ack_at+ack_note;其余一律不动(人/会话处理)。
幂等:只处理 ack_at IS NULL。留痕:systemd journal(每轮一行 matched 数)。
被 systemd timer 每 15min 调用(nautilus-org-autoack.timer)。
"""
import sys
from datetime import datetime

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
import models.agent_survival  # noqa: F401 mapper
from utils.database import SessionLocal
from sqlalchemy import text

# 白名单:纯通报类(无请办/无 deadline 义务),协议 V1§3 明确互不逐复
PREFIXES = (
    "[loop-diff", "[worker审计]", "[worker 审计]", "[进展同步]",
    "[loop-diff]",
)
# 明信片函(复活阶段三·U27 9/27 用户批):人格层通讯,收讫即归档,无 SLA 语义
POSTCARD_PREFIX = "[kind:postcard"


def run() -> int:
    s = SessionLocal()
    now = datetime.now()
    n = 0
    for p in PREFIXES:
        r = s.execute(
            text("UPDATE org_mailbox SET ack_at=:t, ack_note=:note "
                 "WHERE ack_at IS NULL AND title LIKE :pre"),
            {"t": now, "note": "通报类自动ack(断奶第二刀 auto_ack.py,9/25)", "pre": p + "%"})
        n += r.rowcount
    r = s.execute(
        text("UPDATE org_mailbox SET ack_at=:t, ack_note=:note "
             "WHERE ack_at IS NULL AND title LIKE :pre"),
        {"t": now, "note": "postcard 收讫(人格层通讯·无SLA)", "pre": POSTCARD_PREFIX + "%"})
    n += r.rowcount
    s.commit()
    s.close()
    return n


if __name__ == "__main__":
    matched = run()
    print(f"auto_ack matched={matched} at {datetime.now():%F %T}")
