---
name: orgfuel-ORGG-fd31689d24d3d465-ccc7c39cf5
description: "判读档判例 _notes_rerank_wire · 风险 ## 风险 - **模型加载耗时**:bge-reranke"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fd31689d24d3d465
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_rerank_wire · 风险
## 风险
- **模型加载耗时**:bge-reranker-v2-m3 首次加载数十秒(与 embedder 同量级)。懒加载 → 仅开 flag 且首次 recall 时付出。
- **内存**:reranker ~2GB,与 bge-m3 叠加。生产开 flag 前确认 daemon 内存余量(云端曾有页抖动 OOM 史 · session 0603 G15)。
- **latency**:每 recall 多一次 cross-encoder predict(top-K 对)。top_k=5 时极小;若扩候选到 top-30/50 则按 benchmark 67min/500q ≈ 8s/q GPU,CPU 更慢 → 生产候选数需保守。
