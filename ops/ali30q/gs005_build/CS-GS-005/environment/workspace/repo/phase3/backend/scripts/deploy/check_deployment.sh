#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 部署检查脚本
################################################################################
#
# 功能：
# - 服务健康检查
# - API可用性检查
# - 数据库连接检查
# - Redis连接检查
# - 区块链连接检查
# - 性能指标检查
#
# 使用方法：
#   ./check_deployment.sh [选项]
#
# 选项：
#   --host HOST          指定主机地址（默认：localhost）
#   --port PORT          指定端口（默认：8001）
#   --timeout SECONDS    超时时间（默认：30）
#   --verbose            详细输出
#   --json               JSON格式输出
#   --help               显示帮助信息
#
################################################################################

set -euo pipefail

# ============================================================================
# 配置变量
# ============================================================================

# 默认配置
HOST="${HOST:-localhost}"
PORT="${PORT:-8001}"
TIMEOUT="${TIMEOUT:-30}"
VERBOSE=false
JSON_OUTPUT=false

# 检查结果
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# 辅助函数
# ============================================================================

log_info() {
    if [[ "${JSON_OUTPUT}" == "false" ]]; then
        echo -e "${BLUE}[INFO]${NC} $@"
    fi
}

log_success() {
    if [[ "${JSON_OUTPUT}" == "false" ]]; then
        echo -e "${GREEN}[✓]${NC} $@"
    fi
}

log_warning() {
    if [[ "${JSON_OUTPUT}" == "false" ]]; then
        echo -e "${YELLOW}[⚠]${NC} $@"
    fi
}

log_error() {
    if [[ "${JSON_OUTPUT}" == "false" ]]; then
        echo -e "${RED}[✗]${NC} $@"
    fi
}

show_help() {
    cat << EOF
Nautilus Phase 3 Backend - 部署检查脚本

使用方法:
    $0 [选项]

选项:
    --host HOST          指定主机地址（默认：localhost）
    --port PORT          指定端口（默认：8001）
    --timeout SECONDS    超时时间（默认：30）
    --verbose            详细输出
    --json               JSON格式输出
    --help               显示此帮助信息

示例:
    # 检查本地部署
    $0

    # 检查远程服务器
    $0 --host production.example.com --port 8001

    # JSON格式输出
    $0 --json

EOF
    exit 0
}

# ============================================================================
# 检查函数
# ============================================================================

check_service_health() {
    log_info "检查服务健康状态..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local url="http://${HOST}:${PORT}/health"
    local response=$(curl -sf --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "")

    if [[ -n "${response}" ]]; then
        local status=$(echo "${response}" | jq -r '.status' 2>/dev/null || echo "")

        if [[ "${status}" == "healthy" ]]; then
            log_success "服务健康状态: ${status}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))

            if [[ "${VERBOSE}" == "true" ]]; then
                echo "${response}" | jq '.' 2>/dev/null || echo "${response}"
            fi
            return 0
        else
            log_error "服务健康状态异常: ${status}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        log_error "无法连接到健康检查端点: ${url}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_api_endpoints() {
    log_info "检查API端点..."

    local endpoints=(
        "/health"
        "/api/v1/status"
    )

    for endpoint in "${endpoints[@]}"; do
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        local url="http://${HOST}:${PORT}${endpoint}"

        if curl -sf --max-time "${TIMEOUT}" "${url}" > /dev/null 2>&1; then
            log_success "API端点可访问: ${endpoint}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            log_error "API端点不可访问: ${endpoint}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    done
}

check_database_connection() {
    log_info "检查数据库连接..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local url="http://${HOST}:${PORT}/health"
    local response=$(curl -sf --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "")

    if [[ -n "${response}" ]]; then
        local db_status=$(echo "${response}" | jq -r '.checks.database' 2>/dev/null || echo "")

        if [[ "${db_status}" == "ok" ]] || [[ "${db_status}" == "healthy" ]]; then
            log_success "数据库连接正常"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            log_error "数据库连接异常: ${db_status}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        log_warning "无法获取数据库状态"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        return 1
    fi
}

check_redis_connection() {
    log_info "检查Redis连接..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local url="http://${HOST}:${PORT}/health"
    local response=$(curl -sf --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "")

    if [[ -n "${response}" ]]; then
        local redis_status=$(echo "${response}" | jq -r '.checks.redis' 2>/dev/null || echo "")

        if [[ "${redis_status}" == "ok" ]] || [[ "${redis_status}" == "healthy" ]]; then
            log_success "Redis连接正常"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            log_error "Redis连接异常: ${redis_status}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        log_warning "无法获取Redis状态"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        return 1
    fi
}

check_blockchain_connection() {
    log_info "检查区块链连接..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local url="http://${HOST}:${PORT}/health"
    local response=$(curl -sf --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "")

    if [[ -n "${response}" ]]; then
        local blockchain_status=$(echo "${response}" | jq -r '.checks.blockchain' 2>/dev/null || echo "")

        if [[ "${blockchain_status}" == "ok" ]] || [[ "${blockchain_status}" == "healthy" ]]; then
            log_success "区块链连接正常"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            log_warning "区块链连接异常: ${blockchain_status}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            return 1
        fi
    else
        log_warning "无法获取区块链状态"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        return 1
    fi
}

check_docker_containers() {
    log_info "检查Docker容器状态..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker命令不可用，跳过容器检查"
        return 0
    fi

    local containers=("nexus-server-prod")

    for container in "${containers[@]}"; do
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local status=$(docker inspect --format='{{.State.Status}}' "${container}")
            local health=$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "none")

            if [[ "${status}" == "running" ]]; then
                if [[ "${health}" == "healthy" ]] || [[ "${health}" == "none" ]]; then
                    log_success "容器运行正常: ${container} (${status})"
                    PASSED_CHECKS=$((PASSED_CHECKS + 1))
                else
                    log_warning "容器健康检查异常: ${container} (${health})"
                    WARNING_CHECKS=$((WARNING_CHECKS + 1))
                fi
            else
                log_error "容器状态异常: ${container} (${status})"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
        else
            log_error "容器未运行: ${container}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    done
}

