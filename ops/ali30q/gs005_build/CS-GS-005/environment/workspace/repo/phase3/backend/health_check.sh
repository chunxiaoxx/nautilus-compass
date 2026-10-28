#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 健康检查脚本
#
# 功能：
# - 检查 API 服务响应
# - 检查数据库连接
# - 检查 Redis 连接（如果配置）
# - 检查区块链连接（如果配置）
# - 生成详细的健康报告
#
# 使用方法：
#   ./health_check.sh [--verbose] [--json]
#
# 选项：
#   --verbose  显示详细信息
#   --json     以 JSON 格式输出
#
# 退出码：
#   0 - 所有检查通过
#   1 - 部分检查失败（降级状态）
#   2 - 关键检查失败（不健康状态）
################################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    if [ "$JSON_OUTPUT" != true ]; then
        echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

log_success() {
    if [ "$JSON_OUTPUT" != true ]; then
        echo -e "${GREEN}[✓]${NC} $1"
    fi
}

log_warning() {
    if [ "$JSON_OUTPUT" != true ]; then
        echo -e "${YELLOW}[⚠]${NC} $1"
    fi
}

log_error() {
    if [ "$JSON_OUTPUT" != true ]; then
        echo -e "${RED}[✗]${NC} $1"
    fi
}

# 解析命令行参数
VERBOSE=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            echo "使用方法: $0 [--verbose] [--json]"
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 健康检查结果
OVERALL_STATUS="healthy"
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_DEGRADED=0

# JSON 输出缓冲
JSON_CHECKS=""

################################################################################
# 辅助函数
################################################################################

# 添加检查结果
add_check_result() {
    local name="$1"
    local status="$2"
    local message="$3"
    local details="$4"

    if [ "$JSON_OUTPUT" = true ]; then
        if [ -n "$JSON_CHECKS" ]; then
            JSON_CHECKS="$JSON_CHECKS,"
        fi
        JSON_CHECKS="$JSON_CHECKS{\"name\":\"$name\",\"status\":\"$status\",\"message\":\"$message\""
        if [ -n "$details" ]; then
            JSON_CHECKS="$JSON_CHECKS,\"details\":$details"
        fi
        JSON_CHECKS="$JSON_CHECKS}"
    fi

    case $status in
        healthy)
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            ;;
        degraded)
            CHECKS_DEGRADED=$((CHECKS_DEGRADED + 1))
            if [ "$OVERALL_STATUS" = "healthy" ]; then
                OVERALL_STATUS="degraded"
            fi
            ;;
        unhealthy)
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            OVERALL_STATUS="unhealthy"
            ;;
    esac
}

################################################################################
# 1. 加载环境变量
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    log_info "开始健康检查..."
fi

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs 2>/dev/null)
fi

PORT=${PORT:-8000}
API_URL="http://localhost:$PORT"

################################################################################
# 2. 检查服务进程
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    log_info "检查 1/5: 服务进程状态"
fi

if [ -f "nautilus.pid" ]; then
    PID=$(cat nautilus.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        PROCESS_INFO=$(ps -p "$PID" -o pid,ppid,cmd,%cpu,%mem,etime 2>/dev/null | tail -n 1)
        log_success "服务进程运行中 (PID: $PID)"
        if [ "$VERBOSE" = true ]; then
            echo "  进程信息: $PROCESS_INFO"
        fi
        add_check_result "process" "healthy" "Service running" "{\"pid\":$PID}"
    else
        log_error "服务进程未运行 (PID 文件存在但进程不存在)"
        add_check_result "process" "unhealthy" "Process not running" "{}"
    fi
else
    # 尝试查找进程
    RUNNING_PID=$(ps aux | grep -E "uvicorn.*main:socket_app_with_fastapi" | grep -v grep | awk '{print $2}' | head -n 1)
    if [ -n "$RUNNING_PID" ]; then
        log_warning "服务运行中但 PID 文件不存在 (PID: $RUNNING_PID)"
        add_check_result "process" "degraded" "Running without PID file" "{\"pid\":$RUNNING_PID}"
    else
        log_error "服务未运行"
        add_check_result "process" "unhealthy" "Service not running" "{}"
    fi
fi

################################################################################
# 3. 检查 API 响应
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    log_info "检查 2/5: API 服务响应"
fi

# 检查根路径
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/" 2>/dev/null || echo "000")
ROOT_HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n 1)
ROOT_BODY=$(echo "$ROOT_RESPONSE" | head -n -1)

