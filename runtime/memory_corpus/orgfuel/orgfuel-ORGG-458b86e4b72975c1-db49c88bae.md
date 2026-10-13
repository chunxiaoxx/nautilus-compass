---
name: orgfuel-ORGG-458b86e4b72975c1-db49c88bae
description: "判读档判例 ORG_PRECEDENT_FUEL_V0_20261007 · 二、机制设计(v0:采集→抽取→判定→入册"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-458b86e4b72975c1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 ORG_PRECEDENT_FUEL_V0_20261007 · 二、机制设计(v0:采集→抽取→判定→入册,四段全自动化)
## 二、机制设计(v0:采集→抽取→判定→入册,四段全自动化)

```
[采集] 五框会话日志/queue.md/信箱函件/勘误账/审计发现/值守记录
   ↓ 采集器(仿 v5 轨迹采集器,采集"判断-结果"事件而非原始文本)
[抽取] 结构化候选判例:{情境, 判断/动作, 结果, 结果来源(阻抗等级 L0-L3)}
   ↓ 规则+judge 初筛
[判定] 现役 NACRE judge 三态判:该"判断-结果"对是否构成有效判例(对/错/不可验)
   ↓ 证据三层强制(实测/推断/不可验)+qid 防泄漏+dedup(七算子审计教训:写必有 gate)
[入册] 过门者进 delta registry(fuel_eligible)→ corpus_pipeline 计数器自动+1 → 触发器链
```
