---
name: orgfuel-ORGM-a14c2b96932a8784-cbebed510c
description: "记忆条目 cheap-tier-close-and-watcher-20260904.md 2026-09-04 che"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-a14c2b96932a8784
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 cheap-tier-close-and-watcher-20260904.md
2026-09-04 cheap-tier(raw-state 强化)双域定案:**web 36.3%(87/240)/ ent 36.5%(77/211)**,双双低于 d12 现役(40.0/38.4)→ 预注册规则执行,三改组合(a11y_chars1500/query_decomp/shot_per_traj)关闭,d12 维持现役,营销/README 沿用现役数字。ent raw 曾被坏判官(4096+medium,启动漏带修正 flag)压至 30.8%,重判修复 +5.7pt(flips +16/−4,failed=0)。

**watcher 全自动链路(定型,后续跑分默认)**:GPU 上 `watch_ent_rejudge.sh` = `while pgrep -f evaluation.harness; do sleep 60; done; export $(cat /root/e2e/judge.env|xargs); python3 /root/rejudge_cheap.py <out>/per_question.jsonl <rejudge_out>.jsonl`——跑完→自动重判→ALL_DONE 零人工。启动命令模板(含 `--evaluator-max-completion-tokens 16384 --evaluator-reasoning-effort low`)+3 分钟自检已固化 TRANSFER_RUNBOOK(commit d7df1d6)。

**Why**:连踩 401/4096 两坑后,判官配置坑已从模板层堵死;watcher 把"跑完忘重判"这个环节也消掉了。本线 5 次 judge 事故(401/4096×2/断连/预算)全
