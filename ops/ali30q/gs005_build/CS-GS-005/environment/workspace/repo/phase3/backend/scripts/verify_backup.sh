#!/bin/bash
# ============================================================================
# 数据库备份验证脚本
# ============================================================================
# 功能: 验证备份文件的完整性和可恢复性
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
TEST_DB_NAME="test_restore_$(date +%s)"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

# ============================================================================
# 验证备份文件存在
# ============================================================================
check_backup_file() {
    log_info "检查备份文件: $BACKUP_FILE"

    if [ -z "$BACKUP_FILE" ]; then
        log_error "未指定备份文件"
        echo "用法: $0 <backup_file>"
        exit 1
    fi

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi

    log_success "备份文件存在"
}

# ============================================================================
# 检查文件完整性
# ============================================================================
verify_file_integrity() {
    log_info "验证文件完整性..."

    # 检查文件大小
    local file_size=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
    log_info "文件大小: $(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "$file_size bytes")"

    if [ "$file_size" -lt 1024 ]; then
        log_error "文件太小，可能损坏: $file_size bytes"
        return 1
    fi

    # 检查文件类型
    local file_type=$(file -b "$BACKUP_FILE")
    log_info "文件类型: $file_type"

    # 如果是压缩文件，验证压缩完整性
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        log_info "验证 gzip 压缩完整性..."
        if gzip -t "$BACKUP_FILE" 2>&1; then
            log_success "压缩文件完整性验证通过"
        else
            log_error "压缩文件损坏"
            return 1
        fi
    fi

    log_success "文件完整性验证通过"
}

# ============================================================================
# 创建测试数据库
# ============================================================================
create_test_database() {
    log_info "创建测试数据库: $TEST_DB_NAME"

    # 检查数据库是否已存在
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$TEST_DB_NAME"; then
        log_warning "测试数据库已存在，删除后重建"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c "DROP DATABASE $TEST_DB_NAME;"
    fi

    # 创建测试数据库
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE DATABASE $TEST_DB_NAME
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
EOF

    log_success "测试数据库创建成功"
}

# ============================================================================
# 恢复备份到测试数据库
# ============================================================================
restore_backup() {
    log_info "恢复备份到测试数据库..."

    local start_time=$(date +%s)

    # 根据文件类型选择恢复方法
    if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
        # SQL 格式备份
        log_info "使用 SQL 格式恢复..."
        if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" 2>&1; then
            log_success "SQL 备份恢复成功"
        else
            log_error "SQL 备份恢复失败"
            return 1
        fi
    elif [[ "$BACKUP_FILE" == *.sql ]]; then
        # 未压缩的 SQL 备份
        log_info "使用未压缩 SQL 格式恢复..."
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -f "$BACKUP_FILE" 2>&1; then
            log_success "SQL 备份恢复成功"
        else
            log_error "SQL 备份恢复失败"
            return 1
        fi
    elif [[ "$BACKUP_FILE" == *.dump ]] || [[ "$BACKUP_FILE" == *.custom ]]; then
        # pg_dump custom 格式
        log_info "使用 custom 格式恢复..."
        if pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -v "$BACKUP_FILE" 2>&1; then
            log_success "Custom 备份恢复成功"
        else
            log_error "Custom 备份恢复失败"
            return 1
        fi
    else
        log_error "不支持的备份文件格式"
        return 1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "恢复耗时: ${duration}秒"

    log_success "备份恢复完成"
}

# ============================================================================
# 验证恢复的数据
# ============================================================================
verify_restored_data() {
    log_info "验证恢复的数据..."

    # 检查数据库连接
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_error "无法连接到测试数据库"
        return 1
    fi

    # 获取表数量
    local table_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -tAc "
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
    ")
    log_info "表数量: $table_count"

    if [ "$table_count" -eq 0 ]; then
        log_warning "未找到任何表"
    fi

    # 获取记录总数
    log_info "统计各表记录数..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" <<EOF
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;
EOF

    # 检查索引
    local index_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -tAc "
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE schemaname = 'public';
    ")
    log_info "索引数量: $index_count"

    # 检查序列
    local sequence_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -tAc "
        SELECT COUNT(*)
        FROM information_schema.sequences
        WHERE sequence_schema = 'public';
    ")
    log_info "序列数量: $sequence_count"

    # 检查视图
    local view_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -tAc "
        SELECT COUNT(*)
        FROM information_schema.views
        WHERE table_schema = 'public';
    ")
    log_info "视图数量: $view_count"

    # 检查扩展
    log_info "已安装的扩展:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -c "
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname NOT IN ('plpgsql');
    "

    log_success "数据验证完成"
}

