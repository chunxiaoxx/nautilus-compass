# 自举标签质量抽检预注册档(2026-10-13 · R532 · 四臂判定的下一杠杆)

> 动机:四臂对照(FOURARM_COMPARE_20261013)实证"标签质量>数据量"(1.7B-v2 自举池 -2.0pp)。
> 本检测定自举标签池(1811 条,占池 55%)的 judge 自判准确率,决定语料棘轮的下一步方向。

## 一、抽样(冻结)

- 总体:8B 触发池 2843 条中 self_labeled 1811 条(eightb_trigger 切分口径)
- 分层:按 _src(org_fuel:gate_passed/letters/docs/outreach/queue/memory/flywheel/flywheel_vetted/queue_r3/memory_r3/flywheel_r3/grain_r4/commits_r5)占比分层,n=100,SEED 20261013
- 盲评者:非实现者(Claude 会话,非 judge 1.7B 权重、非训练执行者)——判据模板语义与 judge 同一口径,但**评时不看 judge_verdict**(盲评)

## 二、判据(冻结,出数前)

- 盲评口径:"含具体判定或行动 AND 具体可验证结果/后果 → pass;有行动无结果 → insufficient_evidence;无有效内容 → fail"
- 对拍统计:一致率 = (盲评==judge_verdict)/100;分源一致率;Cochran Q 或 binomial 95% CI
- **方向门(冻结)**:
  - 一致率 ≥90%:自举标签可用,棘轮继续(8B 第三评可发)
  - 80–90%:可用但降置信,混合人工抽检入惯例(每轮 5%)
  - <80%:标签回灌修正(盲评分歧条目复查)后再训,数量棘轮暂停
- 分歧条目全数列明(逐条+双方判定),不隐藏

## 三、输出

- 报告:docs/metering/SELFLABEL_AUDIT_20261013.md(对拍表+一致率+CI+分歧分析+方向裁定)
- 样本:runtime/org_fuel/selflabel_audit_sample.jsonl(100 条,qid/src/content/judge_verdict/盲评列)

—— compass · SELFLABEL-AUDIT · R532 · 2026-10-13(盲评前冻结)
