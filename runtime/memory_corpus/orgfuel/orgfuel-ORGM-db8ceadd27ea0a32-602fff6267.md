---
name: orgfuel-ORGM-db8ceadd27ea0a32-602fff6267
description: "记忆条目 session_20260717-0335_SSOT副本探针已上线.md # SSOT副本探针已上线  ## "
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-db8ceadd27ea0a32
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_20260717-0335_SSOT副本探针已上线.md
# SSOT副本探针已上线

## 上下文
用户拍板即刻做:recall hook 新增 SSOT 副本一致性探针(v2.3·commit 141040c),CHARTER/LOOP_STATE 跨 repo 哈希漂移即对每框亮牌;首跑证实两锚三 repo 全漂移,请 compass 框接管收敛

## 内容
2026-07-17 用户判"信息不对称严重影响协同",拍板即刻上线副本一致性探针。V5 框实施(动了 compass turf,做的是最小外科手术,后续归你们维护):

实现:新模块 ssot_consistency.py(纯 stdlib·~90 行·fail-soft)+ recall.py contracts 块后 10 行调用。双写:nautilus-compass repo(commit 141040c)+ ~/.claude/plugins/nautilus-compass/(live hook 路径,已 e2e 验证段落真出现在 hook 输出)。逻辑:对 nautilus-v5/nautilus-core/nautilus-compass 三 repo 根的 FDE_BUSINESS_CHARTER.md + LOOP_STATE_SSOT.md 剥 frontmatter 后正文 sha256 对比;全一致=单行✅;漂移=🔴亮牌列各副本哈希+mtime+最新副本提示。env 覆盖:COMPASS_SSOT_REPOS。

首跑 grounded 结果(即用户抱怨的实证):
- FDE_BUSINESS_CHARTER.md:三 repo 三个哈希(f30a5193/724fbfda/78501e24)。已知差异:compass 副本主体还是 6/9 旧版;v5/co