if [ "$ROOT_HTTP_CODE" = "200" ]; then
    log_success "API 根路径响应正常 (HTTP 200)"
    if [ "$VERBOSE" = true ]; then
        echo "$ROOT_BODY" | python3 -m json.tool 2>/dev/null || echo "$ROOT_BODY"
    fi
    add_check_result "api_root" "healthy" "API responding" "{\"http_code\":200}"
else
    log_error "API 根路径响应异常 (HTTP $ROOT_HTTP_CODE)"
    add_check_result "api_root" "unhealthy" "API not responding" "{\"http_code\":$ROOT_HTTP_CODE}"
fi

# 检查健康检查端点
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
HEALTH_HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    log_success "健康检查端点响应正常 (HTTP 200)"
    if [ "$VERBOSE" = true ]; then
        echo "$HEALTH_BODY" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_BODY"
    fi

    # 解析健康状态
    HEALTH_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        add_check_result "api_health" "healthy" "Health endpoint healthy" "{\"http_code\":200}"
    elif [ "$HEALTH_STATUS" = "degraded" ]; then
        log_warning "服务处于降级状态"
        add_check_result "api_health" "degraded" "Health endpoint degraded" "{\"http_code\":200}"
    else
        log_warning "健康状态未知: $HEALTH_STATUS"
        add_check_result "api_health" "degraded" "Health status unknown" "{\"http_code\":200}"
    fi
else
    log_error "健康检查端点响应异常 (HTTP $HEALTH_HTTP_CODE)"
    add_check_result "api_health" "unhealthy" "Health endpoint not responding" "{\"http_code\":$HEALTH_HTTP_CODE}"
fi

# 检查 API 文档
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/docs" 2>/dev/null || echo "000")
DOCS_HTTP_CODE=$(echo "$DOCS_RESPONSE" | tail -n 1)

if [ "$DOCS_HTTP_CODE" = "200" ]; then
    log_success "API 文档可访问 (HTTP 200)"
    add_check_result "api_docs" "healthy" "API docs accessible" "{\"http_code\":200}"
else
    log_warning "API 文档不可访问 (HTTP $DOCS_HTTP_CODE)"
    add_check_result "api_docs" "degraded" "API docs not accessible" "{\"http_code\":$DOCS_HTTP_CODE}"
fi

################################################################################
# 4. 检查数据库连接
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    log_info "检查 3/5: 数据库连接"
fi

