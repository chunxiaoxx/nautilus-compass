---
name: orgfuel-ORGD-438a84665dee967b-2a0d09a179
description: "[### 修复一：fact_status 写入 gate（评估前移，最轻）] - 变更：memory frontmatt"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-438a84665dee967b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 修复一：fact_status 写入 gate（评估前移，最轻）] - 变更：memory frontmatter 增加字段 `fact_status: measured | inferred | heard`（实测过/推断/传闻）+可选 `verified_at`（上次实测日期）
- 纪律：写入方（Claude/用户）落条目时必填；recall 注入时随条目带出——高 stakes 决策（部署/对外/杀进程）只采信 measured 级
- 实施位置：记忆写入模板（全局 CLAUDE.md 记忆节+memory 文件约定）；daemon 侧注入格式（涉及 recall 输出模板，实施前先读 recall.py 确认注入拼装点）
- 验证：抽样 10 条新记忆检查字段存在+一次 high-stakes 提问只命中 measured
