---
name: orgfuel-ORGG-14fbb571c0a6544a-70ab0ff0cb
description: "判读档判例 HANDOFF_20260917_glama_connector · 提交步骤(glama.ai,需登录 G"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-14fbb571c0a6544a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 HANDOFF_20260917_glama_connector · 提交步骤(glama.ai,需登录 GitHub 账号)
## 提交步骤(glama.ai,需登录 GitHub 账号)

1. 打开 **https://glama.ai/mcp/connectors** → "Add MCP Server";
2. **Transport**:Streamable HTTP · **URL**:`https://compass.nautilus.social/mcp/`;
3. **Auth**:API Key/Bearer——先去 https://compass.nautilus.social/signup 控制台
   建 **scoped 只读 token**(仅 memory 读权限,别用全权);
4. 名称/描述:Nautilus Compass Memory · local-first agent memory via MCP
   (byte-recomputable, ed25519-signed receipts);
5. Source repo:github.com/chunxiaoxx/nautilus-compass(v3.2.0 · 344290b0);
6. 提交后看列表页:连接器页应有 tools 列表(凭 token 内省);
   若显示 "unable to introspect"/"?" → 走下面备选。
