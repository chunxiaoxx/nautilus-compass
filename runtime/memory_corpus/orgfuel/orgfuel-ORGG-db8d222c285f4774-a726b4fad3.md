---
name: orgfuel-ORGG-db8d222c285f4774-a726b4fad3
description: "判读档判例 2026-06-03-poi-central-ledger-design · 3. 决策汇总(brainst"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-db8d222c285f4774
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-design · 3. 决策汇总(brainstorming + 审查重裁)
## 3. 决策汇总(brainstorming + 审查重裁)

| # | 决策 | 说明 |
|---|---|---|
| 1 | `memory_key = project/filename` | 如 `C--Users-chunx/session_x.md`,防跨 project 短名碰撞 |
| 2 | **单表 MVP**(审查重裁) | 砍 ledger 明细 / recompute / distinct_consumers。boost 只读一个标量,明细已有两份(`poi_events.jsonl` + 云端 `agent_tool_calls`),L4「谁受益」可 join `agent_tool_calls` |
| 3 | 快照 cache | reconciler 现有 DB 连接顺手 `SELECT` 出 dict,~0ms boost,DB 挂了 daemon 照常跑 |
| 4 | 设计含两侧 · 实现分两期 | Phase 1 本地(不动 live)/ Phase 2 云端 daemon boost |
| 5 | **迁移砍**(审查重裁) | 从零累积(几天 reconcile 长回来);关键召回锚点可手动 INSERT 几行 |
| 6 | **写角色简化**(审查重裁) | Phase 1 复用现有连接加单表写权;Phase 2 再建 `poi_writer` 专用角色收紧 |

被否方案(记录避免重提):A 云端再跑一个 reconciler 写云端文件(治标,留 2-reconciler + 文件锁死债);B 每 daemon 一个信用 side-store(半步解耦)。
