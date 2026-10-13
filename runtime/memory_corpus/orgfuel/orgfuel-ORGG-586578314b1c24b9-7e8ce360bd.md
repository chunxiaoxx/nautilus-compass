---
name: orgfuel-ORGG-586578314b1c24b9-7e8ce360bd
description: "判读档判例 _notes_rerank_wire · reranker 注入点 ## reranker 注入点 **`t"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-586578314b1c24b9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_rerank_wire · reranker 注入点
## reranker 注入点
**`top` 定好之后(line 699 之后)、构建 `result["recall"]`(line 701)之前。**
这样 reranker 同时覆盖 vec-only 和 RRF-fused 两条路径,且只对最终 top-K 重排(latency 可控)。

注意:reranker 跨编码器对 top-K 重排,要看「完整候选文本」效果最好。BM25 用 `e.get("embed_text","")`,reranker 应同源用 `embed_text`(非仅 `description`)。
若要让 reranker 看更多候选再砍到 top_k,可对 `scored[:RERANK_CANDIDATES]`(如 top-30/50)重排后取 top_k —— 与 benchmark `TOP_K_RETRIEVE=50` 一致。本期先对已得 `top` 重排(最小改动),候选扩展留 1.4 benchmark 验证时按分数决定。
