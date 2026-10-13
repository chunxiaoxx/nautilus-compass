---
name: orgfuel-ORGG-8747b06aa8cc3ee4-ceb3ca9c58
description: "判读档判例 2026-08-30-multi-tenant-memory-design · 1. 问题与愿景 ## 1."
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8747b06aa8cc3ee4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-30-multi-tenant-memory-design · 1. 问题与愿景
## 1. 问题与愿景

8/30 两次安全事件证明单租户形态不可对外:① workbuddy 接入 MCP 可读各对话框全部记忆(存量全权 token + TCP 通道无项目边界);② 8770 老服务 X-User-ID 无验证,公网 443 可冒充任意用户读记忆、无凭证写记忆目录(记忆投毒),均已修复。

用户愿景(原话):"各个用户的各个设备各个 agent 互相映射就能实现统一记忆管理"——即**每个用户一个记忆空间,其在所有设备上的所有 agent 汇入同一空间;用户之间完全隔离**。
