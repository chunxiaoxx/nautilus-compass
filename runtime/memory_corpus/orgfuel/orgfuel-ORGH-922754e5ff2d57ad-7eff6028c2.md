---
name: orgfuel-ORGH-922754e5ff2d57ad-7eff6028c2
description: "工具决策记录 verdict_to_samples.py 判例→训练样本转换器(P3 燃料瓶颈机制化解)。  背景:de"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-922754e5ff2d57ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 verdict_to_samples.py
判例→训练样本转换器(P3 燃料瓶颈机制化解)。

背景:delta_0001 手写导出只产 14 条/案,200 门槛=14 案件日——判分产出与语料
沉淀之间缺机制。本转换器把任意 verdict JSON 的 findings/verdict 自动映射为
训练样本,投递 delta/inbox/ 交 p3_delta.py 白名单门吸收。

映射规则(判例→样本,一判读多样本):
  · 每个 finding(带 evidence_tier+upgrade_path)→ 1 条样本:
      artifact=finding 全文+basis;truth_label 按证据层映射
      (measured 且判定成立→pass;inferred/unverifiable→insufficient_evidence;
       被否证的 claim 类 finding→fail,由 --fail-keywords 识别)
  · verdict 总判定 → 1 条样本(PARTIAL/PASS→pass,U→insufficient_evidence)
标签纪律:转换器**不产生 fail 假阳性**——只把明确被否证的推断标 fail,
其余一律 pass 或 U;拿不准=U(宁欠勿毒,承 judge 自报三陷阱)。

用法:python tools/verdict_to_samples.py <verdict.json> [--judge <judge名>] [--dry]
输出:runtime/verdict_corpus/delta/inbox/v2s_<stem>.jsonl(交白名单门)