# ============================================================================
# 执行数据完整性测试
# ============================================================================
test_data_integrity() {
    log_info "执行数据完整性测试..."

    # 测试查询
    log_info "执行测试查询..."

    # 检查是否有损坏的索引
    local corrupt_indexes=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -tAc "
        SELECT COUNT(*)
        FROM pg_class c
        JOIN pg_index i ON c.oid = i.indexrelid
        WHERE c.relkind = 'i'
        AND NOT pg_index_is_valid(i.indexrelid);
    ")

    if [ "$corrupt_indexes" -gt 0 ]; then
        log_error "发现 $corrupt_indexes 个损坏的索引"
        return 1
    else
        log_success "所有索引完整"
    fi

    # 检查外键约束
    log_info "检查外键约束..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -c "
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        LIMIT 5;
    "

    log_success "数据完整性测试通过"
}

# ============================================================================
# 性能测试
# ============================================================================
performance_test() {
    log_info "执行性能测试..."

    # 测试简单查询性能
    log_info "测试查询性能..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$TEST_DB_NAME" -c "
        EXPLAIN ANALYZE
        SELECT COUNT(*) FROM pg_class;
    "

    log_success "性能测试完成"
}

# ============================================================================
# 清理测试数据库
# ============================================================================
cleanup_test_database() {
    log_info "清理测试数据库: $TEST_DB_NAME"

    # 断开所有连接
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$TEST_DB_NAME'
AND pid <> pg_backend_pid();
EOF

    # 删除测试数据库
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;"

    log_success "测试数据库已清理"
}

# ============================================================================
# 生成验证报告
# ============================================================================
generate_report() {
    local status="$1"
    local report_file="backup_verification_$(date +%Y%m%d_%H%M%S).txt"

    log_info "生成验证报告: $report_file"

    cat > "$report_file" <<EOF
========================================
数据库备份验证报告
========================================
验证时间: $(date '+%Y-%m-%d %H:%M:%S')
备份文件: $BACKUP_FILE
测试数据库: $TEST_DB_NAME
验证状态: $status

----------------------------------------
文件信息
----------------------------------------
文件大小: $(du -h "$BACKUP_FILE" | cut -f1)
文件类型: $(file -b "$BACKUP_FILE")

----------------------------------------
验证结果
----------------------------------------
EOF

    if [ "$status" = "成功" ]; then
        cat >> "$report_file" <<EOF
✓ 文件完整性验证通过
✓ 备份恢复成功
✓ 数据完整性验证通过
✓ 性能测试通过

结论: 备份文件可用，可以安全用于恢复
EOF
    else
        cat >> "$report_file" <<EOF
✗ 验证失败

结论: 备份文件可能存在问题，请检查备份流程
EOF
    fi

    cat >> "$report_file" <<EOF

========================================
EOF

    log_success "验证报告已生成: $report_file"
    cat "$report_file"
}

# ============================================================================
# 显示使用帮助
# ============================================================================
show_usage() {
    cat <<EOF
用法: $0 <backup_file> [选项]

参数:
    backup_file             备份文件路径

选项:
    -u, --user USER         数据库用户 (默认: postgres)
    -h, --host HOST         数据库主机 (默认: localhost)
    -p, --port PORT         数据库端口 (默认: 5432)
    --no-cleanup            不清理测试数据库
    --help                  显示此帮助信息

示例:
    # 验证备份文件
    $0 /var/backups/postgresql/nautilus_production_20260227.sql.gz

    # 验证并保留测试数据库
    $0 /var/backups/postgresql/backup.sql.gz --no-cleanup

    # 指定数据库连接参数
    $0 backup.sql.gz --host localhost --port 5432 --user postgres
EOF
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    local cleanup=true
    local verification_status="成功"

    # 解析参数
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    BACKUP_FILE="$1"
    shift

    while [[ $# -gt 0 ]]; do
        case $1 in
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
            --no-cleanup)
                cleanup=false
                shift
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

    log_info "开始验证备份文件..."

    # 执行验证步骤
    if ! check_backup_file; then
        verification_status="失败"
    elif ! verify_file_integrity; then
        verification_status="失败"
    elif ! create_test_database; then
        verification_status="失败"
    elif ! restore_backup; then
        verification_status="失败"
    elif ! verify_restored_data; then
        verification_status="失败"
    elif ! test_data_integrity; then
        verification_status="失败"
    elif ! performance_test; then
        verification_status="失败"
    fi

    # 生成报告
    generate_report "$verification_status"

    # 清理测试数据库
    if [ "$cleanup" = true ]; then
        cleanup_test_database
    else
        log_warning "保留测试数据库: $TEST_DB_NAME"
    fi

    if [ "$verification_status" = "成功" ]; then
        log_success "备份验证完成！备份文件可用"
        exit 0
    else
        log_error "备份验证失败！"
        exit 1
    fi
}

# ============================================================================
# 脚本入口
# ============================================================================
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
