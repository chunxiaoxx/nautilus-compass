#!/usr/bin/env bash
# Nautilus 站点低噪看门狗 · 只报「真出事」· 直发 Telegram(绕坏掉的后端 webhook + 系统 proxy)
#
# 设计铁律(吸取 2026-06-16 教训:旧 CPU>40% 瞬时阈值狂刷 → 被关 → 真站点 down 没人知):
#   - 只检测「结果级」故障:站点经 nginx 不可达 / 关键服务挂 / 持续资源枯竭。
#   - 绝不报瞬时 CPU / 负载尖峰。
#   - 连续 N 次失败才报一次(防抖);持续故障每 ~60min 再提醒一次;恢复发一条。
# 由 systemd timer 每 2 分钟跑一次。token/chat 从 .env 读,不硬编码。
set -uo pipefail

ENV_FILE=/home/ubuntu/nautilus-v5/.env
STATE=/run/nautilus-watchdog.fails
FAIL_THRESHOLD=2          # 连续 2 次(~4min)才报,过滤瞬时抖动
REMIND_EVERY=30           # 持续故障每 30 个周期(~60min)再提醒一次

TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"'"'"' ")
CHAT=$(grep -E '^TELEGRAM_CHAT_ID=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"'"'"' ")

send() {  # $1 = 文本(可含换行)
  [ -n "${TOKEN:-}" ] && [ -n "${CHAT:-}" ] || return 0
  curl -s --noproxy '*' --max-time 15 \
    "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    --data-urlencode chat_id="${CHAT}" \
    --data-urlencode text="$1" >/dev/null 2>&1
}

if [ "${1:-}" = "--selftest" ]; then
  send "🧪 [看门狗自检] $(date '+%F %T')"$'\n'"已部署的 nautilus-site-watchdog 发送链路正常。今后只在站点/服务真出事时报警。"
  echo "selftest sent (token=${TOKEN:+set} chat=${CHAT:+set})"; exit 0
fi

problems=""
add() { problems="${problems}• $1"$'\n'; }

# 1. 站点经 nginx 可达(本地走 nginx → 抓 nginx 挂 / 后端 502 / 整链异常·正是 6/16 事故)
code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 https://localhost/ 2>/dev/null)
case "$code" in 200|301|302|307|308) ;; *) add "站点经 nginx 返回 ${code:-超时}(nginx/后端链路异常)";; esac

# 2-3. 关键 systemd 服务
systemctl is-active --quiet nginx            || add "nginx.service 未运行"
systemctl is-active --quiet nautilus-backend || add "nautilus-backend.service 未运行"

# 4. 磁盘 >90%(持续型·非抖动)
disk=$(df / 2>/dev/null | awk 'NR==2{gsub("%","",$5);print $5+0}')
[ "${disk:-0}" -ge 90 ] && add "根分区磁盘 ${disk}%(>90%)"

# 5. 可用内存 <600MB(配合连续阈值 = 持续低才报)
memav=$(free -m 2>/dev/null | awk '/^Mem:/{print $7+0}')
[ "${memav:-9999}" -lt 600 ] && add "可用内存 ${memav}MB(<600MB)"

# 6. compass→T4 recall 隧道(9876/9877)· 掉 = v5/v7/kairos recall 断(6/16 cutover 后)
# 仅当端口确实被监听(隧道已部署)时才检测,避免未部署环境误报
for tport in 9876 9877; do
  if systemctl is-active --quiet compass-t4-tunnel 2>/dev/null; then
    timeout 3 bash -c "exec 3<>/dev/tcp/127.0.0.1/${tport}" 2>/dev/null || add "compass→T4 隧道端口 ${tport} 不通(三框 recall 降级)"
  fi
done

prev=$(cat "$STATE" 2>/dev/null || echo 0); prev=${prev:-0}
ts=$(date '+%F %T')

if [ -n "$problems" ]; then
  cnt=$((prev + 1)); echo "$cnt" > "$STATE"
  if [ "$cnt" -eq "$FAIL_THRESHOLD" ] || { [ "$cnt" -gt "$FAIL_THRESHOLD" ] && [ $(((cnt - FAIL_THRESHOLD) % REMIND_EVERY)) -eq 0 ]; }; then
    send "🔴 Nautilus 告警 · ${ts}"$'\n'"${problems}主机: VM-0-8-ubuntu(43.160.239.61)"
  fi
else
  [ "$prev" -ge "$FAIL_THRESHOLD" ] && send "🟢 Nautilus 恢复正常 · ${ts}"$'\n'"所有检查通过"
  echo 0 > "$STATE"
fi
