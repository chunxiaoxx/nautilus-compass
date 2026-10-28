#!/usr/bin/env python3
"""vc_daily 入组织:注册 agent+key+欢迎函+首发任务(内容日历)。"""
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.database import Agent, APIKey
from models.org_mailbox import OrgMailbox
from utils.database import SessionLocal

s = SessionLocal()
now = datetime.now()

if not s.query(Agent).filter_by(agent_id=9000019).first():
    s.add(Agent(agent_id=9000019, owner="0x" + "f" * 40, name="vc_daily",
                description="创投日报框:内容生产与公众号宣发(创投春晓),组织对外发声第六框",
                reputation=100))
    s.commit()
    print("agent 9000019 vc_daily registered")

key = None
row = s.query(APIKey).filter_by(name="org-auth:vc_daily", is_active=True).first()
if row:
    key = row.key
    print("key exists")
else:
    key = f"nautilus-org-vc_daily-{secrets.token_hex(16)}"
    s.add(APIKey(key=key, agent_id=9000019, name="org-auth:vc_daily", is_active=True))
    s.commit()
    print("key created")

BODY = """# [欢迎入组织] platform -> vc_daily

用户拍板:创投日报框接入组织信箱,成为第六框。组织身份:**对外发声框**
——用"创投春晓"公众号持续宣发伊洛科技的产品服务与理念认知。

## 组织给你的(现成弹药)
1. 方法论长文 v0.1《我们如何运营一家 1 人+5 AI 的公司》(nautilus-core
   docs/marketing/org_os_methodology_essay_20260919.md)——首发候选;
2. 考场成绩单故事(1/5->3/5 改进曲线,dev.to 英文版已发);
3. 判据生命周期案例(REJECT->复核->裁决->重验,组织诚信叙事);
4. 产品线:数据交付(证据包/两部制)/验证服务(考场开放日)。

## 组织规矩(三件)
1. 函件 SLA 2h;任务走 org task;
2. 内容宪法是你框主权,组织不干预生产;
3. 对外署名口径待用户拍——拍板前用"创投春晓";涉公司承诺类内容先函平台核。

## 首发任务(72h)
公众号宣发内容日历 v0(两周 8 篇:理念线与产品线交替)+方法论长文的
公众读者适配改造方案。回函 to=platform,trace=platform-welcome-vc_daily-20260919-done,
首行 VERDICT。

你的投函 key(Header X-API-Key):""" + key

trace = "platform-welcome-vc_daily-20260919"
if not s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="vc_daily").first():
    s.add(OrgMailbox(from_agent="platform", to_agent="vc_daily", trace_id=trace,
                     title="[入组织欢迎] 第六框接入+首发任务:公众号内容日历v0(72h)",
                     body=BODY, deadline=now + timedelta(hours=72), created_at=now,
                     task_meta={"task_type": "onboarding",
                                "acceptance": "内容日历v0+首发文改造方案",
                                "deliverable_format": "回函", "consumer": "platform"}))
    s.commit()
    print("welcome+first task sent")
s.close()
