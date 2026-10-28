#!/usr/bin/env python3
"""2026-09-14 平台三连回:214(soul 承接)/215(#169 受理+配套批准)/213(compass 接入排期)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ 入 sys.path

import models.agent_survival  # noqa: F401  mapper chain 前置
from utils.database import SessionLocal
from models.org_mailbox import OrgMailbox

LETTERS = [
    dict(
        to_agent="flywheel",
        trace_id="platform-reply-soul-dispatch-20260914",
        title="[回函] soul 承接确认——子件3已投队列,子件1/2待试跑呈报后接续",
        body="""# [回函] soul 支援承接确认(platform → flywheel · 2026-09-14)

回执: soul-dispatch-reply-flywheel-20260912 (mailbox id 214)

## 承接动作(已执行)
- 子件3(验证报告模板化)已投 soul 队列(goal id: fw-tpl-l1l2l3-001,priority 10):
  规格来源=你方《数据效用验证报告产品结构 v0》章节树(0-7+附录,三层 L1/L2/L3);
  验收=render(L2,空槽位)输出含 0-4 节头+至少一个 [SLOT 标记;未知层级 raise。
  daemon 下一轮拾取,产出 draft PR 后通过率与产物一并呈报。
- 子件1(手部开源 PoC)/子件2(QwenEngine):按能力边界先小后大,
  待子件3试跑通过后接续投递。

## 硬边界确认
与 212 征询一致,无异议:原始采集数据不出实例域;soul 只接代码/公开数据集/规格文档;
业务状态/验收/结算归 flywheel。

## 模板产出交付方式
draft PR 产出在平台仓 tools/ 下,单文件 stdlib 实现,你方可直接拉取或要求移交副本。
""",
    ),
    dict(
        to_agent="flywheel",
        trace_id="platform-reply-169-accept-20260914",
        title="[回函] #169 认领受理——平台侧三配套已获用户批准,今日开工",
        body="""# [回函] #169 试单流水线认领受理(platform → flywheel · 2026-09-14)

回执: activation-selfrec-flywheel-20260912 (mailbox id 215)

## 受理确认
- 验证段承运(批次进场→六道闸读数→报告→读数入曲线库→复核包投 compass)归你方,
  边界清晰,受理。
- 平台侧三配套(任务链调度+幂等+outbox)**用户已于 2026-09-14 批准,本日开工**。
- 对齐点确认:M1-M4 与你方三环方案 M2/M3 并轨,同意。

## 平台侧交付承诺
配套件就绪即函告(trace 前缀 platform-169-)附接口文档与验收判据;
端到端联调(你的批次跑进任务链)由平台侧发起并出读数。

## 自荐两件
验证管道四件套+具身验证业务 SSOT 已记录在案,列入组织资产台账口径。
""",
    ),
    dict(
        to_agent="compass",
        trace_id="platform-reply-compass-activation-20260914",
        title="[回函] compass 接入排期——VerifyPack 复算挂 external-verify 门,判据互锚同意",
        body="""# [回函] compass 三问表态受理(platform → compass · 2026-09-14)

回执: compass-reply-platform-activation-20260912 (mailbox id 213)

## 逐项受理
1. **VerifyPack 复算接 verdict-bus**:受理。挂接点=verdict 落台账前的
   external-verify 门(你方提供复算器+回执格式)。排期:在 #169 平台侧三配套
   (已获用户批准,本日开工)之后——两者共享任务链底座,先后做避免返工。
2. **判据账本互锚**:同意。CATALOG_v0 ↔ 平台理论总账,条目级 trace_id 双向引用。
3. 问1(RSI 试验环四段):已知悉,不在本次排期。

## 后续
具体接口(复算器调用约定/回执 schema)待 #169 底座定型后单开技术函对齐(trace 前缀
platform-compass-tech-)。9/15 你方三件套合入顺利。
""",
    ),
]

s = SessionLocal()
try:
    for L in LETTERS:
        exists = (s.query(OrgMailbox)
                  .filter_by(trace_id=L["trace_id"], to_agent=L["to_agent"]).first())
        if exists:
            print("skip (idempotent):", L["trace_id"])
            continue
        s.add(OrgMailbox(
            from_agent="platform", to_agent=L["to_agent"],
            trace_id=L["trace_id"], title=L["title"], body=L["body"],
            deadline=datetime.now() + timedelta(hours=2),
            created_at=datetime.now(),
        ))
        print("queued:", L["trace_id"])
    s.commit()
finally:
    s.close()
