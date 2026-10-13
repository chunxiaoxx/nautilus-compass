---
name: orgfuel-ORGG-79b1d724ee922212-e5ff26cf5b
description: "判读档判例 WIRING_PLAN_20261004 · L2 · schema 会签线(flywheel case_s"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-79b1d724ee922212
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 WIRING_PLAN_20261004 · L2 · schema 会签线(flywheel case_spec × compass verdict_schema_v2)【本周】
## L2 · schema 会签线(flywheel case_spec × compass verdict_schema_v2)【本周】

- **接口**:flywheel `case_spec`(声明式验证案 schema,gen4_v1 校验 PASS)× compass `VERDICT_SCHEMA_V2.md`
- **步骤**:①读 flywheel case_spec 全文(仓 C:/Users/chunx/Projects/nautilusflywheel,找 gen4_v1 样例)②产出映射表:case_spec.判据版本 → verdict.criteria.version/ref;case_spec.验收判据 → verdict.criteria.ref;verdict.verdict.state → case_spec 状态机③会签函发 flywheel(双向引用:case_spec 引 verdict_schema_v2 作为结果格式,verdict 引 case_spec 作为案件定义)④各自 schema 加 `peer` 字段
- **验收**:两 schema 互引字段落地,gen4 案例用 v2 verdict 出一份样板
- **依赖**:无(单方面可先做映射表)
