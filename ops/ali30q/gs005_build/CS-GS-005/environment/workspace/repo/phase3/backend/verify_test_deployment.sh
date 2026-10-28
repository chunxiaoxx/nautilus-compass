#!/bin/bash
# Nautilus Phase 3 Backend - 测试环境部署验证脚本
# 生成日期: 2026-02-26

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 检查计数器
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# 检查函数
check_pass() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    print_success "$1"
}

check_fail() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    print_error "$1"
}

check_warn() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
    print_warning "$1"
}

# 1. 检查配置文件
check_config_files() {
    print_header "1. 检查配置文件"

    if [ -f ".env.test" ]; then
        check_pass ".env.test 文件存在"

        # 检查文件权限
        if [ "$(uname)" != "MINGW64_NT"* ]; then
            PERMS=$(stat -c %a .env.test 2>/dev/null || stat -f %A .env.test 2>/dev/null || echo "unknown")
            if [ "$PERMS" = "600" ]; then
                check_pass ".env.test 文件权限正确 (600)"
            else
                check_warn ".env.test 文件权限为 $PERMS，建议设置为 600"
            fi
        fi
    else
        check_fail ".env.test 文件不存在"
    fi

    if [ -f "TEST_ENVIRONMENT_DEPLOYMENT_CHECKLIST.md" ]; then
        check_pass "部署检查清单文件存在"
    else
        check_fail "部署检查清单文件不存在"
    fi

    if [ -f "TEST_ENVIRONMENT_SETUP_GUIDE.md" ]; then
        check_pass "配置指南文件存在"
    else
        check_fail "配置指南文件不存在"
    fi

    if [ -f "TEST_ENVIRONMENT_DEPLOYMENT_REPORT.md" ]; then
        check_pass "部署报告文件存在"
    else
        check_fail "部署报告文件不存在"
    fi
}

