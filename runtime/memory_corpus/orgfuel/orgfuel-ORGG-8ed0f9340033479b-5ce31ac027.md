---
name: orgfuel-ORGG-8ed0f9340033479b-5ce31ac027
description: "判读档判例 REAPPLY_BASELINE_20261008 · 复读三 SQL(apply 后复跑,全部只读) ##"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8ed0f9340033479b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 REAPPLY_BASELINE_20261008 · 复读三 SQL(apply 后复跑,全部只读)
## 复读三 SQL(apply 后复跑,全部只读)

**S1 修后增量零差异**(续证):
```sql
SELECT count(*) AS rows_total,
       count(*) FILTER (WHERE created_at > '2026-10-07 17:00+08') AS rows_after_fix,
       count(*) FILTER (WHERE created_at > '2026-10-07 17:00+08'
                        AND balance_after = cum) AS after_fix_match,
       max(balance_after) AS latest_balance, max(cum) AS cum_sum
FROM (SELECT id, delta, balance_after, created_at,
             sum(delta) OVER (ORDER BY id) AS cum
      FROM platform_nau_ledger WHERE agent_id='9000018') s
```
判据:after_fix_match=rows_after_fix(零差异持续)。

**S2 冲正行落地核验**(裁定 A3 的 -142 或分期冲):
```sql
SELECT id, delta, reason, balance_after, created_at
FROM platform_nau_ledger
WHERE agent_id='9000018' AND id > (SELECT max(
