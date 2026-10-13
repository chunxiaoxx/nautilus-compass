---
name: orgfuel-ORGM-05ee3ac5b12fcfef-007170d0d4
description: "记忆条目 daemon-auth-and-hf-offline-20260901.md # daemon 9876 鉴权"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-05ee3ac5b12fcfef
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 daemon-auth-and-hf-offline-20260901.md
# daemon 9876 鉴权 + HF offline + 云端 token 收窄(2026-09-01)

## 1 · 本地 9876 token 鉴权(daemon v3.0.10 · commit c1c4a9e)

- 规则:`ping` 免鉴权(探活依赖 daemon_start.ps1/sh),其余 action(recall/drift/status/ingest/score/shutdown)一律 `hmac.compare_digest` 比对 token;无/错 token 回 `{"ok":false,"error":"auth_failed"}`。
- token 文件:`~/.claude/.cache/compass_daemon_token`(64 hex·0600·首次启动自动生成;`COMPASS_DAEMON_TOKEN_FILE` 可覆盖)。
- **新写 9876 客户端必须在请求 JSON 带 `"token"` 字段**(从上述文件读);已改齐:compass_hud_wrapper(plugins+ops 同步)、stop_hook(plugins+repo 同步,含 8/30 os import 差异收编)、ops/compass_status.sh、daemon.py CLI stop。
- 客户端 token 缺失时 daemon DENY + HUD 显示"服务未响应"——看到这个先查 token 文件而不是重启 daemon。
- **9/1 下午抓到漏改客户端 #1:本地 stdio 桥 `~/.claude/plugins/nautilus-compass/mcp_server.py`(Claude Code 的 naut
