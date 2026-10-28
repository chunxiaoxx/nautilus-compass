#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - 回滚脚本
#
# 功能：
# - 停止当前运行的服务
# - 恢复数据库备份
# - 可选：回滚到指定版本
#
# 使用方法：
#   ./rollback.sh [backup_file]
#   ./rollback.sh                    # 使用最新备份
#   ./rollback.sh nautilus_backup_20260226_120000.sql  # 使用指定备份
#
# 注意：
#   - 此脚本会停止当前服务
#   - 数据库将被恢复到备份时的状态
#   - 请确保备份文件存在且有效
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

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_warning "========================================="
log_warning "  Nautilus Phase 3 回滚操作"
log_warning "========================================="
echo ""

# 确认操作
read -p "此操作将停止服务并恢复数据库，是否继续？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_info "回滚操作已取消"
    exit 0
fi

################################################################################
# 1. 加载环境变量
################################################################################
log_info "步骤 1/5: 加载环境变量..."

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    log_success "环境变量加载完成"
else
    log_error ".env 文件不存在"
    exit 1
fi

# 检查 DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL 未设置"
    exit 1
fi

################################################################################
# 2. 停止服务
################################################################################
log_info "步骤 2/5: 停止服务..."

if [ -f "nautilus.pid" ]; then
    PID=$(cat nautilus.pid)

    if ps -p "$PID" > /dev/null 2>&1; then
        log_info "停止进程 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true

        # 等待进程结束
        WAIT_COUNT=0
        while ps -p "$PID" > /dev/null 2>&1 && [ $WAIT_COUNT -lt 10 ]; do
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done

        # 如果进程仍在运行，强制杀死
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "进程未响应，强制终止..."
            kill -9 "$PID" 2>/dev/null || true
            sleep 1
        fi

        log_success "服务已停止"
    else
        log_info "服务未运行"
    fi

    rm -f nautilus.pid
else
    log_info "未找到 PID 文件，服务可能未运行"
fi

# 额外检查：查找并停止所有相关进程
RUNNING_PROCESSES=$(ps aux | grep -E "uvicorn.*main:socket_app_with_fastapi|python.*main.py" | grep -v grep | awk '{print $2}')
if [ -n "$RUNNING_PROCESSES" ]; then
    log_warning "发现其他运行中的进程，正在停止..."
    echo "$RUNNING_PROCESSES" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

log_success "所有服务进程已停止"

################################################################################
# 3. 选择备份文件
################################################################################
log_info "步骤 3/5: 选择备份文件..."

BACKUP_DIR="$SCRIPT_DIR/backups"

if [ ! -d "$BACKUP_DIR" ]; then
    log_error "备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 如果指定了备份文件
if [ -n "$1" ]; then
    if [[ "$1" == /* ]]; then
        # 绝对路径
        BACKUP_FILE="$1"
    else
        # 相对路径或文件名
        if [ -f "$1" ]; then
            BACKUP_FILE="$1"
        elif [ -f "$BACKUP_DIR/$1" ]; then
            BACKUP_FILE="$BACKUP_DIR/$1"
        else
            log_error "备份文件不存在: $1"
            exit 1
        fi
    fi
else
    # 使用最新的备份
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/nautilus_backup_*.sql 2>/dev/null | head -n 1)

    if [ -z "$BACKUP_FILE" ]; then
        log_error "未找到备份文件"
        exit 1
    fi

    log_info "使用最新备份: $(basename "$BACKUP_FILE")"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

log_success "备份文件: $BACKUP_FILE"

# 显示备份文件信息
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_DATE=$(stat -c %y "$BACKUP_FILE" 2>/dev/null || stat -f "%Sm" "$BACKUP_FILE" 2>/dev/null || echo "未知")
log_info "备份大小: $BACKUP_SIZE"
log_info "备份时间: $BACKUP_DATE"

# 再次确认
echo ""
read -p "确认使用此备份恢复数据库？(yes/no): " CONFIRM_RESTORE
if [ "$CONFIRM_RESTORE" != "yes" ]; then
    log_info "回滚操作已取消"
    exit 0
fi

################################################################################
# 4. 恢复数据库
################################################################################
log_info "步骤 4/5: 恢复数据库..."

# 从 DATABASE_URL 提取连接信息
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"

    log_info "数据库: $DB_NAME@$DB_HOST:$DB_PORT"

    # 检查 psql 是否可用
    if ! command -v psql &> /dev/null; then
        log_error "psql 未安装，无法恢复数据库"
        exit 1
    fi

    # 创建当前状态的紧急备份
    EMERGENCY_BACKUP="$BACKUP_DIR/emergency_backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "创建紧急备份: $EMERGENCY_BACKUP"
    PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$EMERGENCY_BACKUP" 2>/dev/null || {
        log_warning "紧急备份失败，继续恢复..."
    }

    # 删除现有数据库并重新创建
    log_info "重建数据库..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || {
        log_error "无法删除数据库"
        exit 1
    }

    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
        log_error "无法创建数据库"
        exit 1
    }

    # 恢复备份
    log_info "恢复备份数据..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE" 2>/dev/null || {
        log_error "数据库恢复失败"

        # 尝试恢复紧急备份
        if [ -f "$EMERGENCY_BACKUP" ]; then
            log_warning "尝试恢复紧急备份..."
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$EMERGENCY_BACKUP" 2>/dev/null || true
        fi

        exit 1
    }

    log_success "数据库恢复完成"
else
    log_error "无法解析 DATABASE_URL"
    exit 1
fi

################################################################################
# 5. 验证恢复
################################################################################
log_info "步骤 5/5: 验证数据库恢复..."

# 检查表是否存在
TABLE_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)

if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 0 ]; then
    log_success "数据库验证通过，共 $TABLE_COUNT 个表"
else
    log_error "数据库验证失败"
    exit 1
fi

################################################################################
# 回滚完成
################################################################################
echo ""
log_success "========================================="
log_success "  回滚操作完成！"
log_success "========================================="
echo ""
log_info "数据库已恢复到: $(basename "$BACKUP_FILE")"
log_info "紧急备份保存在: $EMERGENCY_BACKUP"
echo ""
log_info "下一步操作："
log_info "  1. 检查数据库数据是否正确"
log_info "  2. 重新部署服务: ./deploy_blockchain.sh"
log_info "  3. 执行健康检查: curl http://localhost:8000/health"
echo ""
log_warning "注意：服务已停止，需要手动重新启动"
echo ""
