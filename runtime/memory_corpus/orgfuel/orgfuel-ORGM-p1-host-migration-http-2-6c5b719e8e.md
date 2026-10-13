---
name: orgfuel-ORGM-p1-host-migration-http-2-6c5b719e8e
description: "--- name: p1-host-migration-http-20260906 description: P1 宿主"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-p1-host-migration-http-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: p1-host-migration-http-20260906
description: P1 宿主迁移 HTTP 直连 9/6 启动——4 dialog token 全绿·hr/fde 已切·platform/compass 被内部工具卡住·隧道 9/15 硬停
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-06T03:37:32.074Z
---

P1 旧入口退役(9/15)宿主迁移 9/6 执行记录:

**验证结论(全部实测)**:
- 4 个宿主 dialog token(hr/compass/platform/fde)HTTP 直连 `https://compass.nautilus.social/mcp/` recall 全绿(HTTP 200)
- **行为等价**:TCP 桥(scope=user)与 HTTP(注入持有者)两侧都命中同一空间 `C--Users-chunx`——4 宿主共享空间是现状固有,迁移不引入混仓
- HTTP 面 tools/list=8 自助工具(drift_check/drift_history/feedback_log/ingest_obs/profile/recall/session_search/thread_recall);历史用量(工具漂移日志)只有 proof_of_impact×3 超出面外
- 协议配方:POST /mcp/ + `Authorization: Bearer cmp_…` + `Accept: application/json, text/event-stream`,JSON-
