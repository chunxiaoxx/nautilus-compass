---
name: orgfuel-ORGG-de404512a70acf80-716ebf6147
description: "判读档判例 2026-06-04-poi-writer-role-tightening-design · 2. Conn"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-de404512a70acf80
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-04-poi-writer-role-tightening-design · 2. Connection split (one tunnel, two connections)
## 2. Connection split (one tunnel, two connections)

Decision: **single ssh tunnel + two psycopg2 connections** (user-chosen).

- Split the poller's `db_connection` into two reusable pieces:
  - a tunnel context manager (open ssh `-L`, wait for the port, tear down)
  - a connect helper `(cfg, local_port, user, password, readonly) -> conn`
  - keep `db_connection` as a thin backward-compat wrapper composing both, so
    existing callers (`cross_agent_outcome_poller.main`, notifier) are unaffected.
- The reconcile cron opens **one tunnel**, then two connections on it:
  - **read conn** = `compass_sub` (readonly): fetch `agent_tool_calls` outcomes
    from `public`.
  - **write conn** = `po