check_system_resources() {
    log_info "检查系统资源..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker命令不可用，跳过资源检查"
        return 0
    fi

    local container="nexus-server-prod"

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

        local stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemPerc}}" "${container}" 2>/dev/null || echo "")

        if [[ -n "${stats}" ]]; then
            local cpu=$(echo "${stats}" | cut -d',' -f1 | sed 's/%//')
            local mem=$(echo "${stats}" | cut -d',' -f2 | sed 's/%//')

            log_info "CPU使用率: ${cpu}%"
            log_info "内存使用率: ${mem}%"

            # 检查资源使用是否正常
            if (( $(echo "${cpu} < 90" | bc -l) )) && (( $(echo "${mem} < 90" | bc -l) )); then
                log_success "系统资源使用正常"
                PASSED_CHECKS=$((PASSED_CHECKS + 1))
            else
                log_warning "系统资源使用率较高 (CPU: ${cpu}%, MEM: ${mem}%)"
                WARNING_CHECKS=$((WARNING_CHECKS + 1))
            fi
        else
            log_warning "无法获取资源使用情况"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
    fi
}

check_logs_for_errors() {
    log_info "检查应用日志..."

    if ! command -v docker &> /dev/null; then
        log_warning "Docker命令不可用，跳过日志检查"
        return 0
    fi

    local container="nexus-server-prod"

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

        local error_count=$(docker logs --tail 100 "${container}" 2>&1 | grep -i "error" | wc -l)
        local warning_count=$(docker logs --tail 100 "${container}" 2>&1 | grep -i "warning" | wc -l)

        if [[ ${error_count} -eq 0 ]]; then
            log_success "日志中无错误信息"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        elif [[ ${error_count} -lt 5 ]]; then
            log_warning "日志中发现 ${error_count} 条错误信息"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        else
            log_error "日志中发现 ${error_count} 条错误信息"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi

        if [[ "${VERBOSE}" == "true" ]] && [[ ${error_count} -gt 0 ]]; then
            log_info "最近的错误日志:"
            docker logs --tail 100 "${container}" 2>&1 | grep -i "error" | tail -5
        fi
    fi
}

check_response_time() {
    log_info "检查响应时间..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local url="http://${HOST}:${PORT}/health"
    local start_time=$(date +%s%N)

    if curl -sf --max-time "${TIMEOUT}" "${url}" > /dev/null 2>&1; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))

        log_info "响应时间: ${response_time}ms"

        if [[ ${response_time} -lt 200 ]]; then
            log_success "响应时间正常 (< 200ms)"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        elif [[ ${response_time} -lt 500 ]]; then
            log_warning "响应时间较慢 (${response_time}ms)"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        else
            log_error "响应时间过慢 (${response_time}ms)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        log_error "无法测量响应时间"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# ============================================================================
# 输出函数
# ============================================================================

print_summary() {
    if [[ "${JSON_OUTPUT}" == "true" ]]; then
        cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "host": "${HOST}",
  "port": ${PORT},
  "total_checks": ${TOTAL_CHECKS},
  "passed": ${PASSED_CHECKS},
  "failed": ${FAILED_CHECKS},
  "warnings": ${WARNING_CHECKS},
  "success_rate": $(echo "scale=2; ${PASSED_CHECKS} * 100 / ${TOTAL_CHECKS}" | bc)
}
EOF
    else
        echo ""
        echo "=========================================="
        echo "部署检查摘要"
        echo "=========================================="
        echo "总检查项: ${TOTAL_CHECKS}"
        echo -e "${GREEN}通过: ${PASSED_CHECKS}${NC}"
        echo -e "${RED}失败: ${FAILED_CHECKS}${NC}"
        echo -e "${YELLOW}警告: ${WARNING_CHECKS}${NC}"
        echo "成功率: $(echo "scale=2; ${PASSED_CHECKS} * 100 / ${TOTAL_CHECKS}" | bc)%"
        echo "=========================================="

        if [[ ${FAILED_CHECKS} -eq 0 ]]; then
            echo -e "${GREEN}✓ 所有关键检查通过${NC}"
            exit 0
        else
            echo -e "${RED}✗ 存在失败的检查项${NC}"
            exit 1
        fi
    fi
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                HOST="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                echo "未知选项: $1"
                show_help
                ;;
        esac
    done

    if [[ "${JSON_OUTPUT}" == "false" ]]; then
        echo "=========================================="
        echo "Nautilus Phase 3 Backend 部署检查"
        echo "=========================================="
        echo "主机: ${HOST}"
        echo "端口: ${PORT}"
        echo "时间: $(date)"
        echo "=========================================="
        echo ""
    fi

    # 执行检查
    check_service_health
    check_api_endpoints
    check_database_connection
    check_redis_connection
    check_blockchain_connection
    check_docker_containers
    check_system_resources
    check_logs_for_errors
    check_response_time

    # 输出摘要
    print_summary
}

# 执行主函数
main "$@"
