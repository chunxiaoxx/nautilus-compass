---
name: orgfuel-ORGH-2cc4fe9c9cfb8de1-7d0f51f0a8
description: "commit dd9e8bef5fd4 2026-08-29 feat(v3.1.0): workbuddy 反馈包 P"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2cc4fe9c9cfb8de1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit dd9e8bef5fd4 2026-08-29
feat(v3.1.0): workbuddy 反馈包 P0/P1 剩余项清零——drift fail-loudly/tokens mtime 热加载/daemon 冷启动重试/inotify 关闭告警;SERVER_VERSION 对齐 3.1.0 终结双轨版本号
- daemon.py: drift anchors 缺失从静默跳过改 fail-loudly(结果带 anchors_error+should_alert,治'安全防线形同虚设'P0·1.1);COMPASS_USE_INOTIFY=0 启动 WARNING(P1·2.2)
- mcp_http_server.py: tokens.json mtime 懒重载,新签 token 免 systemd restart(P1·2.1)
- mcp_server.py: daemon 超时自动重试一次放宽 90s(模型冷加载,P0·1.3)
- SERVER_VERSION 2.3.x→3.1.0: 治'仓 tag v3.0.0 服务报 2.3'双轨困惑(workbuddy 问'为何不是 v3.0')

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
