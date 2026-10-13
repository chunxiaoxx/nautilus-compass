---
name: orgfuel-ORGG-0fec2a9b05fb9483-4143af6838
description: "判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 二 · S1 增量"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0fec2a9b05fb9483
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 二 · S1 增量收集(tools/p3_delta.py)
## 二 · S1 增量收集(tools/p3_delta.py)

- 输入:tools/verdict_corpus_exporter.py 全量重跑(幂等)与上一 anchor 的语料 manifest 对账。
- **label_origin 白名单门(反自报,承 judge 自报三陷阱)**:只收
  `independent_recompute` / `human_review` / `official_rule` / `three_vendor_final` 四类;
  `verdict-judge-*` 自标注一律拒收进 rejected 池并计数披露(判官自产标签=作弊通道,永久禁入)。
- 输出:runtime/verdict_corpus/delta/delta_NNNN.jsonl + manifest(计数/来源分布/rejected 计数/sha16)。
- 增量来源现状(2026-10-03 盘点):G1 三批 verdict + pusht 四窗 verdict(均为 compass 独立判,可归 independent_recompute)+ errata gold 活水 + unlabelled 47 待标——**尚未导出,首个 delta 待跑**。
