---
name: orgfuel-ORGG-3c216b09c4c1279d-49bdfdafe8
description: "判读档判例 MEMX_FUSION_20261009 · 二、核心创新算子:因果倒置三向归因(站3,全新 glue) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-3c216b09c4c1279d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 MEMX_FUSION_20261009 · 二、核心创新算子:因果倒置三向归因(站3,全新 glue)
## 二、核心创新算子:因果倒置三向归因(站3,全新 glue)

每次判读 FAIL / drift 触发 / 判据未命中,反演根因并三分类:

| 归因 | 机制判据 | 产出动作 |
|---|---|---|
| **甲·记忆缺口** | recall 无相关命中(coverage=0) | 定向补写任务(该记的没记) |
| **乙·记忆错误** | 命中了但内容错/过期 | 该条 fact_status 降级+勘误修正写入(记忆版 errata,delta 通道已有) |
| **丙·检索失效** | 记忆在但没召回(embedding/改写问题) | 检索调优信号(入 E1 held-out 集) |

实现=一个归因脚本(输入:判读卡/漂移事件;动作:查 recall 日志+dedup 库+fact_status;输出:三分类任务清单)。**纯 glue,零训练,本周可实现**——它把每一次失败变成记忆系统的训练信号,这就是"自我催化"的化学本质:失败不再只是失败,而是定向喂养。
