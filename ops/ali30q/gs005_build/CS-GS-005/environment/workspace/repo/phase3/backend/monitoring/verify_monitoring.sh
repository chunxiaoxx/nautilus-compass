#!/bin/bash

# Nautilus Monitoring Verification Script
# 验证监控系统部署状态
# 作者: DevOps Team
# 日期: 2026-03-02

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 计数器
PASSED=0
FAILED=0
WARNING=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    ((WARNING++))
}

# 检查 Docker 容器状态
check_containers() {
    echo ""
    echo "=========================================="
    echo "1. Docker 容器状态检查"
    echo "=========================================="

    containers=("nautilus-prometheus" "nautilus-grafana" "nautilus-alertmanager" "nautilus-node-exporter")

    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            status=$(docker inspect --format='{{.State.Status}}' ${container})
            if [ "$status" == "running" ]; then
                log_success "${container} 运行中"
            else
                log_error "${container} 状态异常: ${status}"
            fi
        else
            log_error "${container} 未运行"
        fi
    done
}

# 检查服务健康状态
check_service_health() {
    echo ""
    echo "=========================================="
    echo "2. 服务健康状态检查"
    echo "=========================================="

    # 检查 Prometheus
    if curl -s -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_success "Prometheus 健康检查通过"
    else
        log_error "Prometheus 健康检查失败"
    fi

    # 检查 Grafana
    if curl -s -f http://localhost:3001/api/health > /dev/null 2>&1; then
        log_success "Grafana 健康检查通过"
    else
        log_error "Grafana 健康检查失败"
    fi

    # 检查 AlertManager
    if curl -s -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
        log_success "AlertManager 健康检查通过"
    else
        log_error "AlertManager 健康检查失败"
    fi

    # 检查 Node Exporter
    if curl -s -f http://localhost:9100/metrics > /dev/null 2>&1; then
        log_success "Node Exporter 健康检查通过"
    else
        log_error "Node Exporter 健康检查失败"
    fi
}

# 检查 Prometheus Targets
check_prometheus_targets() {
    echo ""
    echo "=========================================="
    echo "3. Prometheus Targets 检查"
    echo "=========================================="

    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，跳过详细检查"
        return
    fi

    targets=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null)

    if [ -z "$targets" ]; then
        log_error "无法获取 Prometheus targets"
        return
    fi

    # 检查每个 target
    echo "$targets" | jq -r '.data.activeTargets[] | "\(.labels.job)|\(.health)|\(.lastError)"' | while IFS='|' read -r job health error; do
        if [ "$health" == "up" ]; then
            log_success "Target ${job}: UP"
        else
            log_error "Target ${job}: DOWN - ${error}"
        fi
    done
}

