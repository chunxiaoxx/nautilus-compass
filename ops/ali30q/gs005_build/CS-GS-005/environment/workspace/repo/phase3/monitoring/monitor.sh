#!/bin/bash
# 监控服务管理脚本

set -e

COMPOSE_FILE="docker-compose.monitoring.yml"

show_help() {
    cat << EOF
Nautilus 监控服务管理工具

用法: $0 [命令]

命令:
  start       启动所有监控服务
  stop        停止所有监控服务
  restart     重启所有监控服务
  status      查看服务状态
  logs        查看服务日志
  health      检查服务健康状态
  reload      重新加载配置（无需重启）
  clean       清理所有数据和容器
  help        显示此帮助信息

示例:
  $0 start              # 启动监控服务
  $0 logs prometheus    # 查看 Prometheus 日志
  $0 health             # 检查所有服务健康状态

EOF
}

check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "错误: $COMPOSE_FILE 不存在"
        exit 1
    fi
}

start_services() {
    echo "启动监控服务..."
    check_compose_file
    docker-compose -f "$COMPOSE_FILE" up -d
    echo "✓ 服务已启动"
    echo ""
    sleep 3
    check_health
}

stop_services() {
    echo "停止监控服务..."
    check_compose_file
    docker-compose -f "$COMPOSE_FILE" down
    echo "✓ 服务已停止"
}

restart_services() {
    echo "重启监控服务..."
    check_compose_file
    docker-compose -f "$COMPOSE_FILE" restart
    echo "✓ 服务已重启"
    echo ""
    sleep 3
    check_health
}

show_status() {
    echo "监控服务状态:"
    echo "-----------------------------------"
    check_compose_file
    docker-compose -f "$COMPOSE_FILE" ps
}

show_logs() {
    check_compose_file
    if [ -n "$1" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

check_health() {
    echo "检查服务健康状态:"
    echo "-----------------------------------"

    # Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo "✓ Prometheus (9090) - 运行正常"
    else
        echo "✗ Prometheus (9090) - 无法连接"
    fi

    # AlertManager
    if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
        echo "✓ AlertManager (9093) - 运行正常"
    else
        echo "✗ AlertManager (9093) - 无法连接"
    fi

    # Node Exporter
    if curl -s http://localhost:9100/metrics > /dev/null 2>&1; then
        echo "✓ Node Exporter (9100) - 运行正常"
    else
        echo "✗ Node Exporter (9100) - 无法连接"
    fi

    # Grafana
    if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
        echo "✓ Grafana (3001) - 运行正常"
    else
        echo "✗ Grafana (3001) - 无法连接"
    fi

    echo ""
    echo "告警规则加载状态:"
    RULES_COUNT=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | jq -r '.data.groups[].rules[] | select(.type=="alerting") | .name' | wc -l)
    if [ "$RULES_COUNT" -gt 0 ]; then
        echo "✓ 已加载 $RULES_COUNT 条告警规则"
    else
        echo "✗ 未检测到告警规则"
    fi

    echo ""
    echo "活跃告警:"
    ACTIVE_ALERTS=$(curl -s http://localhost:9090/api/v1/alerts 2>/dev/null | jq -r '.data.alerts[] | select(.state=="firing") | .labels.alertname' | wc -l)
    if [ "$ACTIVE_ALERTS" -gt 0 ]; then
        echo "⚠ 当前有 $ACTIVE_ALERTS 个活跃告警"
        curl -s http://localhost:9090/api/v1/alerts | jq -r '.data.alerts[] | select(.state=="firing") | "  - \(.labels.alertname) (\(.labels.priority)): \(.annotations.summary)"'
    else
        echo "✓ 无活跃告警"
    fi
}

reload_config() {
    echo "重新加载配置..."

    # 重新加载 Prometheus 配置
    if curl -s -X POST http://localhost:9090/-/reload > /dev/null 2>&1; then
        echo "✓ Prometheus 配置已重新加载"
    else
        echo "✗ Prometheus 配置重新加载失败"
    fi

    # 重新加载 AlertManager 配置
    if curl -s -X POST http://localhost:9093/-/reload > /dev/null 2>&1; then
        echo "✓ AlertManager 配置已重新加载"
    else
        echo "✗ AlertManager 配置重新加载失败"
    fi
}

clean_all() {
    echo "警告: 此操作将删除所有监控数据和容器"
    read -p "确认继续? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        echo "清理监控服务..."
        check_compose_file
        docker-compose -f "$COMPOSE_FILE" down -v
        echo "✓ 已清理所有数据和容器"
    else
        echo "已取消"
    fi
}

# 主逻辑
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    health)
        check_health
        ;;
    reload)
        reload_config
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "错误: 未知命令 '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
