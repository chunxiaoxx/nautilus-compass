---
name: orgfuel-ORGG-3fb5be1ffe70879e-0c18b12a4b
description: "判读档判例 L1_CRITERIA_FREEZE_NOTES_20261005 · 一、SWE-bench Verifi"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-3fb5be1ffe70879e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 L1_CRITERIA_FREEZE_NOTES_20261005 · 一、SWE-bench Verified
## 一、SWE-bench Verified

- **上游正本**:HF `princeton-nlp/SWE-bench_Verified`(500 题,OpenAI 2024-08 人工验证 subset);判分引擎 swe-bench/SWE-bench(301 实测自 princeton-nlp 迁移);官方榜 swebench.com。
- **criteria_version v1 冻结口径**:主指标=**resolved %**(FAIL_TO_PASS+PASS_TO_PASS 单元测试全过);harness=官方 run_evaluation 栈(候选 agent harness=mini-swe-agent)钉 release tag;单 run 起步(k=1),k>1 时报 mean±spread;模型训练截止披露强制。
- **污染风险与对策**:①题目源自公开 GitHub issue——对策:报告模型 cutoff 与数据集发布(2024-08)关系,cutoff 晚于发布者标注"泄漏风险"进观察区;②harness 提示词差异——对策:harness 版本+agent 配置随成绩行公示;③容器架构——对策:linux x86_64 标准容器,环境哈希随行。
- **U 态条款**:官方评测栈大版本变更而未复跑=旧成绩转观察区。
