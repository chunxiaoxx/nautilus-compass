---
name: orgfuel-ORGD-b0ad4dd14c319c75-c4adee7582
description: "[### 复算 FAIL 后修复与重测(2026-09-14 午后 · 用户拍板「先修 J1/J3 → 重测闭环 → 发"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-b0ad4dd14c319c75
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 复算 FAIL 后修复与重测(2026-09-14 午后 · 用户拍板「先修 J1/J3 → 重测闭环 → 发通] | # | 判定 | 读数 |
|---|---|---|
| J1 | **PASS** | 9/9 后 34/34 带 fact_status(100%;含本日新增 2 条带 measured 的会话记忆) |
| J2 | **PASS** | 复测三档:unique / gray 0.809 / merge 0.9184 |
| J3 | **PASS** | 带链查询命中 arm-a(body 偏移 814 的 3 条尾部链接)→ chain_extra 全带出 ✓;6 查询批量严格验证(每条 chain 目标 ∈ via 条目全文链接 ∧ via ∈ top ∧ 不与 top 重复)ALL PASS;延迟 588-790ms 与基线同量级;无链→空由代码结构+单测保证 |
| J4 | **PASS** | 三 fact hit@3 全对 GREEN(2/654/502ms) |
| 单测 | PASS | 19/19 |
