#!/bin/bash

# Nautilus Monitoring Deployment Script
# 部署 Prometheus + Grafana + AlertManager 监控系统
# 作者: DevOps Team
# 日期: 2026-03-02

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    log_info "检查 Docker 环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi

    log_success "Docker 环境检查通过"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    log_info "检查 Docker Compose 环境..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    log_success "Docker Compose 环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建监控数据目录..."

    # 创建数据目录
    mkdir -p /home/ubuntu/monitoring/prometheus/data
    mkdir -p /home/ubuntu/monitoring/grafana/data
    mkdir -p /home/ubuntu/monitoring/alertmanager/data

    # 设置权限（Grafana 需要 472:472）
    sudo chown -R 472:472 /home/ubuntu/monitoring/grafana/data 2>/dev/null || true

    log_success "目录创建完成"
}

# 停止现有的监控服务
stop_existing_services() {
    log_info "停止现有的监控服务..."

    # 停止容器
    docker stop nautilus-prometheus 2>/dev/null || true
    docker stop nautilus-grafana 2>/dev/null || true
    docker stop nautilus-alertmanager 2>/dev/null || true
    docker stop nautilus-node-exporter 2>/dev/null || true

    # 删除容器
    docker rm nautilus-prometheus 2>/dev/null || true
    docker rm nautilus-grafana 2>/dev/null || true
    docker rm nautilus-alertmanager 2>/dev/null || true
    docker rm nautilus-node-exporter 2>/dev/null || true

    log_success "现有服务已停止"
}

# 部署 Prometheus
deploy_prometheus() {
    log_info "部署 Prometheus..."

    # 复制配置文件
    sudo cp prometheus.yml /home/ubuntu/monitoring/prometheus/prometheus.yml
    sudo cp alerting_rules.yml /home/ubuntu/monitoring/prometheus/alerting_rules.yml
    sudo cp prometheus/alerts.production.yml /home/ubuntu/monitoring/prometheus/alerts.production.yml 2>/dev/null || true

    # 启动 Prometheus
    docker run -d \
        --name nautilus-prometheus \
        --restart=always \
        --network=host \
        -v /home/ubuntu/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
        -v /home/ubuntu/monitoring/prometheus/alerting_rules.yml:/etc/prometheus/alerting_rules.yml:ro \
        -v /home/ubuntu/monitoring/prometheus/alerts.production.yml:/etc/prometheus/alerts.production.yml:ro \
        -v /home/ubuntu/monitoring/prometheus/data:/prometheus \
        prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus \
        --storage.tsdb.retention.time=15d \
        --storage.tsdb.retention.size=10GB \
        --web.console.libraries=/usr/share/prometheus/console_libraries \
        --web.console.templates=/usr/share/prometheus/consoles \
        --web.enable-lifecycle

    log_success "Prometheus 部署完成"
}

# 部署 AlertManager
deploy_alertmanager() {
    log_info "部署 AlertManager..."

    # 复制配置文件
    sudo cp alertmanager.yml /home/ubuntu/monitoring/alertmanager/alertmanager.yml

    # 启动 AlertManager
    docker run -d \
        --name nautilus-alertmanager \
        --restart=always \
        --network=host \
        -v /home/ubuntu/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro \
        -v /home/ubuntu/monitoring/alertmanager/data:/alertmanager \
        prom/alertmanager:latest \
        --config.file=/etc/alertmanager/alertmanager.yml \
        --storage.path=/alertmanager

    log_success "AlertManager 部署完成"
}

# 部署 Node Exporter
deploy_node_exporter() {
    log_info "部署 Node Exporter..."

    # 启动 Node Exporter
    docker run -d \
        --name nautilus-node-exporter \
        --restart=always \
        --network=host \
        --pid=host \
        -v /proc:/host/proc:ro \
        -v /sys:/host/sys:ro \
        -v /:/rootfs:ro \
        prom/node-exporter:latest \
        --path.procfs=/host/proc \
        --path.sysfs=/host/sys \
        --path.rootfs=/rootfs \
        --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)'

    log_success "Node Exporter 部署完成"
}

