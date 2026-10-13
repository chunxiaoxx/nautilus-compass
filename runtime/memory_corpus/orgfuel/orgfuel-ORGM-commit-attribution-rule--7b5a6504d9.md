---
name: orgfuel-ORGM-commit-attribution-rule--7b5a6504d9
description: "--- name: commit-attribution-rule-20260923 description: "用户纠"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-commit-attribution-rule-
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: commit-attribution-rule-20260923
description: "用户纠正——commit 署名必须是 chunxiaoxx,禁止 Co-Authored-By 尾注(Claude/Happy 都不加)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5103bb42-025f-4754-adcf-4ff0f2b7218d
  modified: 2026-09-23T01:09:44.759Z
fact_status: inferred
---

commit 署名纪律(2026-09-23 用户纠正,发现 GitHub 上各仓提交署名显示为 claude 而非 chunxiaoxx)。

**Why**:两层原因——①nautilus-compass repo 级 git config 曾被设为 `nautilus-platform-saas-dialog <saas-dialog@nautilus.social>`(平台迁移期多框身份),该邮箱不关联 GitHub 账号→主作者灰色无名;②`Co-Authored-By: Claude <noreply@anthropic.com>` trailer 被 GitHub 渲染成 Claude 官方头像徽章,视觉上抢走主署名。用户全局规则(git-workflow.md)早已写明「Attribution disabled globally」,加尾注本就违规。

**How to apply**:
- 所有仓 commit 主署名=`chunxiaoxx <chunxiaoxx@gmail.com>`(nautilus-compass repo config 2026-09-23 已修;新仓
