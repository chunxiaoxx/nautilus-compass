#!/bin/bash
# 管道共享状态面刷新器——compass 产出,飞轮快筛/打包轮消费(接线件 2026-10-28)
cd /Users/chunxiao.wang/Projects/nautilus-compass || exit 1
mkdir -p /Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/runtime/pipeline_state
# F-010: 共享 qs.json 必须全量库存;12h 窗会把 CS-303/507 整题踢出。
# 跨时段不混算由 collect 的 latest_batch 承担,不靠 newer-than 砍题。
python3 ops/ali30q/collect_for_quickscreen.py --v5 --scratch --newer-than-hours 0 > /Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/runtime/pipeline_state/qs.json 2>/dev/null
cd /Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix || exit 1
# 仅在有变化时 commit(防 git 噪声,值守 noop 静默纪律)
git add codesense/runtime/pipeline_state/qs.json 2>/dev/null
if ! git diff --cached --quiet codesense/runtime/pipeline_state/qs.json 2>/dev/null; then
  git commit --quiet -m "chore(pipeline_state): qs.json 刷新(读数汇总·compass 自动产) [bait-loop接线]"
fi
