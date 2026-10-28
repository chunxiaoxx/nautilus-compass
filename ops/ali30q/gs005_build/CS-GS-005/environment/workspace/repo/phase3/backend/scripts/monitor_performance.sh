#!/bin/bash
# ============================================================================
# 数据库性能监控脚本
# ============================================================================
# 功能: 监控数据库性能指标并生成报告
# 版本: 1.0.0
# 创建日期: 2026-02-27
# ============================================================================

set -e
set -u

# ============================================================================
# 颜色输出
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# 配置变量
# ============================================================================
DB_NAME="${DB_NAME:-nautilus_production}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
REPORT_DIR="${REPORT_DIR:-/var/log/postgresql/performance}"
DATE=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/performance_report_${DATE}.txt"

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
# 初始化
# ============================================================================
initialize() {
    log_info "初始化性能监控..."
    mkdir -p "$REPORT_DIR"

    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        log_error "PostgreSQL 服务未运行"
        exit 1
    fi

    log_success "初始化完成"
}

# ============================================================================
# 生成报告头部
# ============================================================================
generate_report_header() {
    cat > "$REPORT_FILE" <<EOF
========================================
PostgreSQL 性能监控报告
========================================
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
数据库: $DB_NAME
主机: $DB_HOST:$DB_PORT

========================================
EOF
}

# ============================================================================
# 数据库连接统计
# ============================================================================
check_connections() {
    log_info "检查数据库连接..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
数据库连接统计
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    'Total Connections: ' || count(*) as metric
FROM pg_stat_activity
UNION ALL
SELECT
    'Active Connections: ' || count(*)
FROM pg_stat_activity
WHERE state = 'active'
UNION ALL
SELECT
    'Idle Connections: ' || count(*)
FROM pg_stat_activity
WHERE state = 'idle'
UNION ALL
SELECT
    'Max Connections: ' || setting
FROM pg_settings
WHERE name = 'max_connections';

SELECT
    datname as database,
    count(*) as connections
FROM pg_stat_activity
GROUP BY datname
ORDER BY connections DESC;
EOF
}

# ============================================================================
# 缓存命中率
# ============================================================================
check_cache_hit_ratio() {
    log_info "检查缓存命中率..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
缓存命中率
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    'Buffer Cache Hit Ratio: ' ||
    round(
        sum(heap_blks_hit) * 100.0 /
        NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0),
        2
    ) || '%' as metric
FROM pg_statio_user_tables;

SELECT
    schemaname,
    tablename,
    heap_blks_read,
    heap_blks_hit,
    round(
        heap_blks_hit * 100.0 / NULLIF(heap_blks_hit + heap_blks_read, 0),
        2
    ) as hit_ratio_percent
FROM pg_statio_user_tables
WHERE heap_blks_read + heap_blks_hit > 0
ORDER BY heap_blks_read DESC
LIMIT 10;
EOF
}

# ============================================================================
# 数据库大小
# ============================================================================
check_database_size() {
    log_info "检查数据库大小..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
数据库大小统计
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    'Total Database Size: ' || pg_size_pretty(pg_database_size(current_database())) as metric;

SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF
}

# ============================================================================
# 表膨胀检查
# ============================================================================
check_table_bloat() {
    log_info "检查表膨胀..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
表膨胀检查
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    schemaname,
    tablename,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio_percent,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 10;
EOF
}

# ============================================================================
# 索引使用情况
# ============================================================================
check_index_usage() {
    log_info "检查索引使用情况..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
索引使用情况
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
-- 最常用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC
LIMIT 10;

-- 未使用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 10;
EOF
}

# ============================================================================
# 慢查询统计
# ============================================================================
check_slow_queries() {
    log_info "检查慢查询..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
慢查询统计（需要 pg_stat_statements）
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF' 2>/dev/null || echo "pg_stat_statements 扩展未安装" >> "$REPORT_FILE"
SELECT
    substring(query, 1, 100) as query_snippet,
    calls,
    round(total_exec_time::numeric, 2) as total_time_ms,
    round(mean_exec_time::numeric, 2) as avg_time_ms,
    round(max_exec_time::numeric, 2) as max_time_ms
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
EOF
}

# ============================================================================
# 锁等待检查
# ============================================================================
check_locks() {
    log_info "检查锁等待..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
锁等待情况
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    count(*) as lock_count,
    mode,
    granted
FROM pg_locks
GROUP BY mode, granted
ORDER BY lock_count DESC;

-- 阻塞查询
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    substring(blocked_activity.query, 1, 50) AS blocked_query,
    substring(blocking_activity.query, 1, 50) AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted
LIMIT 5;
EOF
}

