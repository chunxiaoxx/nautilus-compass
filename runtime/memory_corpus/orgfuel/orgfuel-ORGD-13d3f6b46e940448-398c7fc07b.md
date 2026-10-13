---
name: orgfuel-ORGD-13d3f6b46e940448-398c7fc07b
description: "[## 六 · S5 上岗切换(tools/p3_promote.py)+ S6 台账] - champion.json"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-13d3f6b46e940448
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 六 · S5 上岗切换(tools/p3_promote.py)+ S6 台账] - champion.json 原子切换(tmp 写+rename):{adapter_path, adapter_sha16, gate_report_sha16, corpus_delta_sha16, promoted_at}。
- 回滚:保留最近 3 代 champion;kill switch=手动把 champion.json 指回上一代(一条命令,设计档承认人工兜底)。
- 台账 runtime/judge_lora_p3/ledger.json(JSON 数组;仓 .gitignore 第 7 行 `*.jsonl` 全局忽略,审计件须入 git 故用 .json):每轮一条{cycle, delta_n, verdict(SKIP/PASS/FAIL), 门读数, sha 链}并 commit;每条结论带证据三层标注(JUDGING_EVIDENCE_TIERS_20261003)。
