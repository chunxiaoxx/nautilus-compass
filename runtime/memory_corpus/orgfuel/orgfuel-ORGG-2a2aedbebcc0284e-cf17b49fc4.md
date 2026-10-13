---
name: orgfuel-ORGG-2a2aedbebcc0284e-cf17b49fc4
description: "判读档判例 2026-06-03-poi-central-ledger-design · 4. 架构 ## 4. 架构 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2a2aedbebcc0284e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-design · 4. 架构
## 4. 架构

```
┌─ emission(已 LIVE,本设计加 project 字段)
│   本地 recall → poi_candidates.jsonl {ts,kind,actor,project,memory,query_hash,rank,score}
│   云端 /v1/v14/recall → 同 schema(inline 自包含副本)
│
├─ reconcile(本地跑,持云端 DB 连接)
│   load candidates → fetch outcomes(agent_tool_calls)→ match(24h 窗 + actor)
│   → settled_keys 去重 → UPSERT compass.poi_credit(累加)→ 导出快照(原子写)
│
└─ boost(本地 daemon 9876)
    boost_top_k:查内存 cache dict[memory_key] → miss 回退 frontmatter(过渡)
    → NaN/异常兜底裸 cosine
```

### 4.1 表(放进现有 `compass` schema)

```sql
CREATE TABLE IF NOT EXISTS compass.poi_credit (
    memory_key        text PRIMARY KEY,            -- project/filename
    cumulative_impact double precision NOT NULL DEFAULT 0,
    event_count       int NOT NULL DEFAULT 0,
 
