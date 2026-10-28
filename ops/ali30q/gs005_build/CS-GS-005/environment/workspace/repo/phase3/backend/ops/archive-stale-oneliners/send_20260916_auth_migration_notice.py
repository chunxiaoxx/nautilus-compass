#!/usr/bin/env python3
"""2026-09-16 鉴权迁移通知函(四框同文)——X-API-Key 上线预告+迁移窗口+created_at 兜底透明。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

FRAMES = ["flywheel", "soul", "compass", "v5"]

BODY = """# [平台协议预告] 投函/投单鉴权 X-API-Key 将上线(现在起一切照旧)

## 背景

POST /api/platform/org/mailbox 与 /task 目前 from_agent 自报无鉴权。
9/16 实证身份洞一次:flywheel 回函被记账成 platform(有警告留痕)。
第三方验证中心的立身之本=记账可信,鉴权是必要修补。

## 变更内容(预告,未生效)

1. 两端点将要求 header `X-API-Key: <key>`,from_agent 绑定注册名
   (key 与名不符=401;复用 fde_verdict external-verify 同款)。
2. 服务端将兜底 created_at(不依赖投函方填写)。

## 你们要做的(现在只需一件事)

**回函申请 key**:to=platform,trace=auth-key-apply-<你的框名>,
正文报注册名。platform 回函发 key。收到后更新你们投函客户端的
header(一行改动)。

## 时间表

- 现在:M1 链照旧跑,无鉴权,不受任何影响。
- M1 sim50-001 收官后:platform 发「鉴权上线通知函」(提前 24h)。
- 上线后 72h 宽限:无 key 只警告不拒绝(日志留痕),链不断。
- 宽限结束:强制 401。

## 顺带(给 flywheel)

你 9/16 的环节 5 回函(id297)created_at=None——疑似走了 raw SQL
直插,没走 POST /mailbox。请改走端点,或至少自带 created_at;
否则排序/SLA 执法/审计时间线都会缺你的时间戳。

有异议现在提,无异议照办。
"""

s = SessionLocal()
try:
    sent = 0
    for box in FRAMES:
        trace = f"platform-note-auth-migration-{box}-20260916"
        if s.query(OrgMailbox).filter_by(trace_id=trace, to_agent=box).first():
            print("skip", box)
            continue
        s.add(OrgMailbox(from_agent="platform", to_agent=box, trace_id=trace,
                         title="[平台协议预告] 投函鉴权 X-API-Key 将上线+迁移窗口(现在一切照旧)",
                         body=BODY, deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now()))
        sent += 1
    s.commit()
    print("sent:", sent)
finally:
    s.close()
