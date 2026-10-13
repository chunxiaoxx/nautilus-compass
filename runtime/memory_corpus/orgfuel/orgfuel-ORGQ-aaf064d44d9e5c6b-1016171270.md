---
name: orgfuel-ORGQ-aaf064d44d9e5c6b-1016171270
description: "轮次记录 R452 · 2026-10-10 凌晨六(主件轮:rerank 隧道端到端✅[实测 74ms]——本机→A1"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-aaf064d44d9e5c6b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R452 · 2026-10-10 凌晨六(主件轮:rerank 隧道端到端✅[实测 74ms]——本机→A100 GPU 全链打通,daemon 开关设计定案)
### R452 · 2026-10-10 凌晨六(主件轮:rerank 隧道端到端✅[实测 74ms]——本机→A100 GPU 全链打通,daemon 开关设计定案)
- **主件=隧道落地**(tools/a100_rerank_tunnel.py+bat 保活,compass_tunnel.bat 同款模式):paramiko direct-tcpip 双向 pump+断线自愈(transport 失活重建);凭据走 a100_env 不落仓。**端到端实测 74ms**(本机 19879→A100 9879→GPU rerank→返回,ok=True 排序语义正确)——E1 检索质量读数的全链路硬件路径就此打通。
- **daemon 开关设计定案**(候下件实现):`COMPASS_RERANK_REMOTE=127.0.0.1:19879`(空=本地模式不变)——daemon.py `_rerank_top` 加 remote 分支(socket 协议同 rerank_svc),改 plugin 分支+测试择窗部署(生产 daemon 直改纪律)。
- 修一坑:类型注解 `socket.channel` 定义时求值炸→`from __future__ import annotations` 一行修。
- 开业周 daemon 部署窗后顺序:分支合入→隧道 watchdog 自启→COMPASS_PROD_RERANK=1+COMPASS_RERANK_REMOTE 双开→E1 判据 v2 工作集复测验收(零新判据)。
