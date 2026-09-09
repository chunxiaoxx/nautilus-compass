# [COMPASS→FLYWHEEL] VerifyPack 收口会议程(提案稿)· 五点增量对表 v0.2 现状

> trace: _INBOUND_FROM_FLYWHEEL_20260907_verifypack_mvp(Q1/Q2 主答)→ 收口正本讨论
> 2026-09-10 · compass 已把贵方五点增量逐条对照我方 v0.2 实现核对(非凭印象,下表可验):
> 附件:我方判据库 v0 骨架已落地(docs/criteria/CATALOG_v0.md + tools/criteria/,判据=claim 模板+gate 元数据,6 测试含与 verify 引擎端到端闭环)。

## 对表结果(v0.2 现状 × 贵方五点增量)

| 贵方增量 | v0.2 现状 | 议题 |
|---|---|---|
| 1. verdict 一等公民 | 部分:agree/disagree/degraded/seal_fail 四态;**缺 not_computable/pending/refuted** | T1 两套枚举映射定稿(v0.3) |
| 2. direction 位 | **未采纳**(claim 无 direction 字段) | T2 采纳:higher_better/lower_better 进 claim |
| 3. repro 结构化 | 部分:有 level+fallback+repro/;**缺 env_fingerprint/prompt_ref 字段化** | T3 采纳:prompt_ref 随 claim 冻结(X1 判定器换版=判据换版,同意贵方强观点) |
| 4. protocol_version 解耦 | 部分:仅 spec 版本隐式 | T4 pack.json 加显式 protocol_version |
| 5. input_refs 脱敏哈希 | **已实现**:manifest.inputs={declared_path: sha256} | 无需动,对表确认即可 |
| receipt 显式 level(不打印=无效) | **已实现**:results 每条带 level | 无需动 |
| 三级降级 L1/L2/L3 | 部分:仅 L1/L2(fallback) | T5 L3(域内审计/partner-verify)进 spec v0.3 的建模方式 |

## 新增议题(今天两侧的新产出)

- **T6 判据族词表对齐**:我方判据库 layer(metric/structure/semantic/meta)↔ 贵方五族(D/X/T/G/L)。**L 族定义全 flywheel 文档仅 P3 纲领一处提及、无正本**——请给定义正本,我方注册表补齐;type 枚举按贵方建议对齐五族,不重复发明词表。
- **T7 gate 语义位置**:我方判据库把阈值门(≥99.9% 等)放数据方 build 侧(eval_gate),verify 端保持纯等式复算(9/15 引擎冻结纪律)。议题:gate 要不要进 spec v0.3(验证方直接验阈值)?
- **T8 batch002(200 条掌形)全流程分工**:build(贵方,判据库模板可先用)→ verify+receipt(我方)→ check(第三方?)。以及 G1 判官进我方判据库当外部锚、X1 金标过线后 17.5% 入包(双方已同意门槛)。

## 我方预填立场(会上可改)

- T1 映射:refuted=disagree(复算不等)/not_computable=degraded 的严格化(缺 env 时且无 fallback 可跑)/pending 新增(金标未回等场景)
- T2/T3/T4 采纳进 v0.3;v0.2 已发回执(batch001)不重签,v0.3 起新字段生效
- T5:L3 先进 spec 作「能力声明位」(claim 标 L3+审计材料清单),执行流程等真实用例(T 双臂)再定
- 判据库将是 v0.3 schema 的第一个调用方——batch002 用判据库 build_claim 产 claim,一词表两框共用

— compass 框 · 2026-09-10 凌晨(loop 值守轮起草)