# 部署 Grafana
deploy_grafana() {
    log_info "部署 Grafana..."

    # 创建 Grafana 配置目录
    sudo mkdir -p /home/ubuntu/monitoring/grafana/provisioning/datasources
    sudo mkdir -p /home/ubuntu/monitoring/grafana/provisioning/dashboards
    sudo mkdir -p /home/ubuntu/monitoring/grafana/dashboards

    # 复制配置文件
    sudo cp grafana/provisioning/datasources/prometheus.yml /home/ubuntu/monitoring/grafana/provisioning/datasources/
    sudo cp grafana/provisioning/dashboards/dashboards.yml /home/ubuntu/monitoring/grafana/provisioning/dashboards/
    sudo cp grafana/dashboards/*.json /home/ubuntu/monitoring/grafana/dashboards/ 2>/dev/null || true

    # 设置 Grafana 管理员密码
    GRAFANA_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-nautilus2024}"

    # 启动 Grafana
    docker run -d \
        --name nautilus-grafana \
        --restart=always \
        --network=host \
        -e "GF_SECURITY_ADMIN_USER=admin" \
        -e "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}" \
        -e "GF_SERVER_ROOT_URL=http://localhost:3001" \
        -e "GF_SERVER_HTTP_PORT=3001" \
        -e "GF_AUTH_ANONYMOUS_ENABLED=false" \
        -e "GF_LOG_MODE=console" \
        -e "GF_LOG_LEVEL=info" \
        -v /home/ubuntu/monitoring/grafana/data:/var/lib/grafana \
        -v /home/ubuntu/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro \
        -v /home/ubuntu/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro \
        grafana/grafana:latest

    log_success "Grafana 部署完成"
    log_info "Grafana 管理员密码: ${GRAFANA_PASSWORD}"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."

    # 等待 Prometheus
    for i in {1..30}; do
        if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
            log_success "Prometheus 已启动"
            break
        fi
        sleep 2
    done

    # 等待 Grafana
    for i in {1..30}; do
        if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
            log_success "Grafana 已启动"
            break
        fi
        sleep 2
    done

    # 等待 AlertManager
    for i in {1..30}; do
        if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
            log_success "AlertManager 已启动"
            break
        fi
        sleep 2
    done
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."

    echo ""
    echo "=========================================="
    echo "监控服务状态"
    echo "=========================================="

    # 检查 Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_success "✓ Prometheus: http://localhost:9090"
    else
        log_error "✗ Prometheus 未响应"
    fi

    # 检查 Grafana
    if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
        log_success "✓ Grafana: http://localhost:3001"
    else
        log_error "✗ Grafana 未响应"
    fi

    # 检查 AlertManager
    if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
        log_success "✓ AlertManager: http://localhost:9093"
    else
        log_error "✗ AlertManager 未响应"
    fi

    # 检查 Node Exporter
    if curl -s http://localhost:9100/metrics > /dev/null 2>&1; then
        log_success "✓ Node Exporter: http://localhost:9100"
    else
        log_error "✗ Node Exporter 未响应"
    fi

    # 检查 Nautilus Backend
    if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
        log_success "✓ Nautilus Backend: http://localhost:8000/metrics"
    else
        log_warning "⚠ Nautilus Backend 未响应（可能未启动）"
    fi

    echo ""
    echo "=========================================="
    echo "Docker 容器状态"
    echo "=========================================="
    docker ps --filter "name=nautilus-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo ""
}

# 显示访问信息
show_access_info() {
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

    echo ""
    echo "=========================================="
    echo "监控系统访问信息"
    echo "=========================================="
    echo ""
    echo "Prometheus:"
    echo "  - 本地: http://localhost:9090"
    echo "  - 外网: http://${SERVER_IP}:9090"
    echo ""
    echo "Grafana:"
    echo "  - 本地: http://localhost:3001"
    echo "  - 外网: http://${SERVER_IP}:3001"
    echo "  - 用户名: admin"
    echo "  - 密码: ${GRAFANA_ADMIN_PASSWORD:-nautilus2024}"
    echo ""
    echo "AlertManager:"
    echo "  - 本地: http://localhost:9093"
    echo "  - 外网: http://${SERVER_IP}:9093"
    echo ""
    echo "Node Exporter:"
    echo "  - 本地: http://localhost:9100/metrics"
    echo ""
    echo "Nautilus Metrics:"
    echo "  - 本地: http://localhost:8000/metrics"
    echo "  - 外网: http://${SERVER_IP}:8000/metrics"
    echo ""
    echo "=========================================="
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "Nautilus 监控系统部署"
    echo "=========================================="
    echo ""

    # 检查环境
    check_docker
    check_docker_compose

    # 创建目录
    create_directories

    # 停止现有服务
    stop_existing_services

    # 部署服务
    deploy_prometheus
    deploy_alertmanager
    deploy_node_exporter
    deploy_grafana

    # 等待服务启动
    wait_for_services

    # 验证部署
    verify_deployment

    # 显示访问信息
    show_access_info

    log_success "监控系统部署完成！"
    echo ""
}

# 执行主函数
main "$@"
