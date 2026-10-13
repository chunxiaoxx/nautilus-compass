---
name: orgfuel-ORGG-f6851b260adc7468-b54e86d8e1
description: "判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 3. 三方法案"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f6851b260adc7468
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 3. 三方法案
## 3. 三方法案

- **方案 A(推荐)· compass 自建 authz scope 层 + 平台签 token**:compass 在 auth.py 之上加
  per-tool scope 表(agent_id → 允许的工具集),平台签 token 时把 scope claim 进 JWT 或
  compass 本地维护 scope 映射。最小新代码 · 复用既有 authn · 守 G-turf。
- **方案 B · 平台统一 IAM**:平台建中央 IAM 管所有 agent×工具权限,compass 查平台。重 ·
  违"平台只建 substrate"红线 · 弃。
- **方案 C · 无 scope · 仅 authn + quota(现状)**:任何持平台 JWT 的 agent 可调任何工具。
  简单但无最小权限 · 财务/写类工具(ingest/poi)无隔离 · 弃(poi_writer 最小权限先例已立反对)。

**选 A。**
