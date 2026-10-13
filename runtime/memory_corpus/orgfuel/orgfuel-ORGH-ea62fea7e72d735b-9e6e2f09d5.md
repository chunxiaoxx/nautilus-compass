---
name: orgfuel-ORGH-ea62fea7e72d735b-9e6e2f09d5
description: "commit 1428ee53df56 2026-08-29 feat(security): scoped-token "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ea62fea7e72d735b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1428ee53df56 2026-08-29
feat(security): scoped-token 鉴权体系(2.3.1)——治'任何能 ssh cloud 的进程可自签全库 token'的权限洞
- mcp_http_server: token 携带 scopes(read:<proj>/write:<proj>/read:*/admin),_check_scope fail-closed 强制执行;旧格式向后兼容=read:*
- ops/compass_token_admin.py: 签发/撤销收敛为人工显式工具,grant 无 --scopes 拒绝,全权需 --yes-i-want-star
- quickstart: 自签改为默认 read:<project> scoped;重启两服务;自检改走 recall(read scope 内)
- tests/test_mcp_auth_scopes.py: 4 组 12 断言全绿

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
