#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 完整部署脚本
#
# 功能：
# - 检查环境变量和依赖
# - 备份数据库
# - 安装Python依赖
# - 运行数据库迁移
# - 启动服务
# - 执行健康检查
#
# 使用方法：
#   ./deploy_blockchain.sh [--skip-backup] [--skip-deps] [--skip-migration]
#
# 环境变量要求：
#   DATABASE_URL - PostgreSQL连接字符串
#   REDIS_URL - Redis连接字符串
#   JWT_SECRET_KEY - JWT密钥
#   可选：INFURA_PROJECT_ID, BLOCKCHAIN_PRIVATE_KEY (区块链功能)
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
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 解析命令行参数
SKIP_BACKUP=false
SKIP_DEPS=false
SKIP_MIGRATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        *)
            log_error "未知参数: $1"
            echo "使用方法: $0 [--skip-backup] [--skip-deps] [--skip-migration]"
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "开始部署 Nautilus Phase 3 Backend..."
log_info "工作目录: $SCRIPT_DIR"

################################################################################
# 1. 检查环境变量
################################################################################
log_info "步骤 1/7: 检查环境变量..."

# 检测环境类型
if [ -f .env.production ] && [ "$ENVIRONMENT" = "production" ]; then
    ENV_FILE=".env.production"
    log_warning "检测到生产环境配置"
elif [ -f .env ]; then
    ENV_FILE=".env"
    log_info "使用开发环境配置"
else
    log_error "环境配置文件不存在！请从 .env.example 或 .env.production.example 复制并配置。"
    exit 1
fi

# 加载环境文件
log_info "加载环境配置: $ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

# 生产环境额外检查
if [ "$ENVIRONMENT" = "production" ]; then
    log_warning "========================================="
    log_warning "  生产环境部署 - 额外安全检查"
    log_warning "========================================="

    # 检查是否使用默认密钥
    if [[ "$JWT_SECRET_KEY" == *"CHANGE_THIS"* ]] || [[ "$CSRF_SECRET_KEY" == *"CHANGE_THIS"* ]]; then
        log_error "生产环境不能使用默认密钥！请修改 JWT_SECRET_KEY 和 CSRF_SECRET_KEY"
        exit 1
    fi

    # 检查HTTPS配置
    if [ "$FORCE_HTTPS" != "true" ]; then
        log_error "生产环境必须启用 FORCE_HTTPS=true"
        exit 1
    fi

    # 检查DEBUG模式
    if [ "$DEBUG" = "true" ]; then
        log_error "生产环境必须禁用 DEBUG=false"
        exit 1
    fi

    # 检查CORS配置
    if [[ "$ALLOWED_ORIGINS" == *"localhost"* ]]; then
        log_warning "警告: CORS配置包含localhost，这可能不适合生产环境"
        read -p "是否继续部署? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "部署已取消"
            exit 0
        fi
    fi

    # 检查数据库密码
    if [[ "$DATABASE_URL" == *"CHANGE_THIS"* ]]; then
        log_error "生产环境必须修改数据库密码"
        exit 1
    fi

    log_success "生产环境安全检查通过"
fi

