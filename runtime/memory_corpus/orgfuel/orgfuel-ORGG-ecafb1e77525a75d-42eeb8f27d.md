---
name: orgfuel-ORGG-ecafb1e77525a75d-42eeb8f27d
description: "判读档判例 2026-09-02-summary-layer-preregistration · 三、预注册判据(A/B"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ecafb1e77525a75d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-02-summary-layer-preregistration · 三、预注册判据(A/B)
## 三、预注册判据(A/B)

### 3.1 实验设计

- **B 臂(基线)= 8/29 全量 evidence,不重跑**:同判据(subject=doubao-seed-2-0-pro-260215 / judge=glm-5.3-flash / 同 retrieval 配置),500 题分型数字即为基线。
- **A 臂(摘要层)= 只跑三短板型 322 题**(ms 133 + tr 133 + ssa 56),ZMM_SUMMARY_LAYER=1,其余 env 与 8/29 全量一致。
- 高分三型不跑不比(未改动,理论字节不变;全量时顺带回归验证)。

### 3.2 三态判定(跑分前锁定)

| 判定 | 条件 | 处置 |
|---|---|---|
| **PASS** | ms ≥ 35%(锚 22.6)且 ssa ≥ 40%(锚 25.0)且 tr ≥ 30%(锚 15.8)三型全达 | 上 500 全量(ssu/ssp/ku 顺带回归,不回退门 ≤1pt) |
| **PARTIAL** | ≥2 型达标且其余型不低于锚 | 只在达标型路由,上全量 |
| **FAIL** | ≥2 型未达标 | 摘要层设计错,回炉查摘要质量(抽 20 张卡人工验),**不加大剂量不换参数硬调** |

n 说明:ms/tr n=133、ssa n=56,±5pt 内视为平(二项 CI);门都设在 +12pt 以上,远超噪声带。

### 3.3 计算资源(待用户拍板)

- 选项 1:本地跑(API 调用 + 本地 bge-m3 CPU 检索,估 2-4h embed + 322×~2min ≈ 11h 墙钟,零成本)
- 选项 2
