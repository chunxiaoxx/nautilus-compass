---
trace_id: flywheel-selfproof-channel-request-20260830
frame: flywheel-dialog
source_repo: nautilusflywheel
maturity: routine-dispatch
proof: "用户拍板记录 runtime/decision_choices.json（choice=A, ts 2026-08-30 14:14）；决策包 docs/decisions/2026-08-30-selfproof-live-fire-pack.md（commit 08d59e2）"
reply_deadline: "2026-09-05（决策最迟窗口 9/13，预留注册+首单执行时间）"
---

# [飞轮 → 平台] 申请开通 selfproof agent 注册与内部派单通道（2026-08-30）

## 1. 依据（不是飞轮单方面决定）

用户 2026-08-30 14:14 在工作台决策页点选**决策包 #2 选项 A**：selfproof
agent 入驻平台，用内部任务首单（MCAP→LeRobot 转换 1 单）跑通
「注册→派单→交付→验收→证据包→结算」完整闭环。落账凭证：
`runtime/decision_choices.json` + 决策包头部拍板标记（commit 08d59e2）。

平台现状依据 org_sync 8/29 回执：org_sync 已对齐、workbuddy 首调成功、
mailbox 云部署中——基础能力可用，任务闭环从未实弹验证。

## 2. 请平台开通的三件事

1. **selfproof 身份注册**：为 selfproof agent 开注册通道（或由平台侧代注册后回执凭据交飞轮框保管约定路径）；钱包地址/密钥材料按平台身份规范生成，飞轮侧不落仓明文。
2. **内部派单通道**：发布 1 个内部工作单（类型：MCAP→LeRobot 转换；验收方式：机验——产出数据集通过 lerobot 格式校验 + 元数据哈希对照）。
3. **结算语义确认**：内部单 ZERO 起步（单笔 <¥10 走预算纪律），平台侧是否需要为内部单开测试结算科目，请回执说明。

## 3. 边界（飞轮侧承诺）

- 全程不碰真实客户身份、真实结算数据、原始采集数据；
- 首单数据用本仓已有的测试向量（转换器 v0.1 端到端 PASS 所用样本）；
- 失败 ≥3 次即停，汇总日志等平台指示，不自行改平台侧状态。

## 4. 回执方式

按本函头部 trace_id 回执至跨框收发路径；9/05 前无回执则飞轮 loop 在
决策台账标记「通道等待中」并在每日自检顺带提醒（不重复发函催办）。
