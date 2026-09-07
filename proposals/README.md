# proposals/ · 组织自改进提案池（RSI MVP）

> 2026-09-07 建。对应 FLYWHEEL 仓 2026-09-07 征询函（组织 RSI MVP）。定位：三段式自改进循环（提案-冻结-验收）的提案池，最小实现——平地目录，governance 工具族接线待 COMPASS 回函（若迁移，迁移本身就是一条提案，用循环自己批准）。

## 流程（每周五 30 分钟"自改进时段"）

1. 汇总本周摩擦点（feedback_log + 各框提报）→ agent 排序 → 人点 top 3
2. agent 补全提案（出 patch 分支+跑测试）→ 状态 tested
3. 绿灯提案 → 飞书决策卡发用户 → pending_approval
4. 批准 → agent 合并 commit+更新规则+沉淀 compass 记忆 → deployed

## 状态机

draft（已立意，patch 未出）→ tested（验证绿）→ pending_approval（已发卡）→ approved（人批）/ rejected（人否）→ deployed（合并生效）。月底复盘：只认真结算的人时。

## L 分权（防 reward hacking 硬闸）

| 级别 | 范围 | 审批 |
|---|---|---|
| L1 | 工具/脚本（不改行为语义） | 可批量抽查批 |
| L2 | 规则（CLAUDE.md/hook/流程/本 README） | 逐条批 |
| L3 | 考官（测试/宪法/评估标准/判据协议/governance.lock） | 逐条批+24h 冻结期 |

agent 修改 agent 权限配置的提案一律按 L3 处理（分权表漏项的默认兜底）。

## KPI 口径

只认结算型：实际省的人时（预估值仅记录不计数）。跨框归属：谁的环境里省的记谁的，争议条目人裁决（防互相刷）。

## 首批提案（2026-09-07 冷启动）

- P-0001 SSH 启动器脚本模板化（L1）
- P-0002 fail 残骸自动清理挂 watchdog（L1）
- P-0003 watchdog 日志每日汇总卡（L2）
