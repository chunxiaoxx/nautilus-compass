---
name: orgfuel-ORGH-d6c724305dbce8db-9dd73d3342
description: "commit 38d2f3fe8501 2026-07-08 docs(compass): P0 版本硬伤修正(中文 R"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d6c724305dbce8db
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 38d2f3fe8501 2026-07-08
docs(compass): P0 版本硬伤修正(中文 README)+ 卖点闭合设计文档
对外文档一致性 P0(实测校正,非引陈旧文档):
- README.zh-CN.md 版本徽章 1.0.0_stable → 2.3.0(对齐 pyproject 单一源)。
- README.zh-CN.md MCP 徽章 7 → 17 tools(自数 mcp_server.py TOOLS 注册表真实数,
  子 agent 说 16 亦不准,徽章 7 更错)。
- BLACKBOX_VS_WHITEBOX.md 安装命令解 pin ==1.1.0 → 不 pin(防再 stale)。
- docs/plans/2026-07-08 设计文档:两条卖点实测大半已闭合(act-on 0.178 非陈旧 0.012,
  生命周期 v2.3.0 已接生产 recall),真实剩余 = tier driver 未调度 + drift 52% 误报,
  + 文档反而低估现状。② 降误报属真工程,R3 长 session 尾部不做,fresh session 执行。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KPiwS16Zr86HwJ2jTBogzm
