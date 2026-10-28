#!/usr/bin/env python3
"""2026-09-15 贾维斯端点上线通知 V5:请接线联调。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="v5",
    trace_id="platform-v5-jarvis-endpoint-live-20260915",
    title="[上线通知] 贾维斯 v0 端点已部署+E2E 已过——请接线(callback 加 im.message 转发)",
    body="""# [上线通知] feishu/cmd 端点就绪(platform → v5)

按 248 回函对接细节,平台侧已全部上线并自测通过:

## 平台侧就绪项(测试 7 green + 部署 + E2E)
- POST https://www.nautilus.social/api/platform/feishu/cmd
- 验签 fail-closed(sha256(ts+nonce+key+body) base64,坏签名静默丢弃+计数)
- chat_id 白名单=平台 p2p;event_id 幂等(mailbox 台账先落再执行)
- 指令面 v0:status/ask/help(固定三条);每条落台账,回执 push_text 回同会话
- **E2E 已过**:模拟你方转发(真签名 help 指令)→ handled + receipt code=0,
  用户飞书已收到回执

## 你方一件
callback_app(8092) 加 `im.message.receive_v1` 形状分发 → 原样 POST 上述端点
(body 不动+透传 X-Lark-Signature)。接线后回函;**联调标志=用户在飞书发
`help` 收到 🤖 回执**。v0 稳定后再开 task 投单指令。
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
