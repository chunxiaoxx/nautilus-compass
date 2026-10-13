---
name: orgfuel-ORGG-de29e4d769ccec27-10cd11419c
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · Component 1 · "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-de29e4d769ccec27
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · Component 1 · candidate emission(云端 gating)
## Component 1 · candidate emission(云端 gating)

`ops/patch_v14_recall_poi_candidate.py` — 幂等增量 patch:
- guard marker `_v14_emit_poi_candidate`,已 patch 则 skip
- **edit 1**:给 `v14_recall` 签名加 `agent_id: Optional[str] = None`(query 参数)
- **edit 2**:插入 inline helper `_v14_emit_poi_candidate(hits, query, agent_id)`
  - cache dir = `COMPASS_POI_CACHE_DIR` 默认 `/home/ubuntu/compass/.cache/poi`
  - 写 `poi_candidates.jsonl`,每 hit 一行,schema 同 `proof/poi_emitter`:`{ts, kind:"candidate", actor, memory, query_hash, rank, score}`
    - `actor` = agent_id or `"unknown"`;`memory` = `hit["path"]`(文件名);`query_hash` = `sha1(query)[:16]`
  - **云端跳过 self-cite 抑制**(memory 文件不在云端 · 无 frontmatter 可读 · 平台 agent 引用平台 memory 正是想