# 2. 检查必需的环境变量
check_env_variables() {
    print_header "2. 检查环境变量配置"

    if [ ! -f ".env.test" ]; then
        check_fail "无法检查环境变量：.env.test 文件不存在"
        return
    fi

    # 必需的环境变量
    REQUIRED_VARS=(
        "ENVIRONMENT"
        "DATABASE_URL"
        "REDIS_URL"
        "JWT_SECRET_KEY"
        "CSRF_SECRET_KEY"
        "BLOCKCHAIN_NETWORK"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env.test; then
            VALUE=$(grep "^${var}=" .env.test | cut -d'=' -f2-)
            if [ -n "$VALUE" ] && [ "$VALUE" != "CHANGE_THIS" ] && [ "$VALUE" != "YOUR_" ]; then
                check_pass "$var 已配置"
            else
                check_warn "$var 存在但需要修改"
            fi
        else
            check_fail "$var 未配置"
        fi
    done

    # 检查是否使用了默认密钥
    if grep -q "CHANGE_THIS_IN_PRODUCTION" .env.test; then
        check_warn "发现默认密钥，请替换为实际密钥"
    else
        check_pass "未发现默认密钥"
    fi
}

# 3. 检查系统依赖
check_system_dependencies() {
    print_header "3. 检查系统依赖"

    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        check_pass "Python 已安装 (版本: $PYTHON_VERSION)"
    else
        check_fail "Python 未安装"
    fi

    # 检查 pip
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        check_pass "pip 已安装"
    else
        check_fail "pip 未安装"
    fi

    # 检查 PostgreSQL
    if command -v psql &> /dev/null; then
        PSQL_VERSION=$(psql --version | cut -d' ' -f3)
        check_pass "PostgreSQL 客户端已安装 (版本: $PSQL_VERSION)"
    else
        check_warn "PostgreSQL 客户端未安装（可能使用远程数据库）"
    fi

    # 检查 Redis
    if command -v redis-cli &> /dev/null; then
        REDIS_VERSION=$(redis-cli --version | cut -d' ' -f2)
        check_pass "Redis 客户端已安装 (版本: $REDIS_VERSION)"
    else
        check_warn "Redis 客户端未安装（可能使用远程 Redis）"
    fi

    # 检查 Docker (可选)
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        check_pass "Docker 已安装 (版本: $DOCKER_VERSION)"
    else
        check_warn "Docker 未安装（如使用 Docker 部署则需要安装）"
    fi

    # 检查 Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        check_pass "Git 已安装 (版本: $GIT_VERSION)"
    else
        check_warn "Git 未安装"
    fi
}

# 4. 检查 Python 依赖
check_python_dependencies() {
    print_header "4. 检查 Python 依赖"

    if [ -f "requirements.txt" ]; then
        check_pass "requirements.txt 文件存在"

        # 检查虚拟环境
        if [ -d "venv" ] || [ -n "$VIRTUAL_ENV" ]; then
            check_pass "Python 虚拟环境已创建"
        else
            check_warn "未检测到虚拟环境，建议创建虚拟环境"
        fi
    else
        check_fail "requirements.txt 文件不存在"
    fi
}

# 5. 检查目录结构
check_directory_structure() {
    print_header "5. 检查目录结构"

    # 检查日志目录
    if [ -d "/var/log/nautilus" ]; then
        check_pass "日志目录存在 (/var/log/nautilus)"

        # 检查写入权限
        if [ -w "/var/log/nautilus" ]; then
            check_pass "日志目录可写"
        else
            check_warn "日志目录不可写，可能需要调整权限"
        fi
    else
        check_warn "日志目录不存在 (/var/log/nautilus)，部署时需要创建"
    fi

    # 检查备份目录
    if [ -d "/var/backups/nautilus/test" ]; then
        check_pass "备份目录存在 (/var/backups/nautilus/test)"
    else
        check_warn "备份目录不存在，部署时需要创建"
    fi

    # 检查密钥目录
    if [ -d "keys" ]; then
        check_pass "密钥目录存在 (keys/)"

        # 检查目录权限
        if [ "$(uname)" != "MINGW64_NT"* ]; then
            PERMS=$(stat -c %a keys 2>/dev/null || stat -f %A keys 2>/dev/null || echo "unknown")
            if [ "$PERMS" = "700" ]; then
                check_pass "密钥目录权限正确 (700)"
            else
                check_warn "密钥目录权限为 $PERMS，建议设置为 700"
            fi
        fi
    else
        check_warn "密钥目录不存在，如使用加密文件方式需要创建"
    fi
}

# 6. 检查网络连接
check_network_connectivity() {
    print_header "6. 检查网络连接"

    # 检查 Infura 连接
    print_info "测试 Infura Sepolia RPC 连接..."
    if curl -s -X POST https://sepolia.infura.io/v3/test \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}' \
        --max-time 5 &> /dev/null; then
        check_pass "Infura Sepolia RPC 可访问"
    else
        check_warn "Infura Sepolia RPC 连接失败（可能需要配置 API Key）"
    fi

    # 检查本地端口
    if command -v netstat &> /dev/null || command -v ss &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
            check_warn "端口 8000 已被占用"
        else
            check_pass "端口 8000 可用"
        fi

        if netstat -tuln 2>/dev/null | grep -q ":8001 " || ss -tuln 2>/dev/null | grep -q ":8001 "; then
            check_warn "端口 8001 已被占用"
        else
            check_pass "端口 8001 可用"
        fi
    else
        check_warn "无法检查端口占用（netstat/ss 未安装）"
    fi
}

# 7. 检查数据库连接
check_database_connection() {
    print_header "7. 检查数据库连接"

    if [ ! -f ".env.test" ]; then
        check_warn "无法检查数据库连接：.env.test 文件不存在"
        return
    fi

    # 提取数据库连接信息
    DB_URL=$(grep "^DATABASE_URL=" .env.test | cut -d'=' -f2-)

    if [ -n "$DB_URL" ]; then
        print_info "数据库 URL: ${DB_URL:0:30}..."

        # 尝试使用 Python 测试连接
        if command -v python3 &> /dev/null; then
            python3 -c "
import sys
try:
    import psycopg2
    conn = psycopg2.connect('$DB_URL')
    conn.close()
    print('SUCCESS')
except ImportError:
    print('PSYCOPG2_NOT_INSTALLED')
except Exception as e:
    print(f'ERROR: {e}')
" > /tmp/db_check.txt 2>&1

            RESULT=$(cat /tmp/db_check.txt)
            if [ "$RESULT" = "SUCCESS" ]; then
                check_pass "数据库连接成功"
            elif [ "$RESULT" = "PSYCOPG2_NOT_INSTALLED" ]; then
                check_warn "psycopg2 未安装，无法测试数据库连接"
            else
                check_warn "数据库连接失败（可能数据库未启动或配置错误）"
            fi
            rm -f /tmp/db_check.txt
        else
            check_warn "无法测试数据库连接（Python 未安装）"
        fi
    else
        check_fail "DATABASE_URL 未配置"
    fi
}

# 8. 检查 Redis 连接
check_redis_connection() {
    print_header "8. 检查 Redis 连接"

    if [ ! -f ".env.test" ]; then
        check_warn "无法检查 Redis 连接：.env.test 文件不存在"
        return
    fi

    # 提取 Redis 连接信息
    REDIS_HOST=$(grep "^REDIS_HOST=" .env.test | cut -d'=' -f2-)
    REDIS_PORT=$(grep "^REDIS_PORT=" .env.test | cut -d'=' -f2-)
    REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" .env.test | cut -d'=' -f2-)

    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        print_info "Redis 服务器: $REDIS_HOST:$REDIS_PORT"

        if command -v redis-cli &> /dev/null; then
            if [ -n "$REDIS_PASSWORD" ]; then
                RESULT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning ping 2>&1)
            else
                RESULT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>&1)
            fi

            if [ "$RESULT" = "PONG" ]; then
                check_pass "Redis 连接成功"
            else
                check_warn "Redis 连接失败（可能 Redis 未启动或配置错误）"
            fi
        else
            check_warn "redis-cli 未安装，无法测试 Redis 连接"
        fi
    else
        check_fail "Redis 配置不完整"
    fi
}

