---
name: orgfuel-ORGD-4331d8e49b7d89b1-0bc885eee7
description: "[## 一、公式与三件产品的映射] | 公式项 | 架构实现 | 现役实物(坐标) | |---|---|---| | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-4331d8e49b7d89b1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一、公式与三件产品的映射] | 公式项 | 架构实现 | 现役实物(坐标) |
|---|---|---|
| **压缩** | agent 记忆系统:经验→结构化记忆→向量召回→沿链可信传递 | compass daemon(9876,BGE-m3,98 条记忆)/记忆门三件套(fact_status/dedup_check/沿链一跳,daemon 仓已实现) |
| **验证** | 判分机构:预注册判据+非实现者复算+证据三层标注+判例装订 | compass 判分(12 案判例集)/assay v2 schema(PyPI 3.3.0)/jev-curate 协议/判官 LoRA(J1-J7 三门全绿 88.51%) |
| **因果倒置** | 验证结果反向改模型:errata→delta→训练→回归门→上岗,评测数据飞轮驱动模型进化 | P3 动态权重六段管道(delta ledger)/P2v2 冠军 Qwen3-1.7B QLoRA/J8 热路径装载申报(3037) |
