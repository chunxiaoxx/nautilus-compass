---
name: orgfuel-ORGD-64ad4aad25cc4ece-527b9dbc07
description: "[## 5. 分期(降险 · 每期可独立验证)] - **P0 · 立 T4 GPU daemon**(只你 · 无 a"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-64ad4aad25cc4ece
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 5. 分期(降险 · 每期可独立验证)] - **P0 · 立 T4 GPU daemon**(只你 · 无 agent):spot T4 起 daemon + 拉语料/快照 + reranker 默认开 + 客户端(你本机 recall hook)指向 T4。验:跨设备 recall 通 + reranker lift 生效 + 抗抢占(手动 kill 验 fallback)。
- **P1 · CPU 冷备 + ingest 写路径**:CPU 服装冷备 daemon(systemd · 抢占信号触发)+ 所有 ingest 走云 daemon(单写权威)。验:T4 kill → 1 分钟 fallback · ingest 落持久。**先修 CJK-surrogate ingest 崩 bug**(P1 必修前置)。
- **P2 · Phase B 多 agent**(gated 平台 token):per-agent scope + v5/v7/kairos wire MCP client。验:每 agent recall+ingest 实测。
- **P3 · 本地只读缓存(C)**:离线 recall 副本。