if [ -n "$DATABASE_URL" ]; then
    # 从健康检查响应中提取数据库状态
    if [ "$HEALTH_HTTP_CODE" = "200" ]; then
        DB_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('checks', {}).get('database', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

        if [ "$DB_STATUS" = "healthy" ]; then
            log_success "数据库连接正常"
            add_check_result "database" "healthy" "Database connected" "{}"
        elif [ "$DB_STATUS" = "degraded" ]; then
            log_warning "数据库连接降级"
            add_check_result "database" "degraded" "Database degraded" "{}"
        else
            log_error "数据库连接失败"
            add_check_result "database" "unhealthy" "Database connection failed" "{}"
        fi
    else
        log_warning "无法从健康检查获取数据库状态"
        add_check_result "database" "degraded" "Cannot determine database status" "{}"
    fi
else
    log_warning "DATABASE_URL 未配置"
    add_check_result "database" "degraded" "DATABASE_URL not configured" "{}"
fi

################################################################################
# 5. 检查 Redis 连接
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    log_info "检查 4/5: Redis 连接"
fi

if [ -n "$REDIS_URL" ]; then
    # 从健康检查响应中提取 Redis 状态
    if [ "$HEALTH_HTTP_CODE" = "200" ]; then
        REDIS_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('checks', {}).get('redis', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

        if [ "$REDIS_STATUS" = "healthy" ]; then
            log_success "Redis 连接正常"
            add_check_result "redis" "healthy" "Redis connected" "{}"
        elif [ "$REDIS_STATUS" = "degraded" ]; then
            log_warning "Redis 连接降级"
            add_check_result "redis" "degraded" "Redis degraded" "{}"
        else
            log_warning "Redis 连接失败（可选服务）"
            add_check_result "redis" "degraded" "Redis connection failed" "{}"
        fi
    else
        log_warning "无法从健康检查获取 Redis 状态"
        add_check_result "redis" "degraded" "Cannot determine Redis status" "{}"
    fi
else
    log_info "Redis 未配置（可选）"
    add_check_result "redis" "healthy" "Redis not configured (optional)" "{}"
fi

################################################################################
# 6. 检查区块链连接
################################################################################
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    log_info "检查 5/5: 区块链连接"
fi

if [ -n "$INFURA_PROJECT_ID" ] || [ -n "$SEPOLIA_RPC_URL" ]; then
    # 从健康检查响应中提取区块链状态
    if [ "$HEALTH_HTTP_CODE" = "200" ]; then
        BLOCKCHAIN_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('checks', {}).get('blockchain', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

        if [ "$BLOCKCHAIN_STATUS" = "healthy" ]; then
            log_success "区块链连接正常"
            add_check_result "blockchain" "healthy" "Blockchain connected" "{}"
        elif [ "$BLOCKCHAIN_STATUS" = "degraded" ]; then
            log_warning "区块链连接降级"
            add_check_result "blockchain" "degraded" "Blockchain degraded" "{}"
        else
            log_warning "区块链连接失败（可选服务）"
            add_check_result "blockchain" "degraded" "Blockchain connection failed" "{}"
        fi
    else
        log_warning "无法从健康检查获取区块链状态"
        add_check_result "blockchain" "degraded" "Cannot determine blockchain status" "{}"
    fi
else
    log_info "区块链未配置（可选）"
    add_check_result "blockchain" "healthy" "Blockchain not configured (optional)" "{}"
fi

################################################################################
# 7. 生成报告
################################################################################
if [ "$JSON_OUTPUT" = true ]; then
    # JSON 格式输出
    echo "{\"status\":\"$OVERALL_STATUS\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"checks\":[$JSON_CHECKS],\"summary\":{\"passed\":$CHECKS_PASSED,\"degraded\":$CHECKS_DEGRADED,\"failed\":$CHECKS_FAILED}}"
else
    # 人类可读格式输出
    echo ""
    echo "========================================="
    echo "  健康检查报告"
    echo "========================================="
    echo ""
    echo "总体状态: $OVERALL_STATUS"
    echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "检查结果:"
    echo "  ✓ 通过: $CHECKS_PASSED"
    echo "  ⚠ 降级: $CHECKS_DEGRADED"
    echo "  ✗ 失败: $CHECKS_FAILED"
    echo ""

    if [ "$OVERALL_STATUS" = "healthy" ]; then
        log_success "所有检查通过，系统运行正常"
    elif [ "$OVERALL_STATUS" = "degraded" ]; then
        log_warning "部分检查失败，系统处于降级状态"
    else
        log_error "关键检查失败，系统不健康"
    fi

    echo ""
    echo "详细信息:"
    echo "  - API 地址: $API_URL"
    echo "  - API 文档: $API_URL/docs"
    echo "  - 健康检查: $API_URL/health"
    echo "  - 日志文件: logs/nautilus.log"
    echo ""
fi

################################################################################
# 退出码
################################################################################
if [ "$OVERALL_STATUS" = "healthy" ]; then
    exit 0
elif [ "$OVERALL_STATUS" = "degraded" ]; then
    exit 1
else
    exit 2
fi