# 检查必需的环境变量
REQUIRED_VARS=("DATABASE_URL" "JWT_SECRET_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    log_error "缺少必需的环境变量: ${MISSING_VARS[*]}"
    exit 1
fi

log_success "环境变量检查通过"

# 检查可选的区块链配置
if [ -n "$INFURA_PROJECT_ID" ] && [ -n "$BLOCKCHAIN_PRIVATE_KEY" ]; then
    log_info "检测到区块链配置，将启用区块链功能"
    BLOCKCHAIN_ENABLED=true
else
    log_warning "未配置区块链环境变量，将以非区块链模式运行"
    BLOCKCHAIN_ENABLED=false
fi

################################################################################
# 2. 检查系统依赖
################################################################################
log_info "步骤 2/7: 检查系统依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Python 版本: $PYTHON_VERSION"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 未安装"
    exit 1
fi

log_success "系统依赖检查通过"

################################################################################
# 3. 备份数据库
################################################################################
if [ "$SKIP_BACKUP" = false ]; then
    log_info "步骤 3/7: 备份数据库..."

    BACKUP_DIR="$SCRIPT_DIR/backups"
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/nautilus_backup_$TIMESTAMP.sql"

    # 生产环境备份验证
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warning "生产环境备份 - 执行额外验证"

        # 检查备份目录空间
        AVAILABLE_SPACE=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
        if [ "$AVAILABLE_SPACE" -lt 5 ]; then
            log_error "备份目录空间不足（少于5GB），请清理空间后重试"
            exit 1
        fi
        log_info "备份目录可用空间: ${AVAILABLE_SPACE}GB"
    fi

    # 从 DATABASE_URL 提取连接信息
    # 格式: postgresql://user:password@host:port/dbname
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        log_info "备份数据库: $DB_NAME@$DB_HOST:$DB_PORT"

        # 使用 pg_dump 备份
        if command -v pg_dump &> /dev/null; then
            PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || {
                if [ "$ENVIRONMENT" = "production" ]; then
                    log_error "生产环境数据库备份失败，部署终止"
                    exit 1
                else
                    log_warning "数据库备份失败（可能是数据库不存在或无法连接），继续部署..."
                fi
            }

            if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
                # 验证备份文件完整性
                BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
                if [ "$BACKUP_SIZE" -gt 100 ]; then
                    log_success "数据库备份完成: $BACKUP_FILE ($(numfmt --to=iec-i --suffix=B $BACKUP_SIZE 2>/dev/null || echo ${BACKUP_SIZE}B))"

                    # 生产环境创建备份校验和
                    if [ "$ENVIRONMENT" = "production" ]; then
                        sha256sum "$BACKUP_FILE" > "$BACKUP_FILE.sha256"
                        log_info "备份校验和已创建: $BACKUP_FILE.sha256"
                    fi
                else
                    log_error "备份文件太小，可能不完整"
                    if [ "$ENVIRONMENT" = "production" ]; then
                        exit 1
                    fi
                fi

                # 只保留最近的备份
                if [ "$ENVIRONMENT" = "production" ]; then
                    KEEP_BACKUPS=30  # 生产环境保留30个
                else
                    KEEP_BACKUPS=5   # 开发环境保留5个
                fi
                ls -t "$BACKUP_DIR"/nautilus_backup_*.sql | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm
                ls -t "$BACKUP_DIR"/nautilus_backup_*.sql.sha256 | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm 2>/dev/null || true
                log_info "清理旧备份，保留最近${KEEP_BACKUPS}个"
            fi
        else
            log_warning "pg_dump 未安装，跳过数据库备份"
            if [ "$ENVIRONMENT" = "production" ]; then
                log_error "生产环境必须安装 pg_dump"
                exit 1
            fi
        fi
    else
        log_warning "无法解析 DATABASE_URL，跳过数据库备份"
    fi
else
    log_info "步骤 3/7: 跳过数据库备份（--skip-backup）"
fi

################################################################################
# 4. 安装 Python 依赖
################################################################################
if [ "$SKIP_DEPS" = false ]; then
    log_info "步骤 4/7: 安装 Python 依赖..."

    if [ -f requirements.txt ]; then
        pip3 install -r requirements.txt --quiet || {
            log_error "依赖安装失败"
            exit 1
        }
        log_success "Python 依赖安装完成"
    else
        log_error "requirements.txt 不存在"
        exit 1
    fi
else
    log_info "步骤 4/7: 跳过依赖安装（--skip-deps）"
fi

################################################################################
# 5. 数据库迁移
################################################################################
if [ "$SKIP_MIGRATION" = false ]; then
    log_info "步骤 5/7: 执行数据库迁移..."

    # 检查是否使用 Alembic
    if [ -d "alembic" ] && [ -f "alembic.ini" ]; then
        log_info "使用 Alembic 进行数据库迁移..."

        # 检查 alembic 是否安装
        if command -v alembic &> /dev/null; then
            alembic upgrade head || {
                log_error "Alembic 迁移失败"
                exit 1
            }
            log_success "Alembic 迁移完成"
        else
            log_warning "Alembic 未安装，尝试使用初始化脚本..."
            python3 -c "from utils.database import init_db; init_db()" || {
                log_error "数据库初始化失败"
                exit 1
            }
            log_success "数据库初始化完成"
        fi
    else
        log_info "使用初始化脚本创建数据库表..."
        python3 -c "from utils.database import init_db; init_db()" || {
            log_error "数据库初始化失败"
            exit 1
        }
        log_success "数据库初始化完成"
    fi
else
    log_info "步骤 5/7: 跳过数据库迁移（--skip-migration）"
fi

################################################################################
# 6. 启动服务
################################################################################
log_info "步骤 6/7: 启动服务..."

# 检查是否已有进程在运行
if [ -f "nautilus.pid" ]; then
    OLD_PID=$(cat nautilus.pid)
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        log_warning "检测到已运行的进程 (PID: $OLD_PID)，正在停止..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2

        # 强制杀死
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            kill -9 "$OLD_PID" 2>/dev/null || true
            sleep 1
        fi
    fi
    rm -f nautilus.pid
fi

# 创建日志目录
mkdir -p logs

# 启动服务
log_info "启动 Nautilus Backend 服务..."
PORT=${PORT:-8000}

nohup python3 -m uvicorn main:socket_app_with_fastapi --host 0.0.0.0 --port "$PORT" > logs/nautilus.log 2>&1 &
SERVICE_PID=$!

echo "$SERVICE_PID" > nautilus.pid
log_success "服务已启动 (PID: $SERVICE_PID, Port: $PORT)"

# 等待服务启动
log_info "等待服务启动..."
sleep 5

################################################################################
# 7. 健康检查
################################################################################
log_info "步骤 7/7: 执行健康检查..."

MAX_RETRIES=10
RETRY_COUNT=0
HEALTH_CHECK_URL="http://localhost:$PORT/health"

# 生产环境使用HTTPS
if [ "$ENVIRONMENT" = "production" ] && [ "$FORCE_HTTPS" = "true" ]; then
    HEALTH_CHECK_URL="https://localhost:$PORT/health"
fi

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f -k "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        log_success "健康检查通过"

        # 获取详细健康状态
        HEALTH_RESPONSE=$(curl -s -k "$HEALTH_CHECK_URL")
        echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

        # 生产环境额外检查
        if [ "$ENVIRONMENT" = "production" ]; then
            log_info "执行生产环境额外健康检查..."

            # 检查数据库连接
            if echo "$HEALTH_RESPONSE" | grep -q '"database".*"healthy"'; then
                log_success "数据库连接正常"
            else
                log_error "数据库连接异常"
                exit 1
            fi

            # 检查Redis连接
            if echo "$HEALTH_RESPONSE" | grep -q '"redis".*"healthy"'; then
                log_success "Redis连接正常"
            else
                log_warning "Redis连接异常（非致命）"
            fi

            # 检查区块链连接
            if [ "$BLOCKCHAIN_ENABLED" = true ]; then
                if echo "$HEALTH_RESPONSE" | grep -q '"blockchain".*"healthy"'; then
                    log_success "区块链连接正常"
                else
                    log_warning "区块链连接异常"
                fi
            fi
        fi

        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warning "健康检查失败，重试 $RETRY_COUNT/$MAX_RETRIES..."
        sleep 3
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "健康检查失败，服务可能未正常启动"
    log_info "查看日志: tail -f logs/nautilus.log"

    # 生产环境自动回滚
    if [ "$ENVIRONMENT" = "production" ]; then
        log_error "生产环境健康检查失败，建议执行回滚"
        log_info "回滚命令: ./rollback.sh"
    fi

    exit 1
fi

################################################################################
# 部署完成
################################################################################
echo ""
log_success "========================================="
log_success "  Nautilus Phase 3 部署完成！"
log_success "========================================="
echo ""
log_info "服务信息:"
log_info "  - API 地址: http://localhost:$PORT"
log_info "  - API 文档: http://localhost:$PORT/docs"
log_info "  - 健康检查: http://localhost:$PORT/health"
log_info "  - 进程 PID: $SERVICE_PID"
log_info "  - 日志文件: logs/nautilus.log"
echo ""
log_info "常用命令:"
log_info "  - 查看日志: tail -f logs/nautilus.log"
log_info "  - 停止服务: kill $SERVICE_PID"
log_info "  - 重启服务: ./deploy_blockchain.sh"
log_info "  - 回滚部署: ./rollback.sh"
echo ""

if [ "$BLOCKCHAIN_ENABLED" = true ]; then
    log_info "区块链功能: 已启用"
else
    log_warning "区块链功能: 未启用（需配置 INFURA_PROJECT_ID 和 BLOCKCHAIN_PRIVATE_KEY）"
fi

echo ""
log_success "部署成功完成！"
