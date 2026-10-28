#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 配置验证脚本
################################################################################
#
# 功能：
# - 验证环境变量配置的完整性和正确性
# - 检查必需的配置项
# - 验证密钥强度
# - 检查网络连接
#
# 使用方法：
#   ./validate_config.sh [配置文件路径]
#
################################################################################

set -euo pipefail

# ============================================================================
# 配置变量
# ============================================================================

CONFIG_FILE="${1:-.env.production}"
ERRORS=0
WARNINGS=0
CHECKS=0

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
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $@"
    CHECKS=$((CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $@"
    WARNINGS=$((WARNINGS + 1))
    CHECKS=$((CHECKS + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $@"
    ERRORS=$((ERRORS + 1))
    CHECKS=$((CHECKS + 1))
}

# ============================================================================
# 验证函数
# ============================================================================

check_file_exists() {
    log_info "检查配置文件..."

    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log_error "配置文件不存在: ${CONFIG_FILE}"
        exit 1
    fi

    log_success "配置文件存在: ${CONFIG_FILE}"
}

load_config() {
    log_info "加载配置文件..."

    # 导出所有环境变量
    set -a
    source "${CONFIG_FILE}"
    set +a

    log_success "配置文件加载成功"
}

check_required_vars() {
    log_info "检查必需的环境变量..."

    local required_vars=(
        "ENVIRONMENT"
        "DATABASE_URL"
        "REDIS_URL"
        "JWT_SECRET_KEY"
        "CSRF_SECRET_KEY"
        "CORS_ORIGINS"
        "BLOCKCHAIN_NETWORK"
        "BLOCKCHAIN_RPC_URL"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "缺少必需的环境变量: ${var}"
        else
            log_success "环境变量已设置: ${var}"
        fi
    done
}

check_environment() {
    log_info "检查环境配置..."

    if [[ "${ENVIRONMENT}" != "production" ]]; then
        log_error "ENVIRONMENT 必须设置为 'production'"
    else
        log_success "环境设置正确: ${ENVIRONMENT}"
    fi

    if [[ "${DEBUG:-false}" != "false" ]]; then
        log_error "DEBUG 必须设置为 'false'"
    else
        log_success "调试模式已禁用"
    fi
}

check_secret_keys() {
    log_info "检查密钥强度..."

    # 检查JWT密钥
    if [[ "${JWT_SECRET_KEY}" == *"CHANGE_THIS"* ]]; then
        log_error "JWT_SECRET_KEY 仍使用默认值，必须修改"
    elif [[ ${#JWT_SECRET_KEY} -lt 32 ]]; then
        log_error "JWT_SECRET_KEY 长度不足（当前: ${#JWT_SECRET_KEY}，最小: 32）"
    elif [[ ${#JWT_SECRET_KEY} -lt 64 ]]; then
        log_warning "JWT_SECRET_KEY 长度建议至少64字符（当前: ${#JWT_SECRET_KEY}）"
    else
        log_success "JWT_SECRET_KEY 强度足够（长度: ${#JWT_SECRET_KEY}）"
    fi

    # 检查CSRF密钥
    if [[ "${CSRF_SECRET_KEY}" == *"CHANGE_THIS"* ]]; then
        log_error "CSRF_SECRET_KEY 仍使用默认值，必须修改"
    elif [[ ${#CSRF_SECRET_KEY} -lt 32 ]]; then
        log_error "CSRF_SECRET_KEY 长度不足（当前: ${#CSRF_SECRET_KEY}，最小: 32）"
    else
        log_success "CSRF_SECRET_KEY 强度足够（长度: ${#CSRF_SECRET_KEY}）"
    fi

    # 检查密钥是否相同
    if [[ "${JWT_SECRET_KEY}" == "${CSRF_SECRET_KEY}" ]]; then
        log_error "JWT_SECRET_KEY 和 CSRF_SECRET_KEY 不能相同"
    else
        log_success "JWT和CSRF密钥不同"
    fi
}

check_database_config() {
    log_info "检查数据库配置..."

    # 检查DATABASE_URL格式
    if [[ ! "${DATABASE_URL}" =~ ^postgresql:// ]]; then
        log_error "DATABASE_URL 格式不正确，必须以 postgresql:// 开头"
    else
        log_success "DATABASE_URL 格式正确"
    fi

    # 检查是否使用默认密码
    if [[ "${DATABASE_URL}" == *"CHANGE_THIS"* ]]; then
        log_error "DATABASE_URL 仍使用默认密码，必须修改"
    else
        log_success "数据库密码已修改"
    fi

    # 检查连接池配置
    if [[ ${DB_POOL_SIZE:-20} -lt 10 ]]; then
        log_warning "DB_POOL_SIZE 可能过小（当前: ${DB_POOL_SIZE:-20}）"
    else
        log_success "数据库连接池配置合理"
    fi
}

check_redis_config() {
    log_info "检查Redis配置..."

    # 检查REDIS_URL格式
    if [[ ! "${REDIS_URL}" =~ ^redis:// ]]; then
        log_error "REDIS_URL 格式不正确，必须以 redis:// 开头"
    else
        log_success "REDIS_URL 格式正确"
    fi

    # 检查是否使用默认密码
    if [[ "${REDIS_PASSWORD:-}" == *"CHANGE_THIS"* ]]; then
        log_error "REDIS_PASSWORD 仍使用默认值，必须修改"
    elif [[ -z "${REDIS_PASSWORD:-}" ]]; then
        log_warning "未设置 REDIS_PASSWORD，建议设置密码"
    else
        log_success "Redis密码已设置"
    fi
}

check_cors_config() {
    log_info "检查CORS配置..."

    # 检查是否使用通配符
    if [[ "${CORS_ORIGINS}" == *"*"* ]]; then
        log_error "CORS_ORIGINS 不应使用通配符 *"
    else
        log_success "CORS配置不包含通配符"
    fi

    # 检查是否使用HTTPS
    if [[ "${CORS_ORIGINS}" == *"http://"* ]] && [[ "${CORS_ORIGINS}" != *"localhost"* ]]; then
        log_warning "CORS_ORIGINS 包含HTTP域名，生产环境应使用HTTPS"
    else
        log_success "CORS域名使用HTTPS"
    fi

    # 检查是否修改了默认域名
    if [[ "${CORS_ORIGINS}" == *"yourdomain.com"* ]]; then
        log_error "CORS_ORIGINS 仍使用示例域名，必须修改为实际域名"
    else
        log_success "CORS域名已修改"
    fi
}

check_https_config() {
    log_info "检查HTTPS配置..."

    if [[ "${FORCE_HTTPS:-true}" != "true" ]]; then
        log_error "FORCE_HTTPS 必须设置为 true"
    else
        log_success "强制HTTPS已启用"
    fi

    if [[ "${HSTS_MAX_AGE:-31536000}" -lt 31536000 ]]; then
        log_warning "HSTS_MAX_AGE 建议设置为至少1年（31536000秒）"
    else
        log_success "HSTS配置正确"
    fi
}

check_blockchain_config() {
    log_info "检查区块链配置..."

    # 检查网络配置
    if [[ "${BLOCKCHAIN_NETWORK}" != "mainnet" ]] && [[ "${BLOCKCHAIN_NETWORK}" != "sepolia" ]]; then
        log_error "BLOCKCHAIN_NETWORK 必须是 mainnet 或 sepolia"
    else
        log_success "区块链网络配置正确: ${BLOCKCHAIN_NETWORK}"
    fi

    # 检查RPC URL
    if [[ "${BLOCKCHAIN_RPC_URL}" == *"YOUR_"* ]]; then
        log_error "BLOCKCHAIN_RPC_URL 仍使用占位符，必须修改"
    else
        log_success "区块链RPC URL已配置"
    fi

    # 检查智能合约地址
    local contracts=(
        "IDENTITY_CONTRACT_ADDRESS"
        "TASK_CONTRACT_ADDRESS"
        "REWARD_CONTRACT_ADDRESS"
    )

    for contract in "${contracts[@]}"; do
        if [[ "${!contract:-}" == "0x0000000000000000000000000000000000000000" ]]; then
            log_warning "智能合约地址未配置: ${contract}"
        elif [[ -z "${!contract:-}" ]]; then
            log_error "智能合约地址缺失: ${contract}"
        else
            log_success "智能合约地址已配置: ${contract}"
        fi
    done

    # 检查私钥管理
    if [[ -n "${BLOCKCHAIN_PRIVATE_KEY:-}" ]]; then
        log_warning "不建议在环境变量中直接存储私钥，建议使用密钥管理服务"
    fi

    if [[ "${KEY_SOURCE:-}" == "encrypted_file" ]]; then
        if [[ -z "${KEY_FILE_PATH:-}" ]]; then
            log_error "KEY_SOURCE 设置为 encrypted_file 但未设置 KEY_FILE_PATH"
        elif [[ "${KEY_ENCRYPTION_PASSWORD:-}" == *"CHANGE_THIS"* ]]; then
            log_error "KEY_ENCRYPTION_PASSWORD 仍使用默认值，必须修改"
        else
            log_success "密钥管理配置正确"
        fi
    fi
}

check_security_config() {
    log_info "检查安全配置..."

    # 检查速率限制
    if [[ "${RATE_LIMIT_ENABLED:-true}" != "true" ]]; then
        log_error "RATE_LIMIT_ENABLED 必须设置为 true"
    else
        log_success "速率限制已启用"
    fi

    # 检查API文档
    if [[ "${ENABLE_API_DOCS:-false}" != "false" ]]; then
        log_error "ENABLE_API_DOCS 必须设置为 false"
    else
        log_success "API文档已禁用"
    fi

    if [[ "${ENABLE_SWAGGER:-false}" != "false" ]]; then
        log_error "ENABLE_SWAGGER 必须设置为 false"
    else
        log_success "Swagger UI已禁用"
    fi

    # 检查密码策略
    if [[ ${PASSWORD_MIN_LENGTH:-12} -lt 12 ]]; then
        log_warning "PASSWORD_MIN_LENGTH 建议至少12字符"
    else
        log_success "密码策略配置合理"
    fi
}

check_monitoring_config() {
    log_info "检查监控配置..."

    if [[ "${PROMETHEUS_ENABLED:-true}" != "true" ]]; then
        log_warning "建议启用Prometheus监控"
    else
        log_success "Prometheus监控已启用"
    fi

    if [[ "${AUDIT_LOG_ENABLED:-true}" != "true" ]]; then
        log_warning "建议启用审计日志"
    else
        log_success "审计日志已启用"
    fi
}

check_network_connectivity() {
    log_info "检查网络连接..."

    # 检查RPC连接
    if command -v curl &> /dev/null; then
        if curl -sf --max-time 5 "${BLOCKCHAIN_RPC_URL}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' > /dev/null 2>&1; then
            log_success "区块链RPC连接正常"
        else
            log_warning "无法连接到区块链RPC: ${BLOCKCHAIN_RPC_URL}"
        fi
    else
        log_warning "curl未安装，跳过网络连接检查"
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "配置验证摘要"
    echo "=========================================="
    echo "总检查项: ${CHECKS}"
    echo -e "${GREEN}成功: $((CHECKS - ERRORS - WARNINGS))${NC}"
    echo -e "${YELLOW}警告: ${WARNINGS}${NC}"
    echo -e "${RED}错误: ${ERRORS}${NC}"
    echo "=========================================="

    if [[ ${ERRORS} -eq 0 ]] && [[ ${WARNINGS} -eq 0 ]]; then
        echo -e "${GREEN}✓ 配置验证通过，可以部署${NC}"
        exit 0
    elif [[ ${ERRORS} -eq 0 ]]; then
        echo -e "${YELLOW}⚠ 配置验证通过但有警告，建议修复后部署${NC}"
        exit 0
    else
        echo -e "${RED}✗ 配置验证失败，请修复错误后重试${NC}"
        exit 1
    fi
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    echo "=========================================="
    echo "Nautilus Phase 3 Backend 配置验证"
    echo "=========================================="
    echo "配置文件: ${CONFIG_FILE}"
    echo "时间: $(date)"
    echo "=========================================="
    echo ""

    check_file_exists
    load_config
    check_required_vars
    check_environment
    check_secret_keys
    check_database_config
    check_redis_config
    check_cors_config
    check_https_config
    check_blockchain_config
    check_security_config
    check_monitoring_config
    check_network_connectivity

    print_summary
}

# 执行主函数
main
