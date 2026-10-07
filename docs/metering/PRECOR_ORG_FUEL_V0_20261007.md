# PRECOR ORG-FUEL-V0 · 组织判例燃料试点判据档(2026-10-07 · 预注册)

> 承 ORG_PRECEDENT_FUEL_V0(用户提议)。试点范围=compass 单框(queue.md 全流水 R1-R292+session 记忆 111 条);产物=结构化 org 判例(目标 ≥50 条过门)。

## 一、判例 schema(冻结)

```
{pf_id, event_date, domain, anchor_level(L0/L1/L2/L3),
 situation, judgment_or_action, outcome, outcome_source,
 verdict(有效/无效/不可验), evidence_tier(实测/推断/不可验), content_hash}
```

- anchor_level 判定:L0=物理执行结果/用户拍板/外部复算;L1=跨框互认/专家;L2=模型判(参考层,不进训练集);L3=无结果自述(剔除);
- domain 沿用 qid 前缀法(基础设施/lme/评测/组织协同…)。

## 二、流水线(v0 单框,半自动)

1. **采集**:queue.md 轮次条目+session 记忆条目(111 条)解析为事件;
2. **抽取**:规则抽"判断/动作+结果"对(含:实验判门读数/勘误/审计 finding/崩溃修复/决策后果);
3. **判定**:每候选经 NACRE judge(实例 v1)三态判"是否构成有效判例";抽 10% 人工复检;
4. **入册**:verdict=有效 且 anchor∈{L0,L1} → delta registry(fuel_eligible=true)+corpus_pipeline 计数。

## 三、判门(试点验收,冻结)

1. 产出过门判例 **≥50 条**(L0+L1 合计);
2. 抽检 10%(≥5 条)人工复检一致率 ≥80%;
3. 采集覆盖率:queue.md R256-R292 各轮至少被抽取评估一次(漏轮披露);
4. 全程行级写(崩溃零丢失,v2 教训)。

—— compass · 2026-10-07 · PRECOR-ORG-FUEL-V0(判据冻结)

## v1 判据预告(信箱函件流接入,2026-10-07)

1. 采集源扩展:org_mailbox 函件(全框往返,自带 B 账正本)——抽取"判断/承诺→回执/结果"对(承诺-兑现判例);
2. **元判读边界条款(防自指,固化)**:org 判例训练 judge 的用途仅限"元判读"(识别失败判断模式);L2 及以下自产内容永不进训练集;任何越界需新档+用户批;
3. **燃料供给结构注记**:自产判例密度随流水衰减(易摘果实现象),持续供给依赖外部单(L0/L1 高锚判例)——**开业=燃料闸门**的定量依据(242 条/3 天为易摘峰值,不可外推线性)。
