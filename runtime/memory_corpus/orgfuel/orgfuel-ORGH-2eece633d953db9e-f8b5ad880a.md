---
name: orgfuel-ORGH-2eece633d953db9e-f8b5ad880a
description: "工具决策记录 corpus_pipeline.py corpus_pipeline.py · 判例→判分器语料管道 (A"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2eece633d953db9e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 corpus_pipeline.py
corpus_pipeline.py · 判例→判分器语料管道 (A 件, 2026-10-06 · R270)

合并 verdict_corpus 三 split + delta/*.jsonl(+ 未来判例集导出件),按 qid 去重分组防泄漏,
产 SFT 就绪清单+manifest(sha16+计数)。触发器:train 计数每 +500 打印 RETRAIN-CANDIDATE
(判据:PRECOR 修订版或 P2v2 同门复用);7B 对拍触发=train≥3000(用户 10/6 拍)。

用法: python tools/corpus_pipeline.py [--root runtime/verdict_corpus]
只读输入,写 manifest_corpus_pipeline.json 于 root 目录。幂等。
