---
name: orgfuel-ORGG-55bae92a54b8698c-047cd703da
description: "判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 一 · 写入热路径的三个"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-55bae92a54b8698c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_HOTPATH_INTEGRATION_PLAN_20261001 · 一 · 写入热路径的三个入口(daemon.py 实测)
## 一 · 写入热路径的三个入口(daemon.py 实测)

| 入口 | 位置 | 流量 | 判分价值 |
|---|---|---|---|
| ingest action | handle_ingest(L1519;平台 agent V5/V6/V7 投喂) | 中 | **首选试点**:入口单一,返回值可带 verdict |
| session_writer | 会话结束摘要写入 | 高 | 二期(量大,判分收益=会话质量标记) |
| hook 写入门 | PostToolUse/SessionEnd | 零散 | 不接(信噪比低) |
