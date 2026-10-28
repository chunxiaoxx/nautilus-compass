#!/bin/bash
# 监控系统测试脚本

echo "=========================================="
echo "Nautilus 监控系统测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
PASSED=0
FAILED=0

# 测试函数
test_service() {
    local service_name=$1
    local test_command=$2
    local description=$3

    echo -n "测试 $description... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1. 检查 Docker 服务状态"
echo "----------------------------------------"
test_service "prometheus" "docker ps | grep -q nautilus-prometheus" "Prometheus 容器运行"
test_service "grafana" "docker ps | grep -q nautilus-grafana" "Grafana 容器运行"
test_service "alertmanager" "docker ps | grep -q nautilus-alertmanager" "AlertManager 容器运行"
test_service "node-exporter" "docker ps | grep -q nautilus-node-exporter" "Node Exporter 容器运行"
echo ""

echo "2. 检查服务健康状态"
echo "----------------------------------------"
test_service "prometheus-health" "curl -sf http://localhost:9090/-/healthy" "Prometheus 健康检查"
test_service "grafana-health" "curl -sf http://localhost:3000/api/health | grep -q ok" "Grafana 健康检查"
test_service "backend-health" "curl -sf http://localhost:8000/health" "Backend 健康检查"
echo ""

echo "3. 检查监控指标"
echo "----------------------------------------"
test_service "backend-metrics" "curl -sf http://localhost:8000/metrics | grep -q nautilus_" "Backend 指标端点"
test_service "prometheus-targets" "curl -sf http://localhost:9090/api/v1/targets | grep -q nautilus-backend" "Prometheus Targets"
echo ""

echo "4. 检查告警规则"
echo "----------------------------------------"
test_service "alert-rules" "curl -sf http://localhost:9090/api/v1/rules | grep -q HighAPIErrorRate" "告警规则加载"
echo ""

echo "5. 检查配置文件"
echo "----------------------------------------"
test_service "prometheus-config" "test -f monitoring/prometheus.yml" "Prometheus 配置文件"
test_service "alerting-rules" "test -f monitoring/alerting_rules.yml" "告警规则文件"
test_service "alertmanager-config" "test -f monitoring/alertmanager.yml" "AlertManager 配置文件"
test_service "grafana-datasource" "test -f monitoring/grafana/provisioning/datasources/prometheus.yml" "Grafana 数据源配置"
echo ""

echo "6. 测试指标数据"
echo "----------------------------------------"
echo -n "查询 HTTP 请求指标... "
HTTP_METRICS=$(curl -sf "http://localhost:9090/api/v1/query?query=nautilus_http_requests_total" | grep -o '"status":"success"')
if [ -n "$HTTP_METRICS" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ 无数据（可能需要等待数据采集）${NC}"
fi

echo -n "查询数据库连接指标... "
DB_METRICS=$(curl -sf "http://localhost:9090/api/v1/query?query=nautilus_database_connections" | grep -o '"status":"success"')
if [ -n "$DB_METRICS" ]; then
    echo -e "${GREEN}✓ 通过${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ 无数据（可能需要等待数据采集）${NC}"
fi
echo ""

echo "7. 检查日志文件"
echo "----------------------------------------"
test_service "logs-dir" "test -d logs" "日志目录存在"
test_service "security-analyzer" "test -f monitoring/analyze_security_logs.py" "安全日志分析脚本"
echo ""

echo "=========================================="
echo "测试总结"
echo "=========================================="
echo -e "通过: ${GREEN}${PASSED}${NC}"
echo -e "失败: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！监控系统运行正常。${NC}"
    echo ""
    echo "访问监控界面:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana:    http://localhost:3000 (admin/admin)"
    echo "  - AlertManager: http://localhost:9093"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败，请检查日志。${NC}"
    echo ""
    echo "查看日志命令:"
    echo "  docker-compose logs prometheus"
    echo "  docker-compose logs grafana"
    echo "  docker-compose logs alertmanager"
    exit 1
fi
