#!/bin/bash

################################################################################
# PostgreSQL 数据库恢复脚本
# 功能：全量恢复、时间点恢复(PITR)、恢复验证
################################################################################

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/nautilus}"
LOG_DIR="${LOG_DIR:-$BACKUP_ROOT/logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-nautilus}"
DB_USER="${DB_USER:-postgres}"
PGPASSWORD="${PGPASSWORD:-}"

# 恢复配置
RESTORE_TYPE="${RESTORE_TYPE:-full}"  # full, pitr
BACKUP_FILE="${BACKUP_FILE:-}"
TARGET_TIME="${TARGET_TIME:-}"  # PITR目标时间
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-true}"

# 安全配置
FORCE_RESTORE="${FORCE_RESTORE:-false}"
CREATE_BACKUP_BEFORE_RESTORE="${CREATE_BACKUP_BEFORE_RESTORE:-true}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# 日志函数
################################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"
}

################################################################################
# 初始化
################################################################################

init_restore() {
    log "初始化恢复环境..."

    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_ROOT/temp"

    # 检查依赖
    local deps=("psql" "pg_restore" "gunzip")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "缺少依赖: $dep"
            exit 1
        fi
    done

    # 检查数据库连接
    if ! PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1" &> /dev/null; then
        log_error "无法连接到数据库服务器"
        exit 1
    fi

    log_success "初始化完成"
}

################################################################################
# 安全确认
################################################################################

confirm_restore() {
    log_warning "=========================================="
    log_warning "警告：恢复操作将覆盖现有数据库"
    log_warning "数据库: $DB_NAME"
    log_warning "主机: $DB_HOST"
    log_warning "=========================================="

    if [[ "$FORCE_RESTORE" != "true" ]]; then
        read -p "确认继续恢复? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log "恢复已取消"
            exit 0
        fi
    fi

    log "恢复确认通过"
}

################################################################################
# 查找备份文件
################################################################################

find_backup_file() {
    log "查找备份文件..."

    if [[ -n "$BACKUP_FILE" ]] && [[ -f "$BACKUP_FILE" ]]; then
        log_success "使用指定备份: $BACKUP_FILE"
        echo "$BACKUP_FILE"
        return
    fi

    # 查找最新的全量备份
    local latest_backup=$(find "$BACKUP_ROOT/full" -type f \( -name "*.gz" -o -name "*.gz.enc" \) -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$latest_backup" ]]; then
        log_error "未找到备份文件"
        exit 1
    fi

    log_success "找到最新备份: $latest_backup"
    echo "$latest_backup"
}

################################################################################
# 验证备份文件
################################################################################

verify_backup_file() {
    local backup_file="$1"
    log "验证备份文件: $(basename $backup_file)"

    # 检查文件存在
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在"
        exit 1
    fi

    # 验证校验和
    local checksum_file="${backup_file}.sha256"
    if [[ -f "$checksum_file" ]]; then
        if sha256sum -c "$checksum_file" &> /dev/null; then
            log_success "校验和验证通过"
        else
            log_error "校验和验证失败"
            exit 1
        fi
    else
        log_warning "未找到校验和文件，跳过验证"
    fi

    # 显示备份信息
    local metadata_file="${backup_file}.meta.json"
    if [[ -f "$metadata_file" ]]; then
        log "备份信息:"
        jq -r '. | "  日期: \(.date)\n  大小: \(.file_size_human)\n  数据库: \(.database)\n  类型: \(.backup_type)"' "$metadata_file" | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"
    fi
}

################################################################################
# 解密备份
################################################################################

decrypt_backup() {
    local encrypted_file="$1"
    local decrypted_file="$BACKUP_ROOT/temp/decrypted_${TIMESTAMP}.sql.gz"

    log "解密备份文件..."

    if [[ -z "$ENCRYPTION_KEY" ]]; then
        log_error "未设置解密密钥"
        exit 1
    fi

    openssl enc -aes-256-cbc -d \
        -in "$encrypted_file" \
        -out "$decrypted_file" \
        -k "$ENCRYPTION_KEY" \
        -pbkdf2

    if [[ ! -f "$decrypted_file" ]]; then
        log_error "解密失败"
        exit 1
    fi

    log_success "解密完成"
    echo "$decrypted_file"
}

################################################################################
# 解压备份
################################################################################

decompress_backup() {
    local compressed_file="$1"
    local decompressed_file="$BACKUP_ROOT/temp/decompressed_${TIMESTAMP}.sql"

    log "解压备份文件..."

    gunzip -c "$compressed_file" > "$decompressed_file"

    if [[ ! -f "$decompressed_file" ]]; then
        log_error "解压失败"
        exit 1
    fi

    local size=$(du -h "$decompressed_file" | cut -f1)
    log_success "解压完成，大小: $size"
    echo "$decompressed_file"
}

################################################################################
# 备份当前数据库
################################################################################

backup_current_database() {
    if [[ "$CREATE_BACKUP_BEFORE_RESTORE" != "true" ]]; then
        return
    fi

    log "备份当前数据库..."

    local pre_restore_backup="$BACKUP_ROOT/full/pre_restore_${DB_NAME}_${TIMESTAMP}.sql.gz"

    # 检查数据库是否存在
    local db_exists=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | xargs)

    if [[ "$db_exists" == "1" ]]; then
        PGPASSWORD="$PGPASSWORD" pg_dump \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --format=plain \
            --no-owner \
            --no-acl | gzip > "$pre_restore_backup"

        if [[ -f "$pre_restore_backup" ]]; then
            log_success "当前数据库已备份: $pre_restore_backup"
        else
            log_warning "当前数据库备份失败"
        fi
    else
        log "数据库不存在，跳过备份"
    fi
}

