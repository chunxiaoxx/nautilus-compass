---
name: orgfuel-ORGH-9af2769f28d5f597-3bcad26c5a
description: "commit a0219251e500 2026-05-07 v2 跑分 final · EverMemBench 41"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9af2769f28d5f597
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a0219251e500 2026-05-07
v2 跑分 final · EverMemBench 41.0% → 44.4% · compass 超过全部 4 个 paper Table 4 baseline
T4 v2 driver final · 5 topic × 100 题 · n=500 · 5.58h · ~$25 LLM API:
  topic 01: 44.0%   topic 02: 46.0%   topic 03: 42.0%
  topic 04: 45.0%   topic 05: 45.0%
  OVERALL: 44.4% · recall@30 97.6% · CV 4%

新位置 (paper Table 4):
  MemoBase 34.27 < Mem0 37.09 < Zep 39.97 < MemOS 42.55 < compass 44.40

更新 (10 处):
  · paper §0 abstract · §6.5 表 + caption + narrative
  · CHANGELOG (highlights 段 v2 数 + 新位置)
  · paper/zh/{README,paper2_zh}.md
  · paper/promo/{wechat_long_post,x_thread_zh,x_thread_en,hackernews}.md
  · paper §6.5 cross-ref sec:drift → app:drift (修 1 dangling reference)

paper2_main.pdf · 440K · 24+ 页 · 0 undefined citation/reference
