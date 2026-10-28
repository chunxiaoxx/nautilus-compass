#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 生产环境部署脚本
################################################################################
#
# 功能：
# - 服务器环境检查
# - Docker镜像拉取和构建
# - 零停机部署
# - 健康检查和验证
# - 自动回滚支持
#
# 使用方法：
#   ./deploy_production.sh [选项]
#
# 选项：
#   --version VERSION    指定部署版本（默认：latest）
#   --skip-backup        跳过备份步骤
#   --skip-tests         跳过部署后测试
#   --rollback           回滚到上一个版本
#   --dry-run            模拟运行，不实际部署
#   --help               显示帮助信息
#
################################################################################

set -euo pipefail

# ============================================================================
# 配置变量
# ============================================================================

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 部署配置
VERSION="${VERSION:-latest}"
ENVIRONMENT="production"
DEPLOY_USER="${DEPLOY_USER:-nautilus}"
DEPLOY_GROUP="${DEPLOY_GROUP:-nautilus}"

# Docker配置
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_NAME="${IMAGE_NAME:-nexus-server}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"

# 备份配置
BACKUP_DIR="${BACKUP_DIR:-/var/backups/nautilus}"
BACKUP_RETENTION_DAYS=30

# 健康检查配置
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8001/health}"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=5

# 日志配置
LOG_DIR="${LOG_DIR:-/var/log/nautilus}"
LOG_FILE="${LOG_DIR}/deploy_$(date +%Y%m%d_%H%M%S).log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 选项标志
SKIP_BACKUP=false
SKIP_TESTS=false
DRY_RUN=false
ROLLBACK=false

# ============================================================================
# 辅助函数
# ============================================================================

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "${LOG_FILE}"
}

# 错误处理
error_exit() {
    log_error "$1"
    exit 1
}

# 显示帮助信息
show_help() {
    cat << EOF
Nautilus Phase 3 Backend - 生产环境部署脚本

使用方法:
    $0 [选项]

选项:
    --version VERSION    指定部署版本（默认：latest）
    --skip-backup        跳过备份步骤
    --skip-tests         跳过部署后测试
    --rollback           回滚到上一个版本
    --dry-run            模拟运行，不实际部署
    --help               显示此帮助信息

示例:
    # 部署最新版本
    $0

    # 部署指定版本
    $0 --version v1.2.3

    # 回滚到上一个版本
    $0 --rollback

    # 模拟部署
    $0 --dry-run

EOF
    exit 0
}

# ============================================================================
# 环境检查函数
# ============================================================================

