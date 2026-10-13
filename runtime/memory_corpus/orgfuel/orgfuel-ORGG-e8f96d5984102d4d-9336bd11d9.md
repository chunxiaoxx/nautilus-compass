---
name: orgfuel-ORGG-e8f96d5984102d4d-9336bd11d9
description: "判读档判例 PRECOR_ENACRE1_20261007 · 一、设计 ## 一、设计  - **数据**:verdi"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e8f96d5984102d4d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_ENACRE1_20261007 · 一、设计
## 一、设计

- **数据**:verdict 语料(去重 1453)按 artifact domain 分片;取样本量前 3 的域为 D1/D2/D3,其余并入 D-rest。分片清单与计数随档冻结(sha16)。
- **臂**:
  - A(现役基线):单一大 LoRA(best_lora,dbcbab6fd1ff5821)判全部 291 题(bf16-greedy)——直接复用 PRECOR B/C 已有读数(acc=0.8797)不重跑;
  - B(路由片):每域片 Di 用"该域 train 切片(合并锚回放 10-15%)”训练域 LoRA(底座同 Qwen3-1.7B,r=16 同 champion);推理按 domain 路由挂载(vLLM `--lora-modules` 多片);
- **对照公平性**:A 与 B 见过的训练数据量对齐(B 各域片训练量=对应域 train 计数,总 token 量差 <20% 披露);
- **评测集**:各域 test/dev 切片(训练前冻结),qid 全局防泄漏。
