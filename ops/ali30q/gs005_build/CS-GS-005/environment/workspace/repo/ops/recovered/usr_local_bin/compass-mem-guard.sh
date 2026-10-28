#!/bin/bash
PID=$(systemctl show -p MainPID --value compass-bge-daemon.service)
[ -z "$PID" ] || [ "$PID" = "0" ] && exit 0
RSS_KB=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
[ -z "$RSS_KB" ] && exit 0
MB=$((RSS_KB/1024))
if [ $MB -gt 8000 ]; then
  systemctl restart compass-bge-daemon.service
  echo "compass-mem-guard: restarted at ${MB}MB" >> /var/log/compass-mem-guard.log
fi
