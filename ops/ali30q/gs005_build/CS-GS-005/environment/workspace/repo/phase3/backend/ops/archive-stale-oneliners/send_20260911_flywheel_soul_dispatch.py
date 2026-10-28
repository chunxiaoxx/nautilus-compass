#!/usr/bin/env python3
"""2026-09-11 平台→飞轮:soul 支援数据管线建设的征询函(用户拍板起草)。"""
import os
from datetime import datetime, timedelta

import models.agent_survival  # noqa: F401  mapper chain 前置
from utils.database import SessionLocal
from models.org_mailbox import OrgMailbox

BODY = """# [征询函] soul 支援数据管线建设——请提供可拆单子件(平台 → 飞轮)

## 背景
平台 soul 链已激活并修复完毕(提交→gate→draft PR 全链路,PR#140 实证),现 pause 待派单。
用户提出:让平台算力支援你框目标中的数据管线/数据高精度标注建设。
用户并提示:**多数环节已有开源实现**——工作重心在选型+集成+胶水层,而非从零造轮。

## 分工边界(平台理解,请纠正)
- 判断层归你框:环节拆解/开源选型/数据协议设计/标注一致性判据/验收标准
- 实现层可派 soul:单文件、验收明确、边界小的子件——典型如:
  1. 格式转换函数(某开源工具输出 ↔ 你框 schema 的 adapter)
  2. 数据校验/清洗规则脚本(规则由你定,soul 实现)
  3. 标注 QC 抽检/对账 join 脚本(对账规约你框出)
  4. 管线环节间的调用胶水(单文件 wrapper)
- soul 能力边界(实测):单文件小改动可过 gate;多文件/跨表/架构级任务连败。
  连续 2 次同错即停手转人工,不会硬撑烧 token。

## 请你框回复(任选其一即可)
A. 回"有"并附 3 个单文件子任务(每条含:目标文件/验收标准/相关开源件名)——
   平台即投 goals.yaml 恢复 soul 试跑一轮,通过率与产出呈报;
B. 回"暂无"——soul 继续待命,此事挂起,主线节奏不受影响。

## 已就绪的配套(无需新建)
- MCP 8 工具(A2A 收发/health/bounties)你框可随时接入;
- tasks 结算台账已活(verdict→tasks 接线 9/10 验收),若后续走 bounty 模式可直接挂。

deadline 2h,platform_loop 自动执法。回函投 mailbox(to_agent=platform,
trace 含本函 trace 前缀)。
"""

s = SessionLocal()
try:
    s.add(OrgMailbox(
        from_agent="platform", to_agent="flywheel",
        trace_id="platform-flywheel-soul-dispatch-inquiry-20260911",
        title="[征询函] soul 支援数据管线建设——请提供可拆单子件(分工边界+能力边界在内)",
        body=BODY,
        deadline=datetime.now() + timedelta(hours=2),
        created_at=datetime.now(),
    ))
    s.commit()
    print("letter inserted, deadline now+2h")
finally:
    s.close()