# ============================================================================
# 长时间运行的查询
# ============================================================================
check_long_running_queries() {
    log_info "检查长时间运行的查询..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
长时间运行的查询
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    pid,
    usename,
    application_name,
    state,
    now() - query_start AS duration,
    substring(query, 1, 100) AS query_snippet
FROM pg_stat_activity
WHERE state = 'active'
AND now() - query_start > interval '1 minute'
ORDER BY duration DESC
LIMIT 10;
EOF
}

# ============================================================================
# 复制状态（如果配置了复制）
# ============================================================================
check_replication() {
    log_info "检查复制状态..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
复制状态
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF' 2>/dev/null || echo "未配置复制" >> "$REPORT_FILE"
SELECT
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS lag_size
FROM pg_stat_replication;
EOF
}

# ============================================================================
# 系统资源使用
# ============================================================================
check_system_resources() {
    log_info "检查系统资源..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
系统资源使用
----------------------------------------
EOF

    # 磁盘使用
    echo "磁盘使用:" >> "$REPORT_FILE"
    df -h | grep -E '(Filesystem|/var/lib/postgresql)' >> "$REPORT_FILE" 2>/dev/null || echo "无法获取磁盘信息" >> "$REPORT_FILE"

    # 内存使用
    echo -e "\n内存使用:" >> "$REPORT_FILE"
    free -h >> "$REPORT_FILE" 2>/dev/null || echo "无法获取内存信息" >> "$REPORT_FILE"
}

# ============================================================================
# 配置参数检查
# ============================================================================
check_configuration() {
    log_info "检查配置参数..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
关键配置参数
----------------------------------------
EOF

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t >> "$REPORT_FILE" <<'EOF'
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'max_connections',
    'shared_buffers',
    'effective_cache_size',
    'maintenance_work_mem',
    'work_mem',
    'wal_level',
    'max_wal_senders',
    'checkpoint_completion_target',
    'random_page_cost',
    'effective_io_concurrency'
)
ORDER BY name;
EOF
}

# ============================================================================
# 生成建议
# ============================================================================
generate_recommendations() {
    log_info "生成优化建议..."

    cat >> "$REPORT_FILE" <<EOF

----------------------------------------
优化建议
----------------------------------------
EOF

    # 检查缓存命中率
    local cache_hit_ratio=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT round(sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2)
        FROM pg_statio_user_tables;
    " 2>/dev/null || echo "0")

    if (( $(echo "$cache_hit_ratio < 90" | bc -l 2>/dev/null || echo "0") )); then
        echo "⚠ 缓存命中率较低 ($cache_hit_ratio%)，建议增加 shared_buffers" >> "$REPORT_FILE"
    else
        echo "✓ 缓存命中率良好 ($cache_hit_ratio%)" >> "$REPORT_FILE"
    fi

    # 检查未使用的索引
    local unused_indexes=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT count(*) FROM pg_stat_user_indexes WHERE idx_scan = 0;
    " 2>/dev/null || echo "0")

    if [ "$unused_indexes" -gt 0 ]; then
        echo "⚠ 发现 $unused_indexes 个未使用的索引，建议删除以节省空间" >> "$REPORT_FILE"
    fi

    # 检查表膨胀
    local bloated_tables=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "
        SELECT count(*) FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000 AND n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0) > 20;
    " 2>/dev/null || echo "0")

    if [ "$bloated_tables" -gt 0 ]; then
        echo "⚠ 发现 $bloated_tables 个表存在膨胀，建议执行 VACUUM" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" <<EOF

建议操作:
1. 定期执行 ANALYZE 更新统计信息
2. 定期执行 VACUUM 清理死元组
3. 监控慢查询并优化
4. 删除未使用的索引
5. 检查并优化表膨胀

========================================
EOF
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    log_info "开始性能监控..."

    initialize
    generate_report_header
    check_connections
    check_cache_hit_ratio
    check_database_size
    check_table_bloat
    check_index_usage
    check_slow_queries
    check_locks
    check_long_running_queries
    check_replication
    check_system_resources
    check_configuration
    generate_recommendations

    log_success "性能报告已生成: $REPORT_FILE"

    # 显示报告
    cat "$REPORT_FILE"
}

# ============================================================================
# 脚本入口
# ============================================================================
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
