#!/usr/bin/env bash
# fleet_status.sh · S4 全框状态一览——五框 commit+服务+信箱,一次跑完(默认从 compass 本地跑)
# 用法: bash tools/fleet_status.sh
set -u
P=~/Projects
echo "===== FLEET STATUS $(date '+%m-%d %H:%M') ====="
for d in nautilus-compass nautilusflywheel nautilus-core; do
  if [ -d "$P/$d/.git" ]; then
    echo "-- $d: $(cd $P/$d && git log --oneline -1 --format='%h %ad %s' --date=format:'%m-%d %H:%M' | head -c 90)"
  fi
done

# cloud 框(v5/platform 云侧,经 ssh)
if ssh -o ConnectTimeout=10 cloud 'echo ok' >/dev/null 2>&1; then
  echo "-- cloud(v5/platform 侧):"
  ssh -o ConnectTimeout=10 cloud 'cd /home/ubuntu/nautilus-v5 2>/dev/null && git log --oneline -1 2>/dev/null | head -c 80; echo; systemctl is-active compass-bge-daemon nautilus-v5.service compass-judge-status 2>/dev/null | paste -sd/ -'
  echo "-- 信箱: $(curl -s -m 15 'https://nautilus.social/api/platform/org/mailbox?to=compass&unread=1' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("data") or []))' 2>/dev/null)"
else
  echo "-- cloud: UNREACHABLE"
fi
echo "===== done ====="
