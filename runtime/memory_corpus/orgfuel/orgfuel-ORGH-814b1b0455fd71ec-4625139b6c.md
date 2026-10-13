---
name: orgfuel-ORGH-814b1b0455fd71ec-4625139b6c
description: "commit dc170807bb53 2026-06-08 feat(fde): A 簇避坑语料语义检索(替裸 cat"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-814b1b0455fd71ec
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit dc170807bb53 2026-06-08
feat(fde): A 簇避坑语料语义检索(替裸 cat · RSI grounded-retrieval 热路径)
autolab_corpus_retrieve: bge-m3 dense + bge-reranker-v2-m3(daemon 同模型)按 producer
优化子目标 query 召回最相关避坑原子,替 producer round-2 grounded 臂的裸 cat。批次平衡
警示(correctness-first 元课)无条件保留,不受检索丢弃(metamemory 质量门)。

embed/rerank 后端注入 → CI compass-only 无模型无 LLM(5 TDD)。GPU 真模型验证(bge-m3
8.3s + reranker 2.7s 加载·150-540ms/query):reranker 纠正 dense 漏判(踢 correctness 漏
入·提升 prefetch)= dense 2/3 → rerank 3/3 相关@top3。grounding 输出=balance+top-k 子集
非全塞。turf:compass=检索+语料·V5=retrieve 调用+注入。
