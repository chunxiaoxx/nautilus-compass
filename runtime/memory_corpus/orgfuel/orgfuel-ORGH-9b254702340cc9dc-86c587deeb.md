---
name: orgfuel-ORGH-9b254702340cc9dc-86c587deeb
description: "工具决策记录 delta_backfill.py delta_0004 回填生成器(2026-10-08 · 7B 语料"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9b254702340cc9dc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 delta_backfill.py
delta_0004 回填生成器(2026-10-08 · 7B 语料第二段)。

把仓内已成文的判定档案升格为结构化 delta registry 条目(棘轮式:交付即入册)。
每条 truth_label 均来自已有档案的定谳判定(可溯源坐标),本脚本只做 schema 组装
+content_hash+qid 防撞校验——不做任何新判定(判据零放宽)。

输入源(全部仓内正本):
  docs/metering/C_VERDICT_LEDGER_20261007.md      冲正台账
  docs/metering/A2_RECOMPUTE_VERDICT_20261007.md  A2 复算判定
  docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md E-NACRE-1 负结果
  docs/metering/PRECOR_BC_VERDICT_20261007.md     部署精度判定表
  docs/metering/PRECOR_JUDGE_ROBUST_20261006.md   预注册判据档
  runtime/loop/queue.md R301-R305/R347-R348       运维定谳案
输出:runtime/verdict_corpus/delta/delta_0004.jsonl(+manifest)
