---
name: orgfuel-ORGD-3ba9c6f2e423c829-7dc4bd54ce
description: "[## 一、字段映射(几乎一一对应,同构性实证)] | flywheel case_spec | compass ver"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-3ba9c6f2e423c829
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一、字段映射(几乎一一对应,同构性实证)] | flywheel case_spec | compass verdict v2 | 缝合动作 |
|---|---|---|
| case_id | case_id | 同名直通,无缝合 |
| criteria_ref + criteria_frozen_file | criteria.ref + criteria.version + freeze_chain | verdict 出件时回填 frozen_file 的 sha16 入 freeze_chain |
| stop_loss {rule, action} | verdict.stop_loss {seed_locked/no_expansion/no_new_methods} | spec 的 rule 是前置声明,verdict 的布尔是判定记录——语义同构,verdict 须引用 rule 原文于 text |
| gates.judge = "compass" | judge 字段 | spec 已声明判读方,verdict.judge 与之互证 |
| gates.pre_registered | criteria.freeze_chain[预注册闸] | 同一事件两侧记账 |
| arms[] (role/data_ref/budget) | readings(臂读数) + material(sha 锚定) | 臂结构进 readings,材料 sha 进 material |
| deps {criteria_frozen, balance_ok} | —(判读侧无对应) | spec 侧发车闸,verdict 不重复 |
| artifacts.verdict_ref = "compass:gen4_v1" | **peer_case_sp
