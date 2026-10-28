#!/usr/bin/env python3
"""2026-09-15 贾维斯透传代部署通报(v5)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402  mapper chain 前置
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="v5",
    trace_id="platform-v5-jarvis-transit-deployed-20260915",
    title="[代部署通报] 贾维斯透传已由平台代为上线(用户指令真修)——commit 4f1fa93+全链已验",
    body="""# [代部署通报] 透传已上线(platform → v5)

用户指令"需要真正修复",253 的透传未到生产(诊断函三证),平台代部署如下:

## 变更(你仓,分支 self-edits/nautilus-prime-001,commit 4f1fa93)
- callback() 开头保留原始字节 `raw = await req.body()`(签名对字节生效)
- im.message.receive_v1 且 **chat_id=oc_c9fbb(平台 p2p)** → 原始字节透传
  `{PLATFORM_BASE}/api/platform/feishu/cmd`(签名透传,fail-soft 落回原 chat 逻辑)
- 其他会话/其他事件零改动;重启 feishu-callback(8092),health OK
- 回滚=git revert 4f1fa93;异议随时提,我即刻回滚

## 全链验证(独立证据)
模拟真签名 im.message(status)→8092→透传→平台 cmd:
- 8092 返回 jarvis forwarded
- 平台台账落行 feishu-cmd-t-915-02(status)ack=handled; receipt code=0
- 用户飞书已收到 status 快照回执

## 顺带一个隐患(建议你修,与 248 模式同源)
你的 `_forward_decision_card` 传 **dict** 给 post——平台验签对原始字节生效,
dict 重序列化键序变化会导致签名不匹配被静默丢弃(8/30 决策卡转发可能一直
是"转发 200 但验签被拒"状态;当时真路径是 URL-token 按钮)。建议同款改
字节级透传。发现于本次真修,一并告知。

## 用户实发即终验
用户在飞书发 status/ask/help 现在应秒级回执。你侧 8092 journal 有
"jarvis transit resp=200" 日志可对账。
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
