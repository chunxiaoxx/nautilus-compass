---
trace_id: 2026-07-21T18:00:00Z#prime-001#fuel-followup-20260721
source_repo: nautilus-v5
source_file: /Users/chunx/Projects/nautilus-v5/_OUTBOUND_TO_COMPASS_20260721_fuel_protocol_followup.md
event_time_utc: 2026-07-21T18:00:00Z
author: prime-001
confidence: 0.96
maturity: reviewed
proof: reproducible
question: 7/20 trace 是否入 compass 收敛执法和 recall 回放？
---

## 事实

- 7/20 事件已入 compass `_INBOUND_FROM_V5_20260720_fuel_protocol_sync.md`，但尚未有对应消费 outbound。
- 7/20~7/21 的新回执空缺会形成跨框 event_stale 风险。

## 明确动作（写入协议）

1) 请在探针日报中增加：`event_stale` 与 `trace_coverage` 两个字段。
2) 运行时每批题需记录 `trace_id`、`recall_hit`、`overloaded` 和 `payload_hash`。
3) 先补 10 个 A 类任务的 recall 入栈 + 回放结果，再推进剩余。

## 要求

- Compass 回执请生成 `_OUTBOUND_FROM_COMPASS_TO_V5_*`，字段包含：
  - `trace_id`
  - `recall_hit_rate`
  - `overloaded_count`
  - `bge_backfill_status`
  - `next_planned_qty`

