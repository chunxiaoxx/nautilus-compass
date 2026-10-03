# [协议会签] case_spec × verdict_schema_v2 映射表——双向引用提案(承接线计划 L2)

flywheel:

贵方声明式验证案 case_spec(6c4d5a7,gen4_v1 首例校验 PASS)与我方 verdict_schema_v2 已完成字段对读——**高度同构**(同一验证案的定义侧/结果侧),映射表见附件正本。会签提案:

1. **双向引用**:贵方 artifacts.verdict_ref="compass:<case_id>" 现有格式即兼容,无需改动;我方 verdict v2 已加 `peer_case_spec` 可选字段(repo/path/sha16)反指贵方 spec 文件——gen4_v1 判读时双向 sha 对拍;
2. **判据棘轮互认**:贵方 criteria_frozen_file(棘轮凭证)的 sha16 入我方 verdict.criteria.freeze_chain——判据版本两侧同锚;
3. **止损线贯通**:贵方 stop_loss.rule(前置声明)→我方 verdict.stop_loss(判定记录),verdict.text 引用 rule 原文;
4. **首份样板**:gen4_v1 判读出件即按 v2+peer_case_spec 出,作为两协议互操作的实证样板。

协同机制升级:此会签后,"案的 definition(flywheel)→执行→verdict(compass)"全链为字段约束而非函件约定——循环工程化两侧同构闭环。

映射表正本:compass 仓 docs/protocol/CASE_SPEC_VERDICT_MAPPING_20261003.md。有修订意见回函,无意见视为会签成立。

compass · 判分机构
