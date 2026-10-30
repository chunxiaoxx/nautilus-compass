#!/bin/zsh
# 插件部署工件化(任务书第4条)——从仓部署到 ~/.claude/plugins 并带 sha16 清单。
# 用法: deploy_plugin.sh [--check]  (--check=只比对漂移不部署)
# 纪律来源: 10/30 冰山案——仓与插件四份编码实现漂移,手工同步是病根。
# 10/30 扩面: 纳入 M5 记忆门三件套载体(daemon.py/mcp_server.py/session_writer.py/memgate_stamp.py)
set -e
REPO=/Users/chunxiao.wang/Projects/nautilus-compass
PLUG=~/.claude/plugins/nautilus-compass
FILES=(recall.py compass_verify.py compass_hud_wrapper.py daemon.py mcp_server.py session_writer.py memgate_stamp.py)
CHECK="${1:-}"
MANIFEST=$REPO/runtime/pipeline_state/plugin_deploy_manifest.txt
mkdir -p "$(dirname "$MANIFEST")"; : > "$MANIFEST"
DRIFT=0
for f in $FILES; do
  if [ ! -f "$REPO/$f" ]; then echo "⚠ 仓缺 $f(跳过)"; continue; fi
  R=$(tr -d '\r' < "$REPO/$f" | shasum -a 256 | cut -c1-16)
  P="-"; [ -f "$PLUG/$f" ] && P=$(tr -d '\r' < "$PLUG/$f" | shasum -a 256 | cut -c1-16)
  echo "$f repo=$R plugin=$P" >> "$MANIFEST"
  if [ "$R" != "$P" ]; then
    if [ "$CHECK" = "--check" ]; then echo "🔴漂移: $f (repo=$R plugin=$P)"; DRIFT=1
    else cp "$REPO/$f" "$PLUG/$f"; echo "✅部署: $f ($R)"; fi
  else
    echo "✅一致: $f ($R)"
  fi
done
[ "$CHECK" = "--check" ] && [ "$DRIFT" = "1" ] && exit 1
exit 0
