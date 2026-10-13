---
name: orgfuel-ORGM-cheap-tier-close-and-wat-aa79736056
description: "--- name: cheap-tier-close-and-watcher-20260904 description:"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-cheap-tier-close-and-wat
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: cheap-tier-close-and-watcher-20260904
description: "cheap-tier 双域定案关闭(web 36.3/ent 36.5 均未超现役,三改组合关)+ watcher 全自动跑分链路定型(模板含 judge 修正 flag)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-04T12:10:30.121Z
---

2026-09-04 cheap-tier(raw-state 强化)双域定案:**web 36.3%(87/240)/ ent 36.5%(77/211)**,双双低于 d12 现役(40.0/38.4)→ 预注册规则执行,三改组合(a11y_chars1500/query_decomp/shot_per_traj)关闭,d12 维持现役,营销/README 沿用现役数字。ent raw 曾被坏判官(4096+medium,启动漏带修正 flag)压至 30.8%,重判修复 +5.7pt(flips +16/−4,failed=0)。

**watcher 全自动链路(定型,后续跑分默认)**:GPU 上 `watch_ent_rejudge.sh` = `while pgrep -f evaluation.harness; do sleep 60; done; export $(cat /root/e2e/judge.env|xargs); python3 /root/rejudge_cheap.py <out>/per_question.jsonl <rejudge_out>.jsonl`
