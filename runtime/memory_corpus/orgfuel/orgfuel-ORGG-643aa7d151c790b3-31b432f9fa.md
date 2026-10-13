---
name: orgfuel-ORGG-643aa7d151c790b3-31b432f9fa
description: "判读档判例 _notes_rerank_wire · 生产 recall 路径(daemon.py) ## 生产 rec"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-643aa7d151c790b3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_rerank_wire · 生产 recall 路径(daemon.py)
## 生产 recall 路径(daemon.py)
- `handle_request(req)` @ `daemon.py:610` —— 唯一生产 recall 入口(TCP/MCP 都走它)。
- recall 分支 `daemon.py:667-719`:
  1. `all_entries` 跨 mem_dir union(`:669-675`)。
  2. dense cosine 打分 → `scored` 降序(`:676-682`)。
  3. **可选 BM25+vec RRF fusion**(`COMPASS_USE_BM25_RRF=1`,`:684-697`)→ 得 `top`;否则 `top = scored[:top_k]`(`:699`)。
  4. 构建 `result["recall"]`(`:701-707`)。
