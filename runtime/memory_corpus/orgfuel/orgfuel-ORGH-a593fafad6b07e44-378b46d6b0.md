---
name: orgfuel-ORGH-a593fafad6b07e44-378b46d6b0
description: "commit a6fa495afd22 2026-09-06 perf(tools): memory_git_keepe"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a593fafad6b07e44
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a6fa495afd22 2026-09-06
perf(tools): memory_git_keeper 只管当前会话项目——全量扫 1513 目录把每轮 Stop 拖到 49s+
原版每次 Stop 全量扫 ~/.claude/projects/*/memory(本机 1513 个项目目录,
仅 glob 即分钟级),所有对话框每轮收尾等 49s+ 甚至卡死。
改法:stdin transcript_path 提取项目名只管当前会话(1513→1);fallback
取最近活跃 3 个;墙钟预算 15s 超时即弃。
实测:3min+ 卡死 → 2.4s,提交功能不变(auto checkpoint 正常落)。
平台代修(用户在平台会话拍板热修),晨间知会 compass。
