#!/bin/bash

echo "=== Nautilus Log Analysis ==="
echo ""

echo "=== Log Files Status ==="
ls -lh /var/log/nautilus* /var/log/nginx/*.log 2>/dev/null | awk '{print $9, $5}'
echo ""

echo "=== Top 10 Error Messages ==="
if [ -f /var/log/nautilus-backend-error.log ]; then
  grep -i error /var/log/nautilus-backend-error.log 2>/dev/null | \
    tail -100 | \
    awk '{for(i=4;i<=NF;i++) printf $i" "; print ""}' | \
    sort | uniq -c | sort -rn | head -10
else
  echo "No error log found"
fi
echo ""

echo "=== Recent Backend Logs (Last 10) ==="
tail -10 /var/log/nautilus-backend.log 2>/dev/null || echo "No backend log found"
echo ""

echo "=== Nginx Access Stats (Last 100 requests) ==="
if [ -f /var/log/nginx/access.log ]; then
  tail -100 /var/log/nginx/access.log | \
    awk '{print $9}' | sort | uniq -c | sort -rn
else
  echo "No nginx access log found"
fi
echo ""

echo "=== Nginx Error Count ==="
if [ -f /var/log/nginx/error.log ]; then
  wc -l /var/log/nginx/error.log
else
  echo "No nginx error log found"
fi
echo ""

echo "=== Loki Service Status ==="
docker ps --filter name=loki --format "{{.Names}}: {{.Status}}"
echo ""

echo "=== Promtail Service Status ==="
docker ps --filter name=promtail --format "{{.Names}}: {{.Status}}"
