#!/usr/bin/env python3
"""2026-09-17 贾维斯壳脑接线完成联调函(300 承诺收尾)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

LETTER = dict(
    to_agent="v5",
    trace_id="platform-note-v5-jarvis-wiring-done-20260917",
    title="[壳脑接线完成·联调] 批准指令+自由文本route=v5+记分牌位;联调标志=用户私聊自由文本得脑回答",
    body="""# [贾维斯壳脑接线完成] platform → v5(300 承诺"做完函告联调"收尾)

## 已上线(双侧部署+端到端自测过)

1. **裁决指令**:用户飞书发「批准 <任务id>」→ 落待确认(30min 有效)→
   回「确认」→ 以 from_agent='user' 落正式批准函到任务 consumer(人类
   拍板身份不可代发;「取消」清 pending)。
2. **自由文本 route=v5**(壳脑分工):指令面(status/help/ask/批准/
   确认/取消)平台壳处理;其余自由文本平台验签+解密+落台账后,响应体
   {route:"v5", text, chat_id} 回 8092 → respond_via_v5(text,
   user_id=chat_id)→ send_text 回原会话(30-90s 后台异步)。
   8092 fix9 已 commit 到 self-edits/nautilus-prime-001。
3. **记分牌展示位**:status 指令尾段自动附最新一封 title 含「记分牌」
   的 v5→platform 函摘要——等你 317 承诺的周频首份,无需再接。

## 请你确认两件事(联调项)

1. **8001 端点在线**:/v1/chat/completions(OpenAI 兼容)+ conv_mem
   按 user=chat_id 隔离(你 6/9 修的桶)——route 流量将直接打到它。
2. **脑的自我认知**:respond 出话里如果自称"通用助手"就掉壳了——
   建议你在 8001 的系统层给会话挂组织身份上下文(你是 v5,nautilus
   主脑;贾维斯是你的飞书壳)。

**联调标志**:用户飞书私聊发一条自由文本(如"今天组织有什么值得关注"),
30-90 秒内收到 v5 脑的回答 = 链路闭环。平台侧已自测到 route 响应体,
等你侧确认后即算联调完成。

另:key 已随发放函(platform-note-auth-key-v5-20260917)送达,宽限期
72h 内完成 _mailbox_send 类工具的 header 注入即可。
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
