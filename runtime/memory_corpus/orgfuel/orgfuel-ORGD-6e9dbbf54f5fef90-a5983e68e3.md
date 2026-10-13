---
name: orgfuel-ORGD-6e9dbbf54f5fef90-a5983e68e3
description: "[## 4. 验证(实测 · verification-before-completion)] - reranker e"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-6e9dbbf54f5fef90
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 4. 验证(实测 · verification-before-completion)] - reranker engage 确认:日志 `reranker loaded · BAAI/bge-reranker-v2-m3 on cuda · 6.9s` + GPU 占用 2.3G→**6.3G**(双模型)+ 候选顺序相对 dense-only 重排。
- **延迟实测**:首次 recall 冷启 75.8s(首查嵌入全部 966 文件)· 之后 dense warm 0.2-0.3s · **reranked warm ~4.2s/query**(reranker 跑 `COMPASS_RERANK_CANDIDATES=30` 个 cross-encoder pass)。
- ⚠️ 注:plan 估"T4 GPU ~0.6-0.9s"对应单次嵌入,非 30 候选全 rerank。30 候选 reranked ≈ 4s。若要降延迟,调小 `COMPASS_RERANK_CANDIDATES`。
