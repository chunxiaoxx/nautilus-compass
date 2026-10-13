---
name: orgfuel-ORGH-d3344eb5870b2272-e9eb65469c
description: "工具决策记录 eightb_trigger_split.py 触发日合并池导出+held-out 切分(SEVENB_C"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d3344eb5870b2272
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 eightb_trigger_split.py
触发日合并池导出+held-out 切分(SEVENB_COMPARE_PREREG 零现场清单 步2)。

池=corpus_pipeline 的 merged 全量(与 manifest sha16 同构复算);
标签口径如实申报:org_fuel 系条目 truth_label=judge_verdict(NACRE 1.7B 自判,
自举标注——局限进 report G4 披露);三 split 系条目=原始 truth_label 不动。
切分:held-out 300(SEED 20261005,均匀抽),train=余量;qid 防泄漏审计落 report。
