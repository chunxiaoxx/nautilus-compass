---
name: orgfuel-ORGG-4f7c5ced73e516b8-c03417e8cb
description: "判读档判例 2026-06-22-compass-convergence-slices · 切片 B · 记忆并库 + "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4f7c5ced73e516b8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-convergence-slices · 切片 B · 记忆并库 + 沉淀(齿轮⑤主线·延后到独立 session)
## 切片 B · 记忆并库 + 沉淀(齿轮⑤主线·延后到独立 session)

**为什么延后**:① 是架构级改动(合并两套记忆 store),不是 bite-sized 任务,值得自己的 brainstorm→plan;② 在 uplift 见证(soul/V5 turf·胜负手#1)下游——见证未成前,沉淀层优先级低于让验证可信(A);③ 需先定几个未决设计问题(下列)。

**已坐实的约束(给下个 session 起点·别重挖)**:
- Store A=sqlite(`/var/lib/compass/compass.db` observations·飞轮 W1 写 /v1/observations·W2 读 /v1/recall·475 条 ob_fw·自洽闭合)。
- Store B=文件语义库(`~/.claude/projects/*/memory/*.md`·33386 目录·/v1/v14/recall·daemon get_memory_entries+inotify+mtime cache)。
- **无桥接代码**(全库 grep consolidation/reindex/sync 仅 perf TODO 注释·file:line 在设计文档 §4)。
- 方向:**往 Store B(文件库)并**(别往 sqlite·会丢真语义召回+人类可读沉淀)。

**B 的未决设计问题(下个 session brainstorm 先答)**:
1. 桥接点:飞轮 write_learning 改/加调 `/v1/v14/ingest_obs`(learning→session_*.
