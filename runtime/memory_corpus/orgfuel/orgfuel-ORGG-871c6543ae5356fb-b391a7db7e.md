---
name: orgfuel-ORGG-871c6543ae5356fb-b391a7db7e
description: "判读档判例 2026-09-22-assay-head-charter · 三 · 架构(承 NanoJev 配方,改造"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-871c6543ae5356fb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-assay-head-charter · 三 · 架构(承 NanoJev 配方,改造点)
## 三 · 架构(承 NanoJev 配方,改造点)

| 组件 | NanoJev | Assay-Head 改造 |
|---|---|---|
| 底座 | Qwen3-0.6B | 同(或同家族最新小底座) |
| 训练目标 | RLCD(校准决策强化) | 同+**成本加权**(错放一个 disagree 比错放一个 agree 贵——门代价不对称) |
| 输出空间 | Noul/Choice/Score | **Choice(三态)+ Score(gate_fail_type 置信度)+ Noul(can_judge?)**——第四输出:模型自判「这题我能不能判」,低置信时主动弃判(→人工),这是 NC 态的架构化实现 |
| 输入格式 | state+questions | (starter, diff, tests) 三元组 token 序列;diff 用 hunk 标记对齐 |
