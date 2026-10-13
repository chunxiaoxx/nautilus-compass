---
name: orgfuel-ORGD-6597ed97ccdc98c5-723d371f04
description: "[## 判据(四条,冻结不改)] | # | 判据 | 通过线 | 测法 | |---|---|---|---| | J"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-6597ed97ccdc98c5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 判据(四条,冻结不改)] | # | 判据 | 通过线 | 测法 |
|---|---|---|---|
| J1 | **fact_status 覆盖** | 落档后新写入的 memory 100% 带 `fact_status: measured\|inferred\|heard` | 扫描脚本对 mem 目录全量 frontmatter 检查;基线日(9/9)前旧条目不计入 |
| J2 | **查重零误合并** | 对照组(构造的无关条目对)0 次被判 merge;实验组(cosine≥0.9 对)100% 被判 merge | `dedup_check` 单测+一次真库抽样(≥20 条)人工复核 |
| J3 | **沿链一跳** | 命中含 `[[name]]` 引用的条目时,被引条目 100% 出现在 `chain_extra`;无链查询 chain_extra 恒空;recall P95 ≤ 基线 ×1.2 | 构造 A→B 对;延迟取 /status 滑窗+50 次冒烟计时 |
| J4 | **全局回归门** | 冻结三条 fact 查询的目标条目 hit@3 不低于改动前基线;e2e 现役口径不重跑时以三 fact 门+冒烟为准 | `ops/regression_gate.py`(改前跑=基线,改后跑=对照) |