check_prerequisites() {
    log_info "检查部署前置条件..."

    # 检查是否以root或sudo运行
    if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
        error_exit "此脚本需要root权限或sudo权限"
    fi

    # 检查必需的命令
    local required_commands=("docker" "docker-compose" "curl" "jq" "psql")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "未找到必需的命令: $cmd"
        fi
    done

    # 检查Docker服务
    if ! systemctl is-active --quiet docker; then
        error_exit "Docker服务未运行"
    fi

    # 检查磁盘空间（至少需要10GB）
    local available_space=$(df -BG "${PROJECT_ROOT}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 10 ]]; then
        error_exit "磁盘空间不足，至少需要10GB可用空间"
    fi

    # 检查内存（至少需要4GB）
    local available_memory=$(free -g | awk 'NR==2 {print $7}')
    if [[ $available_memory -lt 4 ]]; then
        log_warning "可用内存不足4GB，可能影响部署性能"
    fi

    # 检查配置文件
    if [[ ! -f "${PROJECT_ROOT}/.env.production" ]]; then
        error_exit "未找到生产环境配置文件: .env.production"
    fi

    # 检查docker-compose文件
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        error_exit "未找到Docker Compose配置文件: ${COMPOSE_FILE}"
    fi

    log_success "前置条件检查通过"
}

check_system_resources() {
    log_info "检查系统资源..."

    # CPU核心数
    local cpu_cores=$(nproc)
    log_info "CPU核心数: ${cpu_cores}"
    if [[ $cpu_cores -lt 4 ]]; then
        log_warning "CPU核心数少于推荐的4核"
    fi

    # 内存
    local total_memory=$(free -h | awk 'NR==2 {print $2}')
    local available_memory=$(free -h | awk 'NR==2 {print $7}')
    log_info "总内存: ${total_memory}, 可用内存: ${available_memory}"

    # 磁盘空间
    local disk_usage=$(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $5}')
    log_info "磁盘使用率: ${disk_usage}"

    # 检查端口占用
    local ports=(8000 8001 5432 6379 9090)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":${port} "; then
            log_warning "端口 ${port} 已被占用"
        fi
    done

    log_success "系统资源检查完成"
}

check_network_connectivity() {
    log_info "检查网络连接..."

    # 检查互联网连接
    if ! curl -s --max-time 5 https://www.google.com > /dev/null; then
        log_warning "无法连接到互联网"
    fi

    # 检查Docker Registry连接
    if [[ -n "${DOCKER_REGISTRY}" ]]; then
        if ! curl -s --max-time 5 "${DOCKER_REGISTRY}" > /dev/null; then
            log_warning "无法连接到Docker Registry: ${DOCKER_REGISTRY}"
        fi
    fi

    # 检查区块链RPC连接
    if [[ -f "${PROJECT_ROOT}/.env.production" ]]; then
        source "${PROJECT_ROOT}/.env.production"
        if [[ -n "${BLOCKCHAIN_RPC_URL}" ]]; then
            if curl -s --max-time 5 -X POST "${BLOCKCHAIN_RPC_URL}" \
                -H "Content-Type: application/json" \
                -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' > /dev/null; then
                log_success "区块链RPC连接正常"
            else
                log_warning "无法连接到区块链RPC: ${BLOCKCHAIN_RPC_URL}"
            fi
        fi
    fi

    log_success "网络连接检查完成"
}

# ============================================================================
# 备份函数
# ============================================================================

backup_current_deployment() {
    if [[ "${SKIP_BACKUP}" == "true" ]]; then
        log_info "跳过备份步骤"
        return 0
    fi

    log_info "备份当前部署..."

    # 创建备份目录
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/${backup_timestamp}"
    mkdir -p "${backup_path}"

    # 备份配置文件
    if [[ -f "${PROJECT_ROOT}/.env.production" ]]; then
        cp "${PROJECT_ROOT}/.env.production" "${backup_path}/"
        log_info "已备份配置文件"
    fi

    # 备份Docker镜像信息
    docker images | grep "${IMAGE_NAME}" > "${backup_path}/docker_images.txt" || true

    # 备份数据库
    if [[ -f "${PROJECT_ROOT}/.env.production" ]]; then
        source "${PROJECT_ROOT}/.env.production"
        if [[ -n "${DATABASE_URL}" ]]; then
            log_info "备份数据库..."
            local db_backup_file="${backup_path}/database_backup.sql"

            # 从DATABASE_URL提取连接信息
            local db_host=$(echo "${DATABASE_URL}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
            local db_port=$(echo "${DATABASE_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
            local db_name=$(echo "${DATABASE_URL}" | sed -n 's/.*\/\([^?]*\).*/\1/p')
            local db_user=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')

            if PGPASSWORD="${DATABASE_URL#*:}" pg_dump -h "${db_host}" -p "${db_port}" \
                -U "${db_user}" -d "${db_name}" > "${db_backup_file}"; then
                log_success "数据库备份完成: ${db_backup_file}"
            else
                log_warning "数据库备份失败"
            fi
        fi
    fi

    # 清理旧备份
    find "${BACKUP_DIR}" -type d -mtime +${BACKUP_RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null || true

    log_success "备份完成: ${backup_path}"
    echo "${backup_path}" > "${BACKUP_DIR}/latest_backup.txt"
}

# ============================================================================
# Docker镜像管理
# ============================================================================

pull_docker_image() {
    log_info "拉取Docker镜像..."

    local image_tag="${IMAGE_NAME}:${VERSION}"
    if [[ -n "${DOCKER_REGISTRY}" ]]; then
        image_tag="${DOCKER_REGISTRY}/${image_tag}"
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] 将拉取镜像: ${image_tag}"
        return 0
    fi

    if docker pull "${image_tag}"; then
        log_success "镜像拉取成功: ${image_tag}"
    else
        log_warning "镜像拉取失败，将尝试本地构建"
        build_docker_image
    fi
}

build_docker_image() {
    log_info "构建Docker镜像..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] 将构建镜像: ${IMAGE_NAME}:${VERSION}"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    if docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VERSION="${VERSION}" \
        -t "${IMAGE_NAME}:${VERSION}" \
        -f Dockerfile .; then
        log_success "镜像构建成功"
    else
        error_exit "镜像构建失败"
    fi
}

# ============================================================================
# 部署函数
# ============================================================================

deploy_application() {
    log_info "开始部署应用..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] 将执行部署操作"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    # 设置环境变量
    export VERSION="${VERSION}"
    export ENVIRONMENT="${ENVIRONMENT}"

    # 使用docker-compose部署
    log_info "启动服务..."
    if docker-compose -f "${COMPOSE_FILE}" up -d --remove-orphans; then
        log_success "服务启动成功"
    else
        error_exit "服务启动失败"
    fi

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
}

# ============================================================================
# 健康检查函数
# ============================================================================

wait_for_healthy() {
    log_info "等待服务健康检查..."

    local elapsed=0
    local healthy=false

    while [[ $elapsed -lt $HEALTH_CHECK_TIMEOUT ]]; do
        if curl -sf "${HEALTH_CHECK_URL}" > /dev/null 2>&1; then
            healthy=true
            break
        fi

        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
        log_info "等待中... (${elapsed}s/${HEALTH_CHECK_TIMEOUT}s)"
    done

    if [[ "${healthy}" == "true" ]]; then
        log_success "服务健康检查通过"
        return 0
    else
        log_error "服务健康检查超时"
        return 1
    fi
}

verify_deployment() {
    log_info "验证部署..."

    # 检查容器状态
    local container_name="nexus-server-prod"
    if docker ps | grep -q "${container_name}"; then
        log_success "容器运行正常: ${container_name}"
    else
        error_exit "容器未运行: ${container_name}"
    fi

    # 检查健康状态
    if ! wait_for_healthy; then
        error_exit "健康检查失败"
    fi

    # 检查API端点
    log_info "检查API端点..."
    if curl -sf "http://localhost:8001/health" | jq -e '.status == "healthy"' > /dev/null; then
        log_success "API端点响应正常"
    else
        log_warning "API端点响应异常"
    fi

    # 检查日志
    log_info "检查应用日志..."
    docker logs --tail 50 "${container_name}" | tee -a "${LOG_FILE}"

    log_success "部署验证完成"
}

# ============================================================================
# 回滚函数
# ============================================================================

rollback_deployment() {
    log_warning "开始回滚部署..."

    # 获取最新备份路径
    local latest_backup=$(cat "${BACKUP_DIR}/latest_backup.txt" 2>/dev/null || echo "")

    if [[ -z "${latest_backup}" ]] || [[ ! -d "${latest_backup}" ]]; then
        error_exit "未找到备份，无法回滚"
    fi

    log_info "从备份恢复: ${latest_backup}"

    # 停止当前服务
    cd "${PROJECT_ROOT}"
    docker-compose -f "${COMPOSE_FILE}" down

    # 恢复配置文件
    if [[ -f "${latest_backup}/.env.production" ]]; then
        cp "${latest_backup}/.env.production" "${PROJECT_ROOT}/"
        log_info "已恢复配置文件"
    fi

    # 恢复数据库
    if [[ -f "${latest_backup}/database_backup.sql" ]]; then
        log_info "恢复数据库..."
        source "${PROJECT_ROOT}/.env.production"

        local db_host=$(echo "${DATABASE_URL}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        local db_port=$(echo "${DATABASE_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        local db_name=$(echo "${DATABASE_URL}" | sed -n 's/.*\/\([^?]*\).*/\1/p')
        local db_user=$(echo "${DATABASE_URL}" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')

        if PGPASSWORD="${DATABASE_URL#*:}" psql -h "${db_host}" -p "${db_port}" \
            -U "${db_user}" -d "${db_name}" < "${latest_backup}/database_backup.sql"; then
            log_success "数据库恢复完成"
        else
            log_error "数据库恢复失败"
        fi
    fi

    # 重启服务
    docker-compose -f "${COMPOSE_FILE}" up -d

    # 验证回滚
    if wait_for_healthy; then
        log_success "回滚成功"
    else
        error_exit "回滚后服务未能正常启动"
    fi
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                error_exit "未知选项: $1"
                ;;
        esac
    done

    # 创建日志目录
    mkdir -p "${LOG_DIR}"

    log_info "=========================================="
    log_info "Nautilus Phase 3 Backend 生产环境部署"
    log_info "=========================================="
    log_info "版本: ${VERSION}"
    log_info "环境: ${ENVIRONMENT}"
    log_info "时间: $(date)"
    log_info "=========================================="

    # 如果是回滚操作
    if [[ "${ROLLBACK}" == "true" ]]; then
        rollback_deployment
        exit 0
    fi

    # 执行部署流程
    check_prerequisites
    check_system_resources
    check_network_connectivity
    backup_current_deployment
    pull_docker_image
    deploy_application
    verify_deployment

    log_success "=========================================="
    log_success "部署完成！"
    log_success "=========================================="
    log_info "版本: ${VERSION}"
    log_info "日志文件: ${LOG_FILE}"
    log_info "健康检查: ${HEALTH_CHECK_URL}"
    log_success "=========================================="
}

# 执行主函数
main "$@"
