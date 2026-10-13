---
name: orgfuel-ORGG-abc74d5e4f64e7ec-7efdf8d017
description: "判读档判例 INFISTAR_GATEWAY_METERING_PLAN_20260930 · 三、执行参数 ## 三、"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-abc74d5e4f64e7ec
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 INFISTAR_GATEWAY_METERING_PLAN_20260930 · 三、执行参数
## 三、执行参数

- **频率**:每日 3 轮(10:00/16:00/21:00 北京),每轮每模型 10 请求
- **30 天累计**:每模型 ~900 请求,5-10 模型,总 4.5k-9k 请求
- **对照腿**:同 probe 集打官方直连(现役 key:zhipu/MiniMax/ARK/TypeSafe 覆盖到的模型);无官方 key 的模型,指纹判定退化为「与该模型公开文档/已知行为特征比对」并标注 U(不可核)
- **调度**:Windows 计划任务调 `tools/infistar_meter.py`;轮内值守监控缺轮
- **落盘**:`runtime/infistar_meter/raw_YYYYMMDD_HH.jsonl`(原始)+`daily_YYYYMMDD.json`(日汇总);原始日志不改写,勘误走追加
