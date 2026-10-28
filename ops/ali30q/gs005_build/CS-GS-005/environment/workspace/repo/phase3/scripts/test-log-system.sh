#!/bin/bash

# Nautilus 日志系统快速测试脚本

echo "=== Nautilus Log Aggregation System Test ==="
echo ""

# 1. 检查服务状态
echo "1. Checking service status..."
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E '(NAME|loki|promtail)'
echo ""

# 2. 检查 Loki 健康状态
echo "2. Checking Loki health..."
LOKI_STATUS=$(curl -s http://localhost:3100/ready)
if [ "$LOKI_STATUS" = "ready" ]; then
  echo "✅ Loki is ready"
else
  echo "⚠️  Loki status: $LOKI_STATUS"
fi
echo ""

# 3. 检查可用的日志源
echo "3. Checking available log sources..."
curl -s http://localhost:3100/loki/api/v1/label/job/values | jq -r '.data[]' 2>/dev/null || echo "No jobs found yet"
echo ""

# 4. 检查 Promtail 采集状态
echo "4. Checking Promtail targets..."
docker logs promtail 2>&1 | grep "Adding target" | tail -5
echo ""

# 5. 测试查询功能
echo "5. Testing query functionality..."
QUERY_RESULT=$(curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"}' \
  --data-urlencode 'limit=1')

if echo "$QUERY_RESULT" | grep -q '"status":"success"'; then
  echo "✅ Query API is working"
  echo "Sample log entries:"
  echo "$QUERY_RESULT" | jq -r '.data.result[].values[]?[1]' 2>/dev/null | head -3
else
  echo "⚠️  Query returned no results (logs may not be ingested yet)"
fi
echo ""

# 6. 检查日志文件
echo "6. Checking log files..."
ls -lh /var/log/nautilus* /var/log/nginx/*.log 2>/dev/null | awk '{print $9, $5}'
echo ""

# 7. 检查存储使用
echo "7. Checking storage usage..."
du -sh /home/ubuntu/loki-data 2>/dev/null || echo "Data directory not accessible"
echo ""

echo "=== Test Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure Grafana data source: http://localhost:3100"
echo "2. Import dashboard: config/grafana-dashboard-logs.json"
echo "3. Set up alerting with Alertmanager"
echo "4. Run: bash /home/ubuntu/analyze-logs.sh for detailed analysis"
