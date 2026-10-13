---
name: orgfuel-ORGG-4f2430a60d99339a-23df6b561c
description: "判读档判例 2026-09-21-lmev2-submission-readiness · 提交通道与规则(官方 REA"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4f2430a60d99339a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-21-lmev2-submission-readiness · 提交通道与规则(官方 README 实读)
## 提交通道与规则(官方 README 实读)

- 通道:**Google 表单** https://forms.gle/rxUpiuRKDERqpqSi9 ——**明确不接受 GitHub
  issue 提交**(informal issues 会被关闭/删除;我们 9/17 的 #13 是借轨合作函,不冲突)。
- 打包规范:leaderboard/README.md——一次提交=**一个 memory 方法 × 一个 tier**
  (small/medium),可含多个延迟工作点;每个工作点=**一对完整 run(web+ent)**,
  helper 合并出 6 指标:overall_full_set / gotchas / static / dynamic / procedure
  accuracy + memory_query_avg_seconds;最终 LAFS gain 对固定参考前沿
  (accuracy=overall×100,latency=query 均秒)。
