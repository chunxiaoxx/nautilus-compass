---
name: orgfuel-ORGH-99f4cf7f3f945cd9-c576b9f5f1
description: "工具决策记录 memory_git_keeper.py Memory git keeper · frame-upgrad"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-99f4cf7f3f945cd9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 memory_git_keeper.py
Memory git keeper · frame-upgrade-20260904-compass #3 (letta MemFS 原则).

对 ~/.claude/projects/*/memory/ 各目录: 有变化才 commit,误改可回滚、版本可追溯。
由 Stop hook 每次调用(见 ~/.claude/settings.json hooks.Stop),任何失败静默退出
(记忆 keeper 永不阻塞会话收尾)。

2026-09-06 · perf(HANDOFF_20260906_STOPHOOK_PERF_DAEMON):1513 个 memory 目录
逐个 spawn git add/diff = 0.21s/仓 ≈ 314s,把每轮 Stop 拖到 ~5 分钟。修法 =
mtime 预过滤:目录内 .md 全部早于窗口(默认 7 天,MEMKEEP_WINDOW_DAYS 可调)
则跳过——死目录零 git 调用,活跃目录行为不变(全目录覆盖保留,与被 revert 的
54e4a3a「只管当前项目」不同,不丢其他目录的 checkpoint 覆盖)。
