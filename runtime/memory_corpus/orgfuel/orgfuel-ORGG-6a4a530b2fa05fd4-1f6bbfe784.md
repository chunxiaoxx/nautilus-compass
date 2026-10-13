---
name: orgfuel-ORGG-6a4a530b2fa05fd4-1f6bbfe784
description: "判读档判例 2026-08-30-multi-tenant-memory-design · 2. 三层映射模型 ## 2"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6a4a530b2fa05fd4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-30-multi-tenant-memory-design · 2. 三层映射模型
## 2. 三层映射模型

```
用户(user_id · JWT 身份)
 ├─ 设备 A ─ agent 1 ─ token(read+write: <user> 的 project 集)
 ├─ 设备 B ─ agent 2 ─ token(read+write: <user> 的 project 集)
 └─ 设备 C ─ agent 3 ─ token(read-only: <user> 的 project 集)
隔离边界: project 命名空间。跨用户 = 跨 project = token scope 不可达。
```

- **身份**:人用 JWT(8770 已有 signup/login);agent 用 scoped token(工具代签或用户面板签发)。
- **空间**:每用户一个 primary project(`u_<id>_memory` 约定),可扩展多 project;同 user 的所有 token 指向同一 project 集 = "多设备多 agent 映射统一记忆"。
- **鉴权链**:JWT ↔ 用户;token ↔ (用户, scope 集);header-only 身份永久禁止(8/30 洞根因)。
