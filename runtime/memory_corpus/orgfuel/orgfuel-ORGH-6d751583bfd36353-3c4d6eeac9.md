---
name: orgfuel-ORGH-6d751583bfd36353-3c4d6eeac9
description: "commit 0148b7014460 2026-06-05 feat: 双轮接线 — 检索栈进生产(reranker+"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6d751583bfd36353
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 0148b7014460 2026-06-05
feat: 双轮接线 — 检索栈进生产(reranker+lifecycle) + FDE verdict→PoI adapter (#36)
* feat(contract): v1.7.1 隐式合约派生 + 自动消费检测 + receiver-authorship

解 cross-agent close_loop 的 consumed=0:
- derive_implicit_contracts: inbound_/outbound_ session 文件 → 隐式合约(解 adoption · 零行为改变 · 2->11)
- auto_detect_consumption: 激活死代码 matches_consume_hint · consume_method=auto_keyword 可审计
- receiver_authorship + _norm_party: 消费须在 receiver root · 杀跨 root FP
- 领域 stopword: 消除 boilerplate 词 FP
全部 opt-in (auto_detect/include_implicit/receiver_authorship 默认 False) · live recall 行为不变
残留: receiver root 内 keyword 仍过度匹配 · 需语义/LLM (见 study design_cross_agent_handoff.md)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>

* ops: P0 shadow drift 遥测幂等 apply 脚本

把本 session P0 的 daemon.py 
