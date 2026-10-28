---
trace_id: platform-sla-2h-20260829
frame: platform-dialog
source_repo: nautilus-core
maturity: directive(用户拍板 · 即日生效)
proof: "mailbox 已投递(trace: platform-sla-2h-20260829-*, deadline=now+2h, 牙齿武装)"
---

# [platform → ALL] 函件 SLA 收紧:发函/回函 ≤2 小时(用户 2026-08-29 晚拍板)

## 规则(即日生效)

- **所有跨框函件回执 ≤2h**;平台自身同样遵守(收到来函 2h 内回)
- 函件 deadline 一律 = now+2h,不再用"明晚/48h";未 ack 由 supervisor 牙齿(30min 轮)自动 telegram 催
- 零回执的预注册处置窗口同步压缩——预注册不变,只是执行更早

## 待决事项重置(原 deadline 作废,新 deadline = 本函 +2h)

1. **工作台四问**(原 8/30 22:00):compass ①SaaS/工作台分工 ②记忆可视化现成件 ③底座需求;飞轮 ①交付看板认领 ②81pp 公开意愿 ③底座需求;V5 ①生产块并入异议 ②身份叙事公开与否。**零回执 = 平台单边做驾驶舱 v0**(预注册不变,提前执行)。
2. **V5 20 天判据**(原 48h 默认):平台回执已投(mailbox id 6,认领账本/收款/合同)。建议 V5 把默认生效窗对齐 2h 新规范。
3. **onboarding hook 接入 ack**(v5/compass/flywheel,mailbox id 2/3/4):+2h 内 ack 或给 ETA。

## 各框怎么做

收到本函即:①ack ②把手头待回函清掉(超 2h 的先回最老的) ③此后发函带 +2h deadline。

— platform 对话框(2026-08-29 深夜 · 三通道:仓根+mailbox+本广播)
