---
name: orgfuel-ORGH-7f6f97af4c3d7e10-1f22f219dd
description: "工具决策记录 anchor_build_v01.py 锚点库 v0.1 构建(P0-full v2 前置 · 2026-"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-7f6f97af4c3d7e10
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 anchor_build_v01.py
锚点库 v0.1 构建(P0-full v2 前置 · 2026-10-02)。

修 v0 缺陷:effect 侧(reason_span)为簇级模板句→hit@5 结构上限 3-4%<5% 门槛。
v2 判据档:docs/metering/P0_FULL_PREREG_V2_20261002.md(先档后做)。

effect(果)= 样本级判定记录,按判据簇回源逐条构造(模板透明,字段全回溯);
cause(因)= 判据文本展开(criteria_lib_v0)+ source 尾段 + artifact_ref 原样。
A3 零编造:构造字段逐条回溯源行(双向断言:question 与 artifact_ref 现值一致)。
F1b 可分性预检:同簇 effect 唯一文本率 ≥95%。