# 9. 生成验证报告
generate_report() {
    print_header "验证报告摘要"

    echo -e "总检查项: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "通过: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "失败: ${RED}$FAILED_CHECKS${NC}"
    echo -e "警告: ${YELLOW}$WARNING_CHECKS${NC}"

    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        if [ $WARNING_CHECKS -eq 0 ]; then
            print_success "所有检查通过！可以开始部署。"
            return 0
        else
            print_warning "检查完成，有 $WARNING_CHECKS 个警告项，建议修复后再部署。"
            return 1
        fi
    else
        print_error "检查失败，有 $FAILED_CHECKS 个错误项，必须修复后才能部署。"
        return 2
    fi
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   Nautilus Phase 3 Backend - 测试环境部署验证脚本         ║"
    echo "║   生成日期: 2026-02-26                                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_config_files
    check_env_variables
    check_system_dependencies
    check_python_dependencies
    check_directory_structure
    check_network_connectivity
    check_database_connection
    check_redis_connection

    echo ""
    generate_report

    EXIT_CODE=$?

    echo ""
    print_info "详细的配置说明请参考："
    echo "  - TEST_ENVIRONMENT_SETUP_GUIDE.md"
    echo "  - TEST_ENVIRONMENT_DEPLOYMENT_CHECKLIST.md"
    echo "  - TEST_ENVIRONMENT_DEPLOYMENT_REPORT.md"

    exit $EXIT_CODE
}

# 运行主函数
main