################################################################################
# 终止数据库连接
################################################################################

terminate_connections() {
    log "终止数据库连接..."

    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
EOF

    log_success "连接已终止"
}

################################################################################
# 删除并重建数据库
################################################################################

recreate_database() {
    log "重建数据库..."

    # 终止连接
    terminate_connections

    # 删除数据库
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

    if [[ $? -ne 0 ]]; then
        log_error "删除数据库失败"
        exit 1
    fi

    log "数据库已删除"

    # 创建数据库
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

    if [[ $? -ne 0 ]]; then
        log_error "创建数据库失败"
        exit 1
    fi

    log_success "数据库已重建"
}

################################################################################
# 全量恢复
################################################################################

full_restore() {
    local backup_file="$1"
    log "开始全量恢复..."

    # 验证备份
    verify_backup_file "$backup_file"

    # 备份当前数据库
    backup_current_database

    # 准备恢复文件
    local restore_file="$backup_file"

    # 处理加密
    if [[ "$backup_file" == *.enc ]]; then
        restore_file=$(decrypt_backup "$backup_file")
    fi

    # 处理压缩
    if [[ "$restore_file" == *.gz ]]; then
        restore_file=$(decompress_backup "$restore_file")
    fi

    # 重建数据库
    recreate_database

    # 执行恢复
    log "恢复数据..."
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$restore_file" \
        2>&1 | tee -a "$LOG_DIR/restore_${DATE_ONLY}.log"

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        log_error "恢复失败"
        exit 1
    fi

    log_success "数据恢复完成"

    # 清理临时文件
    cleanup_temp_files

    # 验证恢复
    verify_restore
}

################################################################################
# 时间点恢复 (PITR)
################################################################################

pitr_restore() {
    log "开始时间点恢复 (PITR)..."

    if [[ -z "$TARGET_TIME" ]]; then
        log_error "未指定目标时间"
        exit 1
    fi

    log "目标时间: $TARGET_TIME"

    # 查找基础备份
    local base_backup=$(find_backup_file)
    log "基础备份: $base_backup"

    # 执行基础恢复
    full_restore "$base_backup"

    # 应用WAL日志
    log "应用WAL日志到目标时间..."

    local wal_dir="$BACKUP_ROOT/wal"
    if [[ ! -d "$wal_dir" ]] || [[ -z "$(ls -A $wal_dir 2>/dev/null)" ]]; then
        log_warning "未找到WAL归档，无法执行PITR"
        return
    fi

    # 配置恢复
    local recovery_conf="$BACKUP_ROOT/temp/recovery.conf"
    cat > "$recovery_conf" <<EOF
restore_command = 'cp $wal_dir/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

    log "恢复配置已创建"
    log_warning "PITR需要手动配置PostgreSQL恢复模式"
    log "请参考文档完成PITR配置"
}

################################################################################
# 验证恢复
################################################################################

verify_restore() {
    log "验证恢复结果..."

    # 检查数据库连接
    if ! PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        log_error "无法连接到恢复的数据库"
        return 1
    fi

    # 检查表数量
    local table_count=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    log "表数量: $table_count"

    if [[ $table_count -eq 0 ]]; then
        log_warning "未找到任何表"
    fi

    # 检查索引
    local index_count=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")
    log "索引数量: $index_count"

    # 检查约束
    local constraint_count=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'public';")
    log "约束数量: $constraint_count"

    # 数据库大小
    local db_size=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));")
    log "数据库大小: $db_size"

    log_success "恢复验证完成"
}

################################################################################
# 清理临时文件
################################################################################

cleanup_temp_files() {
    log "清理临时文件..."

    rm -rf "$BACKUP_ROOT/temp/"*

    log_success "临时文件已清理"
}

################################################################################
# 生成恢复报告
################################################################################

generate_report() {
    log "生成恢复报告..."

    local report_file="$LOG_DIR/restore_report_${TIMESTAMP}.txt"

    cat > "$report_file" <<EOF
================================================================================
PostgreSQL 数据库恢复报告
================================================================================
日期: $(date)
数据库: $DB_NAME
主机: $DB_HOST
恢复类型: $RESTORE_TYPE

恢复信息:
--------------------------------------------------------------------------------
备份文件: $BACKUP_FILE
恢复时间: $TIMESTAMP
EOF

    if [[ "$RESTORE_TYPE" == "pitr" ]]; then
        echo "目标时间: $TARGET_TIME" >> "$report_file"
    fi

    cat >> "$report_file" <<EOF

数据库状态:
--------------------------------------------------------------------------------
EOF

    # 添加数据库统计
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT
            'Tables: ' || COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'public';
    " -t >> "$report_file"

    cat >> "$report_file" <<EOF

================================================================================
EOF

    cat "$report_file"
    log_success "报告已生成: $report_file"
}

################################################################################
# 主函数
################################################################################

main() {
    log "========================================"
    log "PostgreSQL 数据库恢复脚本启动"
    log "========================================"

    # 初始化
    init_restore

    # 安全确认
    confirm_restore

    # 查找备份文件
    if [[ -z "$BACKUP_FILE" ]]; then
        BACKUP_FILE=$(find_backup_file)
    fi

    # 执行恢复
    case "$RESTORE_TYPE" in
        full)
            full_restore "$BACKUP_FILE"
            ;;
        pitr)
            pitr_restore
            ;;
        *)
            log_error "未知的恢复类型: $RESTORE_TYPE"
            exit 1
            ;;
    esac

    # 生成报告
    generate_report

    log_success "恢复流程完成"
}

# 执行主函数
main "$@"
