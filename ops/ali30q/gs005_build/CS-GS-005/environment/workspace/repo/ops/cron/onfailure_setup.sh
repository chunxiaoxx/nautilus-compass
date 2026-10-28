#!/bin/bash
# 一次性执行:B8 OnFailure 批量挂载(sudo 可用时跑: bash /tmp/onfailure_setup.sh)
set -e
for u in $(systemctl list-unit-files --type=service --no-pager | grep -E "nautilus|v7-|flywheel|compass" | grep -v notifier | awk '{print $1}'); do
  case "$u" in *@.service) continue;; esac
  D="/etc/systemd/system/$u.service.d"
  mkdir -p "$D"
  printf "[Unit]\nOnFailure=nautilus-cron-fail-notifier@%%n.service\n" | tee "$D/onfailure.conf" >/dev/null
done
systemctl daemon-reload
echo "done: OnFailure mounted on all org units"
