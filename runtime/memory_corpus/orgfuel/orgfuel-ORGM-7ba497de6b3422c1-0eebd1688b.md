---
name: orgfuel-ORGM-7ba497de6b3422c1-0eebd1688b
description: "记忆条目 security-workbuddy-token-scoping-20260830.md --- name: "
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-7ba497de6b3422c1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 security-workbuddy-token-scoping-20260830.md
---
name: security-workbuddy-token-scoping-20260830
description: 8/30 workbuddy 跨框记忆暴露修复:TCP MCP 版补项目级 scope(8/28 体系只覆盖 HTTP 版)· 13 存量全权 token·workbuddy 已换 scoped+旧已 revoke · 验证矩阵与遗留
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  fact_status: measured
---

# workbuddy 跨框记忆暴露 · TCP scope 修复(2026-08-30)

用户实测发现 workbuddy 接入 compass MCP 能读各对话框全部记忆。查透三层根因:

1. **存量未迁移**:8/28 scoped-token 机制只交付了 HTTP 版(mcp_http_server.py)+签发工具,云端 `/etc/compass/tokens.json` 13 个存量 token 全是旧格式(=全权 read:*+write:*)。
2. **TCP 通道无项目边界**:workbuddy 与各框桥主通道 = 云端 TCP 9877(mcp_server.py),只有工具级 tools.read/write,持有效 token 可跨全部 project 读写。8/28 修复漏了这条通道。
3. **通道拓扑**:workbuddy 桥(mcp_stdio_to_cloud.py)recall/drift/thread
