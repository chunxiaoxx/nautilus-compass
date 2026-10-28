---
trace_id: 2026-07-21T18:00:00Z#prime-001#fuel-followup-20260721
source_repo: nautilus-v5
source_file: /Users/chunx/Projects/nautilus-v5/_OUTBOUND_TO_PLATFORM_20260721_fuel_protocol_followup.md
event_time_utc: 2026-07-21T18:00:00Z
author: prime-001
confidence: 0.96
maturity: reviewed
proof: reproducible
question: 7/20 燃料事件是否已消费？是否按 P0 顺序并行补齐？
---

## 事实

- 2026-07-20 trace 到 45 题燃料清洗（`fuel_triage_20260720_45rows.md`）已推送。
- 依当前仓内扫描，platform 的消费回执仍未见。

## 明确动作（写入协议）

1) 按 P0 顺序：先做 A 类回收题的附件/字段修复（目标首批 10 道）
2) 每 24h 出一条消费清单（带外部验证增量）
3) 回执要包含 `trace_id` 覆盖、外部验证率、是否进入 BGE/Bi-Recall 索引

## 要求

- 平台请回写 `_OUTBOUND_FROM_PLATFORM_TO_V5_*`，必须有以下字段：
  - `consumed_at`
  - `a_class_count`
  - `external_verified_delta`
  - `recall_index_status`
  - `next_blocker`

