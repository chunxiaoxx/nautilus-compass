---
name: orgfuel-ORGD-2a0ddf84433f7fd4-16e7119f7b
description: "[## v1.2 注记(2026-10-07 发车前修订,非放宽)] - **分片键修订**:design 原按 art"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-2a0ddf84433f7fd4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## v1.2 注记(2026-10-07 发车前修订,非放宽)] - **分片键修订**:design 原按 artifact.domain 分片,实测该字段全空(1454/1454 unknown)→改按 **qid 域前缀**(数据自身的天然分片),分片原理(域路由)不变;
- **分片清单冻结**:可训域片=**rejudge(500)/lme-d14(451)/lme-d12(451)** 三片;小域(t3/f15/T* 系合计 52 条)并入 D-rest 不训片,推理路由到默认(基座+现役大 LoRA);
- **对照公平性补充**:B 各片训练集=该域 train 切片+全域锚回放 12%(取 split_train 分层抽样);A 臂读数沿用 PRECOR B/C bf16-greedy=0.8797(291 题同评测集);
- 分片统计与冻结时刻:rejudge 500/lme-d14 451/lme-d12 451/D-rest 52(口径=三 split 合并去重后)。
