# 强模型重判预注册档(2026-10-13 · R534 · SELFLABEL_AUDIT 处置条款①执行)

> 依 SELFLABEL_AUDIT_20261013 §四.3:强模型重判全部自举池。判据本档冻结。

## 一、供给与被判对象

- **供给**:MiniMax-M3(api.minimaxi.com/v1,订阅制,理由:配方实测在档/400k 上下文/推理模型判别力;备选 ARK)
- **对象**:v2 池(orgfuel_v2,3551 条)中 self_labeled 2519 条(原 judge=1.7B 自判标签)
- **保留**:原 judge_verdict 字段不覆盖,新标签写 `strongmodel_verdict`——两标签并存可追溯

## 二、重判口径(与原 judge 模板同语义)

- 判据文本同 ORG-FUEL 三态模板:"含具体判定或行动 AND 具体可验证结果=pass;无具体结果=insufficient_evidence;非判例内容=fail"
- 输入=v2 池行 artifact.content(修复后全非空);截断 1400 字(与原 judge 轮同)
- 推理:温度 0(greedy);剥 `<think>`;max_tokens 8192

## 三、分阶段门(冻结)

| 阶段 | 量 | 通过门 |
|---|---|---|
| P0 先导 | 与 R532 盲评 58 条交集重判 | **对盲评一致率 ≥75%**(强模型 vs 非实现者人评;原 judge 同集 37.9%)|
| P1 全批 | 2519 条 | 输出三态非全 pass(判别力存在);落强model_verdict |
| P2 验收 | 全批后 | 抽 10% 非实现者盲评对拍 ≥90%(SELFLABEL 审计同法)方可回池为训练标签 |

**裁定**:P0 FAIL → 换备选 ARK 或升采样人工;P2 FAIL → 标签修复失败,回人工标注路线。

## 四、产出

- runtime/org_fuel/strongmodel_relabel_r534.jsonl(id/src/judge_verdict/strongmodel_verdict)
- 报告:docs/metering/STRONGMODEL_RELABEL_20261013.md(一致率对比+分布+抽样复核)

—— compass · R534 · 2026-10-13(重判前冻结)
