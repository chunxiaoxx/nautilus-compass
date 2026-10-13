---
name: orgfuel-ORGG-00efcaafba2859df-61240fdd3d
description: "判读档判例 _notes_rerank_wire · 降级写法(沿用 BM25 模式 daemon.py:695-697"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-00efcaafba2859df
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 _notes_rerank_wire · 降级写法(沿用 BM25 模式 daemon.py:695-697)
## 降级写法(沿用 BM25 模式 daemon.py:695-697)
reranker 加载/predict 抛异常 → `log(...)` + fallback 退原 `top`(dense/fused 序),不 crash recall。
进程内单例懒加载(参 `get_embedder()` @ `daemon.py:335` 的 eager-singleton 思路,但 reranker 用 lazy 因默认关)。
