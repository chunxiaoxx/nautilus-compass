---
name: orgfuel-ORGH-52b12b15585ac4a6-c4a8eda386
description: "工具决策记录 corpus_split.py corpus_split · P2 训练集防泄漏分层切分。  关键设计: "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-52b12b15585ac4a6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 corpus_split.py
corpus_split · P2 训练集防泄漏分层切分。

关键设计:
  · 按 qid 分组切分(同题不同 run——d12/d14 同 question_id——必须同折,
    否则 test 泄漏:模型在 train 见过同题不同配置的判定)
  · 分层因子:label(pass/fail/insufficient_evidence)× 源族(bc1/t3/f15/rejudge/lme)
  · seed=20260930 固定;比例 80/10/10
  · 产出 runtime/verdict_corpus/{split_train,split_dev,split_test}.jsonl + 统计
