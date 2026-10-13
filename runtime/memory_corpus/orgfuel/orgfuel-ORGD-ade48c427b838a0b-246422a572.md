---
name: orgfuel-ORGD-ade48c427b838a0b-246422a572
description: "[### 4.4 检索对打的实验设置(逐字段)] - **同题**:LongMemEval-S 全 500 题,按 qu"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-ade48c427b838a0b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 4.4 检索对打的实验设置(逐字段)] - **同题**:LongMemEval-S 全 500 题,按 question_id join;
- **同判据**:retrieval-only 双方(不涉 reader/judge);mem0 侧 `infer=False`(纯检索模式,不开 LLM 提炼);
- **各用默认嵌入**:compass 用 bge-m3,mem0 复现用 vertexai text-embedding-005——比的是两个系统开箱即用的检索层,不替对方换嵌入;
- **版本钉死**:mem0ai 2.0.19(8/27 pip 核对为 PyPI 最新;hosted 闭源版另注);
- **复现成本**:CPU 可跑(smoke)/ GPU 推荐(全 500 题),一条命令(`scripts/reproduce_lmes_retrieval.sh`)。
