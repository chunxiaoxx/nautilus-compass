---
name: orgfuel-ORGD-846f344f678663fb-2eb9576ea2
description: "[## 一、学界业界最新 vs 我们的资产(对照表)] | 外部发现 | 对照内部 | 判读 | |---|---|--"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-846f344f678663fb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一、学界业界最新 vs 我们的资产(对照表)] | 外部发现 | 对照内部 | 判读 |
|---|---|---|
| **研究空白**:无单篇覆盖"量化×小判分×鲁棒性"(SLM-as-judge survey 亦称小判分鲁棒性研究不足) | PRECOR B/C 判定表(fp16 1.0/int8 98.28/int4 94.16,291 题) | **我们已站在空白上——可首发** |
| 量化行为变化已有预注册研究(LessWrong 2026-08) | PRECOR 同方法论 | 方法论互证,引用之 |
| 离散判据平局率高(1-5 制 88/100 tie)→学界转向连续 logprob 打分 | PRECOR-C 软维度门(相邻档) | **方法学直接吸收**:软维度改连续分数口径 |
| RIPD rubric 偏好漂移攻击(promptfoo):自然语言 rubric 可被操纵 | 判读安全(判据注入防御空白) | **新安全项**:判据修订序 v2 加漂移注入测试 |
| Claw-SWE-Bench(2606.12344):通用 harness 评测基准 | caliber-bench(测评测本身可信) | 同赛道进入者,定位互补:它们测效率,我们测可信——白皮书引用作"赛道被验证"证据 |
| 行业口径:"SWE-bench 不宜作采购唯一依据" | 我们 Round1 污染 caveat 同款口径 | 行业向我们的方向走,对外文案可引 |
| Replay buffer:混 5-20% 旧样本关闭 60-80% 遗忘差距 | P3 delta 训练(33/200) | **训练配方直接吸收**:delta 批次混 10-15% 锚定集(split_train 抽样) |
| MemRL(2026-02):冻结 LLM+情景记忆非参数自进
