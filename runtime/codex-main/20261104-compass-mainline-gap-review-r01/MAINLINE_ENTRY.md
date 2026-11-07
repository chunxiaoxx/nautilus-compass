# Compass 主线恢复入口

2026-11-04 增量梳理。任务 `COMPASS-MAINLINE-GAP-REVIEW-20261104-R01`，负责人为 Compass 原会话。原历史入口继续保留，本页连接本轮新增证据。[原历史总结](/Users/chunxiao.wang/Projects/nautilus-compass/docs/soul/COMPASS_PAST_PRESENT_FUTURE_20261103.md)

## 用通俗的话说

Compass 要把组织过去做过的事保存下来，让后来的 agent 找到正确经验，知道哪些说法已被纠正，再用证据检验它是否真的帮任务做得更好。assay/JEV 承接验证与反馈。专属小模型和创新架构继续沿已有理论研究。[本轮详细梳理](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/codex-main/20261104-compass-mainline-gap-review-r01/REPORT.md)

## 现在的位置

- [实测] 已有原始历史、索引、检索代码、assay/JEV 实物和本机小样本实验。旧端口事实题保留 0/3→3/3，也保留检索命中后仍答错的负结果。
- [实测] M4 独立审计发现了遗漏撤销条件、固定旧节点挤掉新证据等问题。r04 后续通过 48 组有判据的单进程工程检查，另有 3 组接口观察。时间、权威与撤销语义及真实任务收益仍待验。
- [实测] D2 存档已有 22 份摘要。另有 21 份部分锚点检查，13 份低于 95%，有效锚点合计 794/855≈92.87%，逐会话平均 92.22%。这是部分存档统计，语义质量和最终验收尚待完成。
- [方向已定] 统一为本机 Compass MCP，自用内网直连，外部按 token 访问。已有历史调用与源文件读回证据，当前各消费者完整接入、统一数据映射和组织记忆恢复程度仍待逐项确认。[证据与版本](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/codex-main/20261104-compass-mainline-gap-review-r01/EVIDENCE.json)

## 近期三项工作

| 优先 | 负责人角色 | 依赖 | 可核验完成条件 |
|---|---|---|---|
| 1. 明确统一入口实际承接了什么 | Compass 维护角色，消费者侧负责人读回 | 现有命名空间、原始来源清单、运行版本证据 | 每个实际消费者有入口→命名空间→原源的独立读回，列明历史覆盖缺口与权限边界，保存版本和时间 |
| 2. 完成本机压缩试点的质量定谳 | 压缩试点执行角色，非实现者复核 | 已有 D1/D2 产物与 J1–J6 正本 | 解释 46/50 选样偏差，完整报告质量、压缩成本和失败项，分列有效锚点、语义幻觉、关键条件保留与预过滤口径，得到可复算结论 |
| 3. 验证真实工作中的帮助 | Compass 评测角色，真实任务消费者提供终态 | 稳定入口、可回读证据、新冻结任务和外部可核 gold | 固定模型、harness、预算和序列化，分别测覆盖、检索、证据保真、回答/弃答和任务终态，完成有记忆/无记忆对照及独立复算 |

这些是后续工作划分。当前交付为有界审查结果，业务执行状态仍归原负责人。

## 分阶段推进

入口与资产承接 → 压缩和证据质量达标 → 消费者真实任务收益 → 由已验证反馈支持专属小模型与架构实验。架构实验继续核对已有 C/V 口径、数据冻结、M1 复盘和资源前置，保留纯相似度对照、失败判据与负结果。[路线与边界](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/codex-main/20261104-compass-mainline-gap-review-r01/REPORT.md)

## 恢复工作时先读

先读本页，再按具体问题进入 REPORT、EVIDENCE 或原试点。全部新增文件位于本目录。独立审核题在读回后归入开发可见集合。历史执行指令按当时范围解释。当前未发现需要用户重新选择架构的事项。[交接与停止点](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/codex-main/20261104-compass-mainline-gap-review-r01/HANDOFF.md)
