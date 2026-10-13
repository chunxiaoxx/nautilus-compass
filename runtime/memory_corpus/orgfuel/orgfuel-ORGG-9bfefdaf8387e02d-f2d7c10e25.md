---
name: orgfuel-ORGG-9bfefdaf8387e02d-f2d7c10e25
description: "判读档判例 2026-09-21-lmev2-submission-readiness · 我方材料盘点 ## 我方材料"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9bfefdaf8387e02d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-21-lmev2-submission-readiness · 我方材料盘点
## 我方材料盘点

| 件 | 状态 | 坐标/缺口 |
|---|---|---|
| 成绩(d12 现役·d14 干净口径) | ✅ | web 40.0% / ent 38.4%(451 题全量;judge=doubao 协议披露在案) |
| 五分解 accuracy(gotchas/static/dynamic/procedure) | ⚠️ 部分 | d12 复盘有 static/dynamic 读数;gotchas/procedure 分解需从原始 run 重导 |
| per-query 延迟(memory_query_avg_seconds) | ❓ | tests/bench_profile.{sh,ps1} 可测;451 题原始 run 是否已带延迟记录待查 |
| 双域原始 run 文件(web+ent 各一对) | ❓ | GPU 机已退租;归档位置待查(本地/云;TRANSFER_RUNBOOK 有复跑命令) |
| tier | ✅ | small(451 题口径) |
| 方法名 | ⚠️ 待定 | 建议 nautilus-mem;与命名纪律一致(对外全名,勿撞 CompassBench) |
| 参考前沿 LAFS | ✅ | 官方 helper 计算(fixed reference frontier 随仓) |
