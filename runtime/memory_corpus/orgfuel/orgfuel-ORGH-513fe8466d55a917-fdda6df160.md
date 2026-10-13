---
name: orgfuel-ORGH-513fe8466d55a917-fdda6df160
description: "commit 079ae1650cca 2026-08-22 feat(daemon): recall 直交付正文摘录("
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-513fe8466d55a917
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 079ae1650cca 2026-08-22
feat(daemon): recall 直交付正文摘录(v2.3.1)
- 此前 recall 只回 path+常空的 description,消费方须二跳读文件才能拿到内容
  (recall-usefulness 实验发现的产品缺口)
- hit 新增 body(前 500 字);插件 mcp_server 渲染追加前 280 字
- 本地验证:daemon+plugin 端到端,飞书部落事实查询正文直达

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