# 检查 Grafana 数据源
check_grafana_datasources() {
    echo ""
    echo "=========================================="
    echo "4. Grafana 数据源检查"
    echo "=========================================="

    # 获取 Grafana API 响应
    datasources=$(curl -s -u admin:nautilus2024 http://localhost:3001/api/datasources 2>/dev/null)

    if [ -z "$datasources" ]; then
        log_warning "无法获取 Grafana 数据源（可能需要登录）"
        return
    fi

    if command -v jq &> /dev/null; then
        count=$(echo "$datasources" | jq '. | length')
        if [ "$count" -gt 0 ]; then
            log_success "Grafana 已配置 ${count} 个数据源"
            echo "$datasources" | jq -r '.[] | "  - \(.name) (\(.type))"'
        else
            log_warning "Grafana 未配置数据源"
        fi
    else
        log_warning "jq 未安装，跳过详细检查"
    fi
}

# 检查 Nautilus API Metrics
check_nautilus_metrics() {
    echo ""
    echo "=========================================="
    echo "5. Nautilus API Metrics 检查"
    echo "=========================================="

    if curl -s -f http://localhost:8000/metrics > /dev/null 2>&1; then
        log_success "Nautilus API metrics 端点可访问"

        # 检查关键指标
        metrics=$(curl -s http://localhost:8000/metrics)

        if echo "$metrics" | grep -q "nautilus_app_info"; then
            log_success "应用信息指标存在"
        else
            log_warning "应用信息指标缺失"
        fi

        if echo "$metrics" | grep -q "nautilus_http_requests_total"; then
            log_success "HTTP 请求指标存在"
        else
            log_warning "HTTP 请求指标缺失"
        fi

        if echo "$metrics" | grep -q "process_resident_memory_bytes"; then
            log_success "进程内存指标存在"
        else
            log_warning "进程内存指标缺失"
        fi
    else
        log_error "Nautilus API metrics 端点不可访问"
    fi
}

# 检查告警规则
check_alert_rules() {
    echo ""
    echo "=========================================="
    echo "6. Prometheus 告警规则检查"
    echo "=========================================="

    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，跳过详细检查"
        return
    fi

    rules=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null)

    if [ -z "$rules" ]; then
        log_error "无法获取告警规则"
        return
    fi

    rule_count=$(echo "$rules" | jq '[.data.groups[].rules[]] | length')

    if [ "$rule_count" -gt 0 ]; then
        log_success "已加载 ${rule_count} 条告警规则"

        # 检查是否有触发的告警
        firing=$(echo "$rules" | jq '[.data.groups[].rules[] | select(.state=="firing")] | length')
        if [ "$firing" -gt 0 ]; then
            log_warning "当前有 ${firing} 条告警触发"
        else
            log_success "当前无告警触发"
        fi
    else
        log_warning "未加载告警规则"
    fi
}

# 检查磁盘空间
check_disk_space() {
    echo ""
    echo "=========================================="
    echo "7. 磁盘空间检查"
    echo "=========================================="

    # 检查监控数据目录
    if [ -d "/home/ubuntu/monitoring" ]; then
        size=$(du -sh /home/ubuntu/monitoring 2>/dev/null | cut -f1)
        log_info "监控数据目录大小: ${size}"
    fi

    # 检查可用空间
    available=$(df -h / | awk 'NR==2 {print $4}')
    log_info "根分区可用空间: ${available}"

    # 检查 Docker 卷
    docker_volumes=$(docker volume ls --filter name=prometheus --filter name=grafana --format '{{.Name}}')
    if [ -n "$docker_volumes" ]; then
        log_success "Docker 卷已创建"
        echo "$docker_volumes" | while read -r vol; do
            echo "  - ${vol}"
        done
    fi
}

# 检查网络连接
check_network() {
    echo ""
    echo "=========================================="
    echo "8. 网络连接检查"
    echo "=========================================="

    ports=("9090:Prometheus" "3001:Grafana" "9093:AlertManager" "9100:Node Exporter" "8000:Nautilus API")

    for port_info in "${ports[@]}"; do
        IFS=':' read -r port name <<< "$port_info"
        if netstat -tuln 2>/dev/null | grep -q ":${port} " || ss -tuln 2>/dev/null | grep -q ":${port} "; then
            log_success "${name} 端口 ${port} 正在监听"
        else
            log_error "${name} 端口 ${port} 未监听"
        fi
    done
}

# 性能测试
performance_test() {
    echo ""
    echo "=========================================="
    echo "9. 性能测试"
    echo "=========================================="

    # 测试 Prometheus 查询响应时间
    start=$(date +%s%N)
    curl -s "http://localhost:9090/api/v1/query?query=up" > /dev/null 2>&1
    end=$(date +%s%N)
    duration=$(( (end - start) / 1000000 ))

    if [ $duration -lt 1000 ]; then
        log_success "Prometheus 查询响应时间: ${duration}ms"
    else
        log_warning "Prometheus 查询响应时间较慢: ${duration}ms"
    fi

    # 测试 Grafana 响应时间
    start=$(date +%s%N)
    curl -s http://localhost:3001/api/health > /dev/null 2>&1
    end=$(date +%s%N)
    duration=$(( (end - start) / 1000000 ))

    if [ $duration -lt 500 ]; then
        log_success "Grafana 响应时间: ${duration}ms"
    else
        log_warning "Grafana 响应时间较慢: ${duration}ms"
    fi

    # 测试 Nautilus Metrics 响应时间
    start=$(date +%s%N)
    curl -s http://localhost:8000/metrics > /dev/null 2>&1
    end=$(date +%s%N)
    duration=$(( (end - start) / 1000000 ))

    if [ $duration -lt 200 ]; then
        log_success "Nautilus Metrics 响应时间: ${duration}ms"
    else
        log_warning "Nautilus Metrics 响应时间较慢: ${duration}ms"
    fi
}

# 生成报告
generate_report() {
    echo ""
    echo "=========================================="
    echo "验证报告"
    echo "=========================================="
    echo ""
    echo "总计: $((PASSED + FAILED + WARNING)) 项检查"
    echo -e "${GREEN}通过: ${PASSED}${NC}"
    echo -e "${RED}失败: ${FAILED}${NC}"
    echo -e "${YELLOW}警告: ${WARNING}${NC}"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ 监控系统运行正常${NC}"
        exit 0
    else
        echo -e "${RED}✗ 监控系统存在问题，请检查失败项${NC}"
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

    echo ""
    echo "=========================================="
    echo "访问信息"
    echo "=========================================="
    echo ""
    echo "Prometheus:"
    echo "  http://localhost:9090"
    echo "  http://${SERVER_IP}:9090"
    echo ""
    echo "Grafana:"
    echo "  http://localhost:3001"
    echo "  http://${SERVER_IP}:3001"
    echo "  用户名: admin"
    echo "  密码: nautilus2024"
    echo ""
    echo "AlertManager:"
    echo "  http://localhost:9093"
    echo "  http://${SERVER_IP}:9093"
    echo ""
    echo "Node Exporter:"
    echo "  http://localhost:9100/metrics"
    echo ""
    echo "Nautilus Metrics:"
    echo "  http://localhost:8000/metrics"
    echo "  http://${SERVER_IP}:8000/metrics"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "Nautilus 监控系统验证"
    echo "=========================================="
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

    # 执行检查
    check_containers
    check_service_health
    check_prometheus_targets
    check_grafana_datasources
    check_nautilus_metrics
    check_alert_rules
    check_disk_space
    check_network
    performance_test

    # 显示访问信息
    show_access_info

    # 生成报告
    generate_report
}

# 执行主函数
main "$@"
