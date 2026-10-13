---
name: orgfuel-ORGG-fa2b2652ca2f1e78-ebd01e22ca
description: "判读档判例 2026-06-22-flywheel-convergence-design · 4. 关键坐标(实测坐实 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fa2b2652ca2f1e78
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-flywheel-convergence-design · 4. 关键坐标(实测坐实 · file:line)
## 4. 关键坐标(实测坐实 · file:line)
- 记忆双库:`/v1/recall`=sqlite(`compass_http_v09.py:804-849`·`/var/lib/compass/compass.db` observations)·`/v1/v14/recall`=文件索引(`daemon.py:568-620` get_memory_entries 扫 `~/.claude/projects/*/memory/*.md`)。**无桥接代码**(全库 grep consolidation/reindex/sync 仅 perf TODO 注释)。
- 飞轮 W1 写 `/v1/observations`(sqlite)·W2 读 `/v1/recall`(sqlite)= 飞轮在 sqlite 内自洽闭合;split-brain 是 sqlite ↔ 文件语义库两体系互不可见。
- capability_evolution:`phase3/backend/services/capability_evolution.py:103 async def record_task_outcome(agent_id整数,task_type,success,quality_score)`·已接 marketplace/survival/a2a。
- prime 注册:`agents` 表 `agent_id=9000002` Nautilus Prime 真钱包·kairos=9000003·v7=9000004。
- 飞轮拓扑:serving=cloud 43.160.239.61:8770(compass.ser
