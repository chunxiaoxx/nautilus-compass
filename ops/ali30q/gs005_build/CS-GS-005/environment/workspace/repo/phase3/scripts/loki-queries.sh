#!/bin/bash

# Loki 查询示例脚本

LOKI_URL="http://localhost:3100"

echo "=== Loki Query Examples ==="
echo ""

# 1. 查询所有 nautilus-backend 日志
echo "1. Query all nautilus-backend logs:"
echo "curl -G -s \"$LOKI_URL/loki/api/v1/query_range\" \\"
echo "  --data-urlencode 'query={job=\"nautilus-backend\"}' \\"
echo "  --data-urlencode 'limit=10'"
echo ""

# 2. 查询错误日志
echo "2. Query error logs:"
echo "curl -G -s \"$LOKI_URL/loki/api/v1/query_range\" \\"
echo "  --data-urlencode 'query={job=\"nautilus-backend-error\"}' \\"
echo "  --data-urlencode 'limit=10'"
echo ""

# 3. 查询包含特定关键词的日志
echo "3. Query logs containing 'error':"
echo "curl -G -s \"$LOKI_URL/loki/api/v1/query_range\" \\"
echo "  --data-urlencode 'query={job=\"nautilus-backend\"} |= \"error\"' \\"
echo "  --data-urlencode 'limit=10'"
echo ""

# 4. 查询 Nginx 访问日志
echo "4. Query nginx access logs:"
echo "curl -G -s \"$LOKI_URL/loki/api/v1/query_range\" \\"
echo "  --data-urlencode 'query={job=\"nginx\",type=\"access\"}' \\"
echo "  --data-urlencode 'limit=10'"
echo ""

# 5. 查询最近 1 小时的日志
echo "5. Query logs from last 1 hour:"
START=$(date -d '1 hour ago' +%s)000000000
END=$(date +%s)000000000
echo "curl -G -s \"$LOKI_URL/loki/api/v1/query_range\" \\"
echo "  --data-urlencode 'query={job=\"nautilus-backend\"}' \\"
echo "  --data-urlencode 'start=$START' \\"
echo "  --data-urlencode 'end=$END' \\"
echo "  --data-urlencode 'limit=10'"
echo ""

# 6. 查询可用的标签
echo "6. Query available labels:"
echo "curl -s \"$LOKI_URL/loki/api/v1/labels\""
echo ""

# 7. 查询特定标签的值
echo "7. Query values for 'job' label:"
echo "curl -s \"$LOKI_URL/loki/api/v1/label/job/values\""
echo ""

# 执行实际查询
echo "=== Executing Queries ==="
echo ""

echo "Available jobs:"
curl -s "$LOKI_URL/loki/api/v1/label/job/values" | jq -r '.data[]' 2>/dev/null || echo "No data yet"
echo ""

echo "Recent nautilus-backend logs (last 5):"
curl -G -s "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode 'query={job="nautilus-backend"}' \
  --data-urlencode 'limit=5' | \
  jq -r '.data.result[].values[]?[1]' 2>/dev/null || echo "No logs found"
