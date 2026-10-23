#!/bin/zsh
# Mac mini 灾难重建:6 个 launchd 服务一键装载(2026-10-23 底账配套)
set -e
for f in "$HOME"/Projects/nautilus-compass/ops/launchd/*.plist; do
  n=$(basename "$f")
  cp "$f" "$HOME/Library/LaunchAgents/$n"
  launchctl unload "$HOME/Library/LaunchAgents/$n" 2>/dev/null || true
  launchctl load "$HOME/Library/LaunchAgents/$n"
  echo "loaded: $n"
done
echo "--- 状态 ---"
launchctl list | grep -E "nautilus|compass"
