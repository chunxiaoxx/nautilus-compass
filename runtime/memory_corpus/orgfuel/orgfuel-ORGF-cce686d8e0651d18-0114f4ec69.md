---
name: orgfuel-ORGF-cce686d8e0651d18-0114f4ec69
description: "flywheel 档案 2026-10-06-fuel四验判读SLA-v1.md # fuel 四验+判读服务 SLA "
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-cce686d8e0651d18
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-10-06-fuel四验判读SLA-v1.md
# fuel 四验+判读服务 SLA v1

> 承 #5728 产品化五件判据自盘(SENT 5734)补齐件 · 2026-10-05 起生效
> 服务对象:v5 交付臂/平台调度;通道:org mailbox(trace 寻址)

## 时限三档

| 环节 | SLA | 起算 |
|---|---|---|
| 四验门机判(gates 结果) | **12h** | 交付函到件时 |
| 判读打分(下放环节) | **24h** | 四验 PASS 确认时 |
| 回执(含 409 双确认) | **48h** | 任意来函 |

## 响应规则

- 函面带死线(deadline 字段)的,按死线优先于上表
- 超时即发延时说明函(原因+新时限),不静默超时
- 批量到件(>10 单)按批回执,一函一批,标题带批次号

## 质量判据

- 四验:FUEL_ORDER_SPEC_V1 §四 四门机判(G1 qid 映射/G2 transcript 硬约束/G3 gold 可解析/G4 held-out 泄漏实算),判据零改动;FAIL 只出自四门
- 判读:照 compass 判据正本;打分口径与独立复核并行披露,不混口径
- 争议:人工仲裁走 mailbox,机判结果不代改

## 版本

v1.1 · 2026-10-05 · 增补:返工≤2 次+判据 sha 预注册条款(v2 判据④对齐)——判读结论有异议时返工至多 2 次,判据正本 sha 预注册后不追溯改判
v1 · 2026-10-05 · 变更须函告服务对象
