# case_spec × verdict_schema_v2 映射表(L2 会签件,2026-10-03)

> 承接线计划 L2(docs/plans/WIRING_PLAN_20261004.md)。实物对读:flywheel runtime/case_specs/gen4_v1.json+src/nautilusflywheel/pipeline/case_spec.py(6c4d5a7)× compass docs/protocol/VERDICT_SCHEMA_V2.md。

## 一、字段映射(几乎一一对应,同构性实证)

| flywheel case_spec | compass verdict v2 | 缝合动作 |
|---|---|---|
| case_id | case_id | 同名直通,无缝合 |
| criteria_ref + criteria_frozen_file | criteria.ref + criteria.version + freeze_chain | verdict 出件时回填 frozen_file 的 sha16 入 freeze_chain |
| stop_loss {rule, action} | verdict.stop_loss {seed_locked/no_expansion/no_new_methods} | spec 的 rule 是前置声明,verdict 的布尔是判定记录——语义同构,verdict 须引用 rule 原文于 text |
| gates.judge = "compass" | judge 字段 | spec 已声明判读方,verdict.judge 与之互证 |
| gates.pre_registered | criteria.freeze_chain[预注册闸] | 同一事件两侧记账 |
| arms[] (role/data_ref/budget) | readings(臂读数) + material(sha 锚定) | 臂结构进 readings,材料 sha 进 material |
| deps {criteria_frozen, balance_ok} | —(判读侧无对应) | spec 侧发车闸,verdict 不重复 |
| artifacts.verdict_ref = "compass:gen4_v1" | **peer_case_spec**(v2.1 新增字段) | **双向引用落点**:verdict 加 peer_case_spec 反指 spec 文件 sha16 |
| (无) | claims[](边界绑定) | verdict 净新增:声称与不支持边界 |

## 二、同构性结论(协同机制协议化的依据)

两个 schema 是同一验证案生命周期的两侧:case_spec=**案的定义侧**(判据棘轮+止损线前置声明+发车闸),verdict v2=**案的结果侧**(判据版本+锚定链+统计裁决+claims 边界+止损判定记录)。判据零放宽/止损线/预注册三制度在两侧均有字段承载——**组织制度已 schema 化,协议会签=把函件约定升级为字段约束**。

## 三、会签动作(已完成项标 ✅)

1. ✅ compass verdict v2 加 `peer_case_spec` 可选字段(docs/protocol/VERDICT_SCHEMA_V2.md v2.1)
2. ✅ 本映射表落档
3. ⏳ 会签函发 flywheel(附本表+提案:case_spec 侧无需改动,verdict_ref 现有格式即兼容;gen4_v1 出 verdict 时按 v2+peer_case_spec 出首份样板)
4. ⏳ gen4_v1 判读时双向引用实测(spec sha16 ↔ verdict peer_case_spec.sha16 对拍)
