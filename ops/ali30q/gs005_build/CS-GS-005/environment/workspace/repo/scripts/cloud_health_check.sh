#!/usr/bin/env bash
# cloud 生产 box 健康检查(事故/重启后跑·2026-06-19 建)
# 本地用法:  ssh cloud -p 24860 'bash -s' < scripts/cloud_health_check.sh
# 或拷到 box:  bash ~/cloud_health_check.sh
set +e
echo "================ NAUTILUS CLOUD HEALTH $(date -u +%H:%M:%SZ) ================"

echo "--- 1. load / mem / disk ---"
uptime
free -m | grep -E "Mem|Swap"
df -h / /data 2>/dev/null | grep -vE "tmpfs|udev"

echo "--- 2. 关键 systemd 服务 ---"
for svc in nginx nautilus-backend docker; do
  st=$(systemctl is-active "$svc" 2>/dev/null)
  printf "  %-20s %s\n" "$svc" "$st"
done

echo "--- 3. 生产容器(应全 Up) ---"
docker ps --format "{{.Names}}\t{{.Status}}" 2>/dev/null | grep -E "espocrm|n8n|nautilus|neo4j|label-studio" | head -20

echo "--- 4. 残留 SWE-bench 负载(应空·否则 docker kill) ---"
pgrep -af "rsi_swe_docker|run_evaluation|swebench" | grep -v pgrep | head
docker ps --filter name=sweb --format "{{.Names}}" | head

echo "--- 5. 站点端到端(本机 localhost) ---"
curl -s -o /dev/null -w "  backend localhost:8000 /api/stats -> %{http_code}\n" --max-time 10 http://localhost:8000/api/stats
curl -s -o /dev/null -w "  nginx localhost:3000 -> %{http_code}\n" --max-time 10 http://localhost:3000/ 2>/dev/null

echo "--- 6. 最近后端错误(若服务存在) ---"
journalctl -u nautilus-backend -n 8 --no-pager 2>/dev/null | tail -8

echo "================ END · 公网请用 curl https://www.nautilus.social/ 复核 ================"
