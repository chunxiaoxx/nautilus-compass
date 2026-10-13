---
name: orgfuel-ORGD-78268f976191ff0f-c31b5d2a8f
description: "[## 1. 证据诊断:六能力真实状态(file:line)] | 能力 | 判定 | 证据 | 闭环差什么 | |--"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-78268f976191ff0f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 1. 证据诊断:六能力真实状态(file:line)] | 能力 | 判定 | 证据 | 闭环差什么 |
|---|---|---|---|
| 记忆胶囊 | 本机闭环·跨设备半闭环 | 摄取 `daemon.py:956`(写+embed+缓存)/召回 `daemon.py:667`;无 capsule 抽象,单元=session_*.md | `/v1/v14/ingest_obs` 用 `ingest_obs+content`,daemon 只认 `ingest+text`(`daemon.py:1092`)→ 疑似静默失败,需云端实测 |
| 检索保真度 | 半闭环 | 生产=裸 bge-m3;reranker 把 P@5 0.86→0.92、单会话 MRR 0.398→0.522(`RESULTS.md:54,186`),只在 benchmark | reranker+query-rewrite+lifecycle 进生产 daemon 热路径 |
| LLM-WIKI2 融合 | 半闭环 | =Ebbinghaus 遗忘+4层做成零-LLM schema(`paper/LLM_WIKI2_FUSE_DESIGN.md`);字段+函数+测试齐,`README:104` 自认生产未激活 | 生产 recall 调 `promote_lifecycle_tier()` |
| LLM 增强融入 | 半闭环 | judge(Gemini)+离线蒸馏(本地 Qwen `l2_distiller.py:33`)在用;召回 `llm_backend` hook 在(`metamemory/builder.py:76`)未接 provider(`recall.py:1247`);5 LLM flag 未接线(`llm_opt_in.py:31`) | hook 接 Qw
