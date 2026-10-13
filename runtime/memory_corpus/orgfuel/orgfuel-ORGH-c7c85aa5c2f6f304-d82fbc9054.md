---
name: orgfuel-ORGH-c7c85aa5c2f6f304-d82fbc9054
description: "commit d4bd5a15f486 2026-09-30 fix(cloud-daemon)+incident: 内"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c7c85aa5c2f6f304
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit d4bd5a15f486 2026-09-30
fix(cloud-daemon)+incident: 内存patch三连环回归全程与回退——churn死循环(LRU逐出后重进不读pkl全量重嵌=CPU风暴18万拒)+pkl回读副作用(RSS 6.4G);已回退9-22原版
- 根因链:MAX_PROJ=4<活跃项目数→churn;刀2漏pkl回读→每轮全项目re-embed;in-flight满→秒拒断供
- 判据设错公开修正:chunk PyList开销低估(32KB vs numpy 4KB),3G线低于物理边界
- 教训入档:LRU必须连带重进路径;生产叠实验三小时=三次回归;根治改离线仿真路线
- v3.1实验版留存daemon.py.v31_experimental_20260930(云);事故函已发platform
- status豁免补丁(本地版)保留待下次窗口

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
