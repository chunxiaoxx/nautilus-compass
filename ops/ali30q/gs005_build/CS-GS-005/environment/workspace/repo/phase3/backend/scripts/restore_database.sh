#!/bin/bash
# ============================================================================
# 数据库恢复测试脚本
# ============================================================================
# 功能: 测试数据库恢复流程，确保备份可用
# 版本: 1.0.0
# 创建日期: 2026-02-27
# ============================================================================

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错

# ============================================================================
# 颜色输出
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# 日志函数
# ============================================================================
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

# ============================================================================
# 配置变量
# ============================================================================
BACKUP_FILE="${BACKUP_FILE:-}"
TARGET_DB_NAME="${TARGET_DB_NAME:-}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
RESTORE_MODE="${RESTORE_MODE:-create}"  # create, replace, or merge

# ============================================================================
# 显示使用帮助
# ============================================================================
show_usage() {
    cat <<EOF
用法: $0 <backup_file> <target_database> [选项]

参数:
    backup_file             备份文件路径
    target_database         目标数据库名称

选项:
    -m, --mode MODE         恢复模式: create, replace, merge (默认: create)
                            create: 创建新数据库
                            replace: 删除并重建数据库
                            merge: 合并到现有数据库
    -u, --user USER         数据库用户 (默认: postgres)
    -h, --host HOST         数据库主机 (默认: localhost)
    -p, --port PORT         数据库端口 (默认: 5432)
    --help                  显示此帮助信息

示例:
    # 创建新数据库并恢复
    $0 backup.sql.gz nautilus_restored

    # 替换现有数据库
    $0 backup.sql.gz nautilus_production --mode replace

    # 合并到现有数据库
    $0 backup.sql.gz nautilus_production --mode merge
EOF
}

# ============================================================================
# 检查备份文件
# ============================================================================
check_backup_file() {
    log_info "检查备份文件: $BACKUP_FILE"

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi

    local file_size=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
    log_info "文件大小: $(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "$file_size bytes")"

    log_success "备份文件检查通过"
}

# ============================================================================
# 检查数据库是否存在
# ============================================================================
database_exists() {
    local db_name="$1"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$db_name"
}

# ============================================================================
# 创建数据库
# ============================================================================
create_database() {
    log_info "创建数据库: $TARGET_DB_NAME"

    if database_exists "$TARGET_DB_NAME"; then
        log_error "数据库已存在: $TARGET_DB_NAME"
        log_info "使用 --mode replace 来替换现有数据库"
        exit 1
    fi

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE DATABASE $TARGET_DB_NAME
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
EOF

    log_success "数据库创建成功"
}

# ============================================================================
# 删除数据库
# ============================================================================
drop_database() {
    log_warning "删除数据库: $TARGET_DB_NAME"

    # 断开所有连接
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$TARGET_DB_NAME'
AND pid <> pg_backend_pid();
EOF

    # 删除数据库
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS $TARGET_DB_NAME;"

    log_success "数据库已删除"
}

# ============================================================================
# 备份现有数据库
# ============================================================================
backup_existing_database() {
    log_info "备份现有数据库..."

    local backup_dir="/var/backups/postgresql/pre_restore"
    local backup_file="${backup_dir}/${TARGET_DB_NAME}_pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"

    mkdir -p "$backup_dir"

    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" | gzip > "$backup_file"

    log_success "现有数据库已备份: $backup_file"
}

# ============================================================================
# 恢复备份
# ============================================================================
restore_backup() {
    log_info "开始恢复备份到: $TARGET_DB_NAME"

    local start_time=$(date +%s)

    # 根据文件类型选择恢复方法
    if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
        log_info "使用 SQL 格式恢复..."
        gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME"
    elif [[ "$BACKUP_FILE" == *.sql ]]; then
        log_info "使用未压缩 SQL 格式恢复..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -f "$BACKUP_FILE"
    elif [[ "$BACKUP_FILE" == *.dump ]] || [[ "$BACKUP_FILE" == *.custom ]]; then
        log_info "使用 custom 格式恢复..."
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -v "$BACKUP_FILE"
    else
        log_error "不支持的备份文件格式"
        exit 1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "恢复耗时: ${duration}秒"

    log_success "备份恢复完成"
}

# ============================================================================
# 验证恢复结果
# ============================================================================
verify_restore() {
    log_info "验证恢复结果..."

    # 检查连接
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_error "无法连接到数据库"
        return 1
    fi

    # 统计信息
    log_info "数据库统计信息:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" <<EOF
-- 表数量
SELECT 'Tables' as type, COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
UNION ALL
-- 索引数量
SELECT 'Indexes', COUNT(*)
FROM pg_indexes
WHERE schemaname = 'public'
UNION ALL
-- 序列数量
SELECT 'Sequences', COUNT(*)
FROM information_schema.sequences
WHERE sequence_schema = 'public'
UNION ALL
-- 视图数量
SELECT 'Views', COUNT(*)
FROM information_schema.views
WHERE table_schema = 'public';

-- 数据库大小
SELECT
    pg_size_pretty(pg_database_size('$TARGET_DB_NAME')) as database_size;

-- 前10个最大的表
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF

    log_success "验证完成"
}

