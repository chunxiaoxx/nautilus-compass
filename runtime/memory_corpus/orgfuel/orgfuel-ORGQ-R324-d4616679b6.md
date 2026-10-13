---
name: orgfuel-ORGQ-R324-d4616679b6
description: "### R324 · 2026-10-08(主件轮:rsi-bench 25 题回归集 v0 构建✅) - **回归集构"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R324
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R324 · 2026-10-08(主件轮:rsi-bench 25 题回归集 v0 构建✅)
- **回归集构建器+首跑✅[实测]**:tools/rsi_regression_build.py(B 臂题级 result.json 全量扫描)→**21 行回归集**(21 唯一任务,选入规则=patch 非空且未 resolved=格式回归域;expectation=修复后同题 reapply 应过或以内容性失败而非格式);**A 臂 15 格式题级在 v5 归因简报坐标,v0 只收 B 臂实物,PR 前补齐**(如实标注)。
- 交付路径:rsi-bench#4 承诺件(25 题回归集+rubric follow-up PR)——v0 21 题+构建器可重跑,A 臂补齐后随 PR 发(10/12 开业后窗)。
