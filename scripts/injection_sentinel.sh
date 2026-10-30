#!/bin/zsh
# 注入哨兵(2026-10-30 立·记忆死7天案的报警缺口补件)
# 判据: 今日 usage.jsonl 里 recall_hit 事件数 = 0 且已过 09:00 → 记忆注入链死,亮牌
# 值守轮每轮调用;退出码 2=亮牌(进值守报表),0=健康/未到判定时点
# SENTINEL_HOME=假缓存目录(混沌验证用·任务书第5条)
BASE="${SENTINEL_HOME:-$HOME/.claude/plugins/nautilus-compass/.cache}"
USAGE="$BASE/usage.jsonl"
ARCH="$BASE/usage_archive"
TODAY=$(date +%Y-%m-%d)
HOUR=$(date +%H)
N=0
for f in "$USAGE" "$ARCH/usage_${TODAY}.jsonl"; do
  [ -f "$f" ] && N=$((N + $(grep -c "\"event\": *\"recall_hit\"\|recall_hit" "$f" 2>/dev/null || echo 0)))
done
# 只数今天的行(跨天文件需按行内 ts 过滤)
N_TODAY=$( { [ -f "$USAGE" ] && cat "$USAGE"; [ -f "$ARCH/usage_${TODAY}.jsonl" ] && cat "$ARCH/usage_${TODAY}.jsonl"; } 2>/dev/null | grep "recall_hit" | grep -c "$TODAY" )
if [ "$N_TODAY" -eq 0 ] && [ "$HOUR" -ge 9 ]; then
  echo "🔴注入哨兵:今日($TODAY)recall_hit=0——记忆注入链疑似死(查 recall.py 目录解析/daemon 9876/节流态)"
  exit 2
fi
echo "✅注入哨兵:今日 recall_hit=${N_TODAY}"
exit 0
