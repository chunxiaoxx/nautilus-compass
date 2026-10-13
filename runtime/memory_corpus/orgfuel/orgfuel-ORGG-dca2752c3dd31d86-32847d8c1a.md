---
name: orgfuel-ORGG-dca2752c3dd31d86-32847d8c1a
description: "判读档判例 2026-06-03-poi-central-ledger-implementation · Task 8:"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-dca2752c3dd31d86
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-implementation · Task 8: cron 接线 — UPSERT + 快照导出(连接复用)
## Task 8: cron 接线 — UPSERT + 快照导出(连接复用)

把 `reconcile_central` 接进 `ops/poi_reconcile_cron.py`:复用现有 DB 连接(读 outcome 那条),settle 后 `fetch_all_credits` → `write_snapshot_atomic`。

**Files:**
- Modify: `ops/poi_reconcile_cron.py`
- Test: `tests/test_poi_reconcile_cron_wire.py`(mock DB 连接 + tmp 快照,验证流程:load candidates → reconcile_central → 导快照文件存在且含 settle 的 key)

**Step 1: 写失败测试** — 用 sqlite 连接 + 假 candidates/outcomes 跑 cron 的 `run_once(conn, ...)` 入口,断言快照文件落地且 boost 能读。

**Step 2-4:** 实现 `run_once`:`load_candidates` → `load_settled` → `reconcile_central(conn=...)` → `save_settled` → `fetch_all_credits` → `write_snapshot_atomic(snapshot_path, credits)`。snapshot_path 默认 `DEFAULT_CACHE_DIR / "poi_credit_ca