# ============================================================================
# 更新序列值
# ============================================================================
update_sequences() {
    log_info "更新序列值..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" <<'EOF'
DO $$
DECLARE
    seq_record RECORD;
    max_val BIGINT;
    seq_val BIGINT;
BEGIN
    FOR seq_record IN
        SELECT
            sequence_schema,
            sequence_name,
            REPLACE(REPLACE(sequence_name, '_id_seq', ''), '_seq', '') as table_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        BEGIN
            EXECUTE format('SELECT COALESCE(MAX(id), 0) FROM %I.%I',
                seq_record.sequence_schema,
                seq_record.table_name
            ) INTO max_val;

            EXECUTE format('SELECT last_value FROM %I.%I',
                seq_record.sequence_schema,
                seq_record.sequence_name
            ) INTO seq_val;

            IF max_val > seq_val THEN
                EXECUTE format('SELECT setval(%L, %s)',
                    seq_record.sequence_schema || '.' || seq_record.sequence_name,
                    max_val
                );
                RAISE NOTICE 'Updated sequence % to %', seq_record.sequence_name, max_val;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Could not update sequence %: %', seq_record.sequence_name, SQLERRM;
        END;
    END LOOP;
END $$;
EOF

    log_success "序列值更新完成"
}

# ============================================================================
# 重建索引
# ============================================================================
rebuild_indexes() {
    log_info "重建索引..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -c "REINDEX DATABASE $TARGET_DB_NAME;"

    log_success "索引重建完成"
}

# ============================================================================
# 分析数据库
# ============================================================================
analyze_database() {
    log_info "分析数据库..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -c "ANALYZE;"

    log_success "数据库分析完成"
}

# ============================================================================
# 生成恢复报告
# ============================================================================
generate_report() {
    local status="$1"
    local report_file="restore_report_$(date +%Y%m%d_%H%M%S).txt"

    log_info "生成恢复报告: $report_file"

    cat > "$report_file" <<EOF
========================================
数据库恢复报告
========================================
恢复时间: $(date '+%Y-%m-%d %H:%M:%S')
备份文件: $BACKUP_FILE
目标数据库: $TARGET_DB_NAME
恢复模式: $RESTORE_MODE
恢复状态: $status

----------------------------------------
数据库信息
----------------------------------------
EOF

    if [ "$status" = "成功" ]; then
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TARGET_DB_NAME" -t >> "$report_file" <<EOF
SELECT
    'Database Size: ' || pg_size_pretty(pg_database_size('$TARGET_DB_NAME'));

SELECT
    'Tables: ' || COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT
    'Indexes: ' || COUNT(*)
FROM pg_indexes
WHERE schemaname = 'public';
EOF

        cat >> "$report_file" <<EOF

结论: 数据库恢复成功
EOF
    else
        cat >> "$report_file" <<EOF

结论: 数据库恢复失败
EOF
    fi

    cat >> "$report_file" <<EOF

========================================
EOF

    log_success "恢复报告已生成: $report_file"
    cat "$report_file"
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    local restore_status="成功"

    # 解析参数
    if [ $# -lt 2 ]; then
        show_usage
        exit 1
    fi

    BACKUP_FILE="$1"
    TARGET_DB_NAME="$2"
    shift 2

    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mode)
                RESTORE_MODE="$2"
                shift 2
                ;;
            -u|--user)
                DB_USER="$2"
                POSTGRES_USER="$2"
                shift 2
                ;;
            -h|--host)
                DB_HOST="$2"
                shift 2
                ;;
            -p|--port)
                DB_PORT="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log_info "开始数据库恢复..."
    log_info "恢复模式: $RESTORE_MODE"

    # 检查备份文件
    check_backup_file

    # 根据恢复模式执行操作
    case "$RESTORE_MODE" in
        create)
            create_database
            ;;
        replace)
            if database_exists "$TARGET_DB_NAME"; then
                backup_existing_database
                drop_database
            fi
            create_database
            ;;
        merge)
            if ! database_exists "$TARGET_DB_NAME"; then
                log_error "目标数据库不存在: $TARGET_DB_NAME"
                exit 1
            fi
            backup_existing_database
            ;;
        *)
            log_error "无效的恢复模式: $RESTORE_MODE"
            show_usage
            exit 1
            ;;
    esac

    # 执行恢复
    if ! restore_backup; then
        restore_status="失败"
    elif ! verify_restore; then
        restore_status="失败"
    else
        # 后处理
        update_sequences
        rebuild_indexes
        analyze_database
    fi

    # 生成报告
    generate_report "$restore_status"

    if [ "$restore_status" = "成功" ]; then
        log_success "数据库恢复完成！"
        exit 0
    else
        log_error "数据库恢复失败！"
        exit 1
    fi
}

# ============================================================================
# 脚本入口
# ============================================================================
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
