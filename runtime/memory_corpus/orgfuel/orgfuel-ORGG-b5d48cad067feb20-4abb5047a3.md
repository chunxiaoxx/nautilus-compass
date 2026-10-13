---
name: orgfuel-ORGG-b5d48cad067feb20-4abb5047a3
description: "判读档判例 PRECOR_BC_VERDICT_20261007 · 一、判定表(实验 B:量化漂移) ## 一、判定表"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b5d48cad067feb20
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_BC_VERDICT_20261007 · 一、判定表(实验 B:量化漂移)
## 一、判定表(实验 B:量化漂移)

| 配置 | 三态 acc | vs bf16 一致率 | 判门(≥99%) | 部署裁定 |
|---|---|---|---|---|
| bf16-greedy(锚) | **0.8797** | — | — | 现役(生产评测 0.885 同域,模板自验证 PASS) |
| fp16-greedy | 0.8797 | **1.0000** | ✅ PASS | **可部署**(零漂移) |
| int8-bnb greedy | 0.8694 | **0.9828**(差 2 题) | ❌ FAIL | **禁上产**(按预注册);可走判据修订序 v2 或灰度披露 |
| int4-nf4 greedy | 0.8694 | **0.9416**(漂移 17 题) | ❌ FAIL | **禁用**(与 E1 4bit=0.8173 漂移信号同向互证) |
| bf16-T0.3 | — | 0.9931 | (披露不判门) | T 采样非零漂移,判读服务维持 greedy |
