---
name: orgfuel-ORGD-343c7fa81b1d204f-f713f32d08
description: "[## Component 1 · candidate emission(云端 gating)] - guard mar"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-343c7fa81b1d204f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## Component 1 · candidate emission(云端 gating)] - guard marker `_v14_emit_poi_candidate`,已 patch 则 skip
- **edit 1**:给 `v14_recall` 签名加 `agent_id: Optional[str] = None`(query 参数)
- **edit 2**:插入 inline helper `_v14_emit_poi_candidate(hits, query, agent_id)`
- cache dir = `COMPASS_POI_CACHE_DIR` 默认 `/home/ubuntu/compass/.cache/poi`
- 写 `poi_candidates.jsonl`,每 hit 一行,schema 同 `proof/poi_emitter`:`{ts, kind:"candidate", actor, memory, query_hash, rank, score}`
- `actor` = agent_id or `"unknown"`;`memory` = `hit["path"]`(文件名);`query_hash` = `sha1(query)[:16]`
- **云端跳过 self-cite 抑制**(memory 文件不在云端 · 无 frontmatter 可读 · 平台 agent 引用平台 memory 正是想 credit 的)
- try/except 包裹 · 永不破坏 recall · `COMPASS_NO_POI_CANDIDATE=1` 可关
- **edit 3**:在 `v14_recall` 成功 return 前插 emit 调用,仅 `hits` 非空时 fire
