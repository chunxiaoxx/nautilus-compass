#!/bin/bash
# 链路自愈+量测(launchd 两个定时任务共用入口)
# refresh: 机场节点轮换后自动重生成三份订阅并部署(自愈)
# watch  : 每小时穿家宽出口做端到端探活并留档(量测供应商稳定性)
set -u
cd /Users/chunxiao.wang/Projects/nautilus-compass
RUNTIME_DIR=runtime/egress_reports
mkdir -p "$RUNTIME_DIR"
TOKEN=$(cat ~/.config/nautilus/sub_token.txt)

refresh() {
  uv run -q --with pyyaml python3 tools/egress/gen_sub.py >> "$RUNTIME_DIR/refresh.log" 2>&1
  uv run -q --with pyyaml python3 tools/egress/gen_rocket_conf.py /tmp/rocket_chain.conf >> "$RUNTIME_DIR/refresh.log" 2>&1
  scp -q /tmp/rocket_chain.conf "cloud:/var/www/subs/$TOKEN/rocket.conf" >> "$RUNTIME_DIR/refresh.log" 2>&1
  uv run -q --with pyyaml python3 tools/egress/gen_uri_sub.py /tmp/rocket_sub_b64.txt >> "$RUNTIME_DIR/refresh.log" 2>&1
  scp -q /tmp/rocket_sub_b64.txt "cloud:/var/www/subs/$TOKEN/rocket.txt" >> "$RUNTIME_DIR/refresh.log" 2>&1
  echo "$(date '+%F %T') refresh done" >> "$RUNTIME_DIR/refresh.log"
}

watch() {
  TS=$(date '+%F %T')
  IP=$(curl -sx "socks5h://hwT25fxG:aXc4xS8s@99.112.135.180:3322" --max-time 20 https://api.ipify.org 2>/dev/null)
  T=$(curl -sx "socks5h://hwT25fxG:aXc4xS8s@99.112.135.180:3322" -o /dev/null -w '%{time_total}' --max-time 20 https://www.baidu.com 2>/dev/null)
  OK=$([ "$IP" = "99.112.135.180" ] && echo OK || echo BAD)
  echo "$TS exit=$IP($OK) baidu=${T}s" >> "$RUNTIME_DIR/watch.log"
  # 连续 3 次异常亮牌
  tail -3 "$RUNTIME_DIR/watch.log" | grep -c BAD | grep -q 3 && touch "$RUNTIME_DIR/CHAIN_ALERT"
}

case "${1:-}" in
  refresh) refresh ;;
  watch) watch ;;
esac
