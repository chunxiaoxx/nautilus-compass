---
name: orgfuel-ORGD-e104f8e9cf231251-4369cace0c
description: "[### 召回引擎:BGE-m3 向量召回] - 引擎:compass daemon(本地 127.0.0.1:9876"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-e104f8e9cf231251
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 召回引擎:BGE-m3 向量召回] - 引擎:compass daemon(本地 127.0.0.1:9876 / 云端 v3.3,43.160.239.61),bge-m3 嵌入。
- 接线:UserPromptSubmit hook 每条 prompt 自动召回 top5 + 24h 内新记忆全列(当前心智优先)——本档写作时正被使用,即消费在飞实证。
- 分级:召回结果按 score 排序 + 沿链展开(被 top 条目引用的一跳邻居);🟢=新鲜(24h 内)、🔴=陈旧(提示时间戳,防旧账倒批今天判断)。
- 嵌入选型定谳(9/25 向量对拍):bge-m3 不换——Qwen3-0.6B recall@5 仅 +0.46pt(<阈值),中文切片现役反优 +2.75pt;MTEB 账面在自家分布不成立,只换不造原则。
