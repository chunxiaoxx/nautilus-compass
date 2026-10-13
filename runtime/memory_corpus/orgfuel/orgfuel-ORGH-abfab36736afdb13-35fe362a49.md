---
name: orgfuel-ORGH-abfab36736afdb13-35fe362a49
description: "commit fe8a0c35f821 2026-08-24 fix(bridge): MCP 云桥握手修复——根因=顶"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-abfab36736afdb13
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit fe8a0c35f821 2026-08-24
fix(bridge): MCP 云桥握手修复——根因=顶层 _eid 非法字段(非版本号):① initialize 改写改 id 无关(旧版只认 id==0) ② 剥离顶层 _eid(v2.1 只清 result 内部,顶层漏网=CC 2.1 严格客户端弃连真根因) ③ 全线 belt-and-braces _eid 剥离
Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
