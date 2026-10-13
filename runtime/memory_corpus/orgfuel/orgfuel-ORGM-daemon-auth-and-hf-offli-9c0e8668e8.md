---
name: orgfuel-ORGM-daemon-auth-and-hf-offli-9c0e8668e8
description: "--- name: daemon-auth-and-hf-offline-20260901 description: ""
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-daemon-auth-and-hf-offli
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: daemon-auth-and-hf-offline-20260901
description: "8/31-9/1 安全债清偿:本地 9876 daemon v3.0.10 token 鉴权(新写客户端必带 token)+ BGE 加载\"client has been closed\"死循环根因=代理断流须 HF_HUB_OFFLINE=1 + 云端 12 token 收窄 9 个剩 3 等报备"
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-04T03:11:39.653Z
---

# daemon 9876 鉴权 + HF offline + 云端 token 收窄(2026-09-01)

## 1 · 本地 9876 token 鉴权(daemon v3.0.10 · commit c1c4a9e)

- 规则:`ping` 免鉴权(探活依赖 daemon_start.ps1/sh),其余 action(recall/drift/status/ingest/score/shutdown)一律 `hmac.compare_digest` 比对 token;无/错 token 回 `{"ok":false,"error":"auth_failed"}`。
- token 文件:`~/.claude/.cache/compass_daemon_token`(64 hex·0600·首次启动自动生成;`COMPASS_DAEMON_TOKEN_FILE` 可覆盖)。
- **新写 9876 客户端必须在请求 JSON 带 `"token"` 字段**(
