---
name: orgfuel-ORGM-add01da47efa5019-3f186b5ae3
description: "记忆条目 commit-attribution-rule-20260923.md commit 署名纪律(2026-09"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-add01da47efa5019
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 commit-attribution-rule-20260923.md
commit 署名纪律(2026-09-23 用户纠正,发现 GitHub 上各仓提交署名显示为 claude 而非 chunxiaoxx)。

**Why**:两层原因——①nautilus-compass repo 级 git config 曾被设为 `nautilus-platform-saas-dialog <saas-dialog@nautilus.social>`(平台迁移期多框身份),该邮箱不关联 GitHub 账号→主作者灰色无名;②`Co-Authored-By: Claude <noreply@anthropic.com>` trailer 被 GitHub 渲染成 Claude 官方头像徽章,视觉上抢走主署名。用户全局规则(git-workflow.md)早已写明「Attribution disabled globally」,加尾注本就违规。

**How to apply**:
- 所有仓 commit 主署名=`chunxiaoxx <chunxiaoxx@gmail.com>`(nautilus-compass repo config 2026-09-23 已修;新仓/临时 fork 工作目录开工先 `git config user.name/user.email`)
- **任何 commit 不加 Co-Authored-By 尾注**(Claude/Happy 都不加),PR body 里的生成器致谢行也不加
- **历史已全量重写**(2026-09-23 用户批准执行):filter-repo+mailmap 把 saas-dialog 及全部人名变体统一为 chunxiaoxx(1340 commits/35 分支/29 tags,bot 保留),mir
