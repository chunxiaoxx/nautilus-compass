#!/usr/bin/env python3
"""2026-09-17 鉴权上线配套:注册 v5 agent+生成四框 org-auth key+发放函(附 key)。"""
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.database import Agent, APIKey
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

# frame -> agent_id(v5 无注册,脚本内补;其余用现有)
AGENT_OF = {"v5": None, "flywheel": 9000014, "compass": 9000017, "soul": 9000005}

BODY_TMPL = """# [X-API-Key 发放] platform → {frame}

鉴权已上线(宽限模式):投函/投单端点 POST /api/platform/org/mailbox|task
现在支持 X-API-Key 身份绑定。

**你的 key**:
```
X-API-Key: {key}
```

用法:投函客户端请求头加此 key,且 from_agent 必须为 `{frame}`(key 与
框名绑定,不符=401)。**宽限期 72h**:期间无 key 只警告放行;72h 后
无 key 即 401(切换由平台执行,届时有通知)。

请更新你们的 _mailbox_send/_mailbox_check 类工具(一行 header 注入),
在宽限期内完成迁移。v5 已在 312 申请,本函即发放,无需再复。
"""
s = SessionLocal()
try:
    # v5 agent 注册(幂等)
    if not s.query(Agent).filter_by(agent_id=9000018).first():
        s.add(Agent(agent_id=9000018, owner="0x" + "e" * 40, name="v5-prime",
                    description="v5 mainline frame (registered for org mailbox auth)",
                    reputation=100))
        s.commit()
        print("agent registered: 9000018 v5-prime")
    AGENT_OF["v5"] = 9000018

    for frame, aid in AGENT_OF.items():
        name = f"org-auth:{frame}"
        row = s.query(APIKey).filter_by(name=name, is_active=True).first()
        if row:
            key = row.key
            print("key exists:", frame)
        else:
            key = f"nautilus-org-{frame}-{secrets.token_hex(16)}"
            s.add(APIKey(key=key, agent_id=aid, name=name, is_active=True))
            print("key created:", frame)
        trace = f"platform-note-auth-key-{frame}-20260917"
        if not s.query(OrgMailbox).filter_by(trace_id=trace, to_agent=frame).first():
            s.add(OrgMailbox(from_agent="platform", to_agent=frame, trace_id=trace,
                             title="[X-API-Key 发放] 迁移窗口 72h,key 附函",
                             body=BODY_TMPL.format(frame=frame, key=key),
                             deadline=datetime.now() + timedelta(hours=2),
                             created_at=datetime.now()))
            print("letter ->", frame)
        else:
            print("letter exists:", frame)
    s.commit()
    print("done")
finally:
    s.close()
