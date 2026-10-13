---
name: orgfuel-ORGG-b4660bf5590f1009-a4f0d5d8e8
description: "判读档判例 2026-06-03-poi-central-ledger-implementation · Task 7:"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b4660bf5590f1009
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-implementation · Task 7: SQL 004 建表 + grant
## Task 7: SQL 004 建表 + grant

**Files:**
- Create: `sql/004_poi_credit.sql`
- Test: `tests/test_sql_004_applies.py`(用 sqlite 跑 schema 段,验证语法可建表)

**Step 1: 写失败测试** — 加载 `sql/004_poi_credit.sql` 里 `CREATE TABLE` 段在 sqlite 跑通(grant 段单独标记跳过 sqlite)。

**Step 2: 确认失败**

**Step 3: 实现**

```sql
-- sql/004_poi_credit.sql · PoI central credit table (Option C · MVP single-table)
-- Reference: docs/plans/2026-06-03-poi-central-ledger-design.md §4.1
CREATE TABLE IF NOT EXISTS compass.poi_credit (
    memory_key        text PRIMARY KEY,
    cumulative_impact double precision NOT NULL DEFAULT 0,
    event_count       int NOT NULL DEFAULT 0,
    last_impact_at    timestamptz
);
-- Phase 1: reuse existing writable account (th
