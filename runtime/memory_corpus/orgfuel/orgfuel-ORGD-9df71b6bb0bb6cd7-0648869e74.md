---
name: orgfuel-ORGD-9df71b6bb0bb6cd7-0648869e74
description: "[## 预注册判据(跑完自检,全过才算完成)] | # | 判据 | 红灯处置(先证伪自己) | |---|---|--"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-9df71b6bb0bb6cd7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 预注册判据(跑完自检,全过才算完成)] | # | 判据 | 红灯处置(先证伪自己) |
|---|---|---|
| J1 | final_score.json 生成于本框仓 `runtime/vb_bench_20260927/` | 无产物=没跑完,不算任何分 |
| J2 | 30 模拟日跑满(seed42 不变) | 中途崩=照报崩溃点,禁改 seed 重跑凑数 |
| J3 | **工具执行>0**(v5 第四坑 899f2d1 修的零工具病;若 30 日零工具→先查 patch 链:API 探活/config 指向/版本,非 bench 有病) | grep 工具调用痕迹;API 18001 日志 |
| J4 | supplier 隔离生效(判分链独立于被测模型链路) | 查 BENCH_CONFIG/SUPPLIER_BASE_URL 实载值 |
| J5 | 分数照报:正负同权,失败解剖到机制级 | 负结果=照报+解剖,不许只报 day 数 |
