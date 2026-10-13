---
name: orgfuel-ORGM-b7bb5ad5afcd08f0-4d5e7ff233
description: "记忆条目 outreach-channels-20260911.md # 推广渠道 9/11 定案(经验)  **选 a"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-b7bb5ad5afcd08f0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 outreach-channels-20260911.md
# 推广渠道 9/11 定案(经验)

**选 awesome 列表先查生命体征,star 数会骗人**:appcypher/awesome-mcp-servers(5.7k★)实际 2026-08-01 已 archive 只读;wong2/awesome-mcp-servers(8k★)PR+Issues 全关(纯手动维护)。fork+分支+entry 全推好才发现门是死的,浪费两轮。提交前必查:`archived`/`has_issues`/`has_discussions`/最近 `pushed_at`。主力=punkpeye #14065(27k★,open 等 merge)。

**Why:** 两列表的 fork 分支/内容/PR 文案全就位后,用户网页点开才发现「所有者已禁用 PR」和「已归档」——API 的 REST 404 无法区分「禁用」和「token 权限」,网页提示才是权威。

**How to apply:**
- GitHub API 写不了第三方 PR 的根因分层:GCM 的 gho_ token 是 GitHub App user-to-server,有 contents write 无 pulls write(GraphQL CreatePullRequest FORBIDDEN/REST 404);自家 repo 实测能到业务层=账号没被 flag。
- `git credential fill` 在 Chrome 重启后会轮换返回空;兜底=`gh auth token`(同一 gho_ 前缀,稳定可用)。
- dev.to `POST /api/comments` 已废(V0/V1 Accept 都 404),写评论唯一路=用户网页贴(草稿给全文)。
- Chrom
