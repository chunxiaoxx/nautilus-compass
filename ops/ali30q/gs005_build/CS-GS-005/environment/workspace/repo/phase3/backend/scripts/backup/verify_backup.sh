#!/bin/bash

################################################################################
# PostgreSQL 备份验证脚本
# 功能：完整性检查、恢复测试、报告生成
################################################################################

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/nautilus}"
LOG_DIR="${LOG_DIR:-$BACKUP_ROOT/logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# 测试数据库配置
TEST_DB_NAME="${TEST_DB_NAME:-nautilus_test_restore}"
TEST_DB_HOST="${TEST_DB_HOST:-localhost}"
TEST_DB_PORT="${TEST_DB_PORT:-5432}"
TEST_DB_USER="${TEST_DB_USER:-postgres}"
PGPASSWORD="${PGPASSWORD:-}"

# 验证配置
VERIFY_MODE="${VERIFY_MODE:-all}"  # checksum, restore, all
BACKUP_FILE="${BACKUP_FILE:-}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-true}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 验证结果
VERIFY_RESULTS=()
VERIFY_PASSED=0
VERIFY_FAILED=0

################################################################################
# 日志函数
################################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"
    VERIFY_PASSED=$((VERIFY_PASSED + 1))
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"
    VERIFY_FAILED=$((VERIFY_FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"
}

################################################################################
# 初始化
################################################################################

init_verify() {
    log "初始化验证环境..."

    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_ROOT/temp"

    # 检查依赖
    local deps=("psql" "pg_restore" "sha256sum")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "缺少依赖: $dep"
            exit 1
        fi
    done

    log_success "初始化完成"
}

################################################################################
# 查找最新备份
################################################################################

find_latest_backup() {
    log "查找最新备份文件..."

    if [[ -n "$BACKUP_FILE" ]] && [[ -f "$BACKUP_FILE" ]]; then
        echo "$BACKUP_FILE"
        return
    fi

    local latest_backup=$(find "$BACKUP_ROOT/full" -type f \( -name "*.gz" -o -name "*.gz.enc" \) -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$latest_backup" ]]; then
        log_error "未找到备份文件"
        exit 1
    fi

    log_success "找到备份: $latest_backup"
    echo "$latest_backup"
}

################################################################################
# 校验和验证
################################################################################

verify_checksum() {
    local backup_file="$1"
    log "验证校验和: $(basename $backup_file)"

    local checksum_file="${backup_file}.sha256"

    if [[ ! -f "$checksum_file" ]]; then
        log_error "校验和文件不存在: $checksum_file"
        VERIFY_RESULTS+=("FAILED: 校验和文件缺失")
        return 1
    fi

    # 验证校验和
    if sha256sum -c "$checksum_file" &> /dev/null; then
        log_success "校验和验证通过"
        VERIFY_RESULTS+=("PASSED: 校验和验证")
        return 0
    else
        log_error "校验和验证失败"
        VERIFY_RESULTS+=("FAILED: 校验和不匹配")
        return 1
    fi
}

################################################################################
# 元数据验证
################################################################################

verify_metadata() {
    local backup_file="$1"
    log "验证元数据: $(basename $backup_file)"

    local metadata_file="${backup_file}.meta.json"

    if [[ ! -f "$metadata_file" ]]; then
        log_warning "元数据文件不存在: $metadata_file"
        VERIFY_RESULTS+=("WARNING: 元数据文件缺失")
        return 1
    fi

    # 检查元数据完整性
    if ! jq empty "$metadata_file" 2>/dev/null; then
        log_error "元数据文件格式错误"
        VERIFY_RESULTS+=("FAILED: 元数据格式错误")
        return 1
    fi

    # 显示元数据信息
    log "备份信息:"
    jq -r '. | "  类型: \(.backup_type)\n  日期: \(.date)\n  大小: \(.file_size_human)\n  数据库: \(.database)"' "$metadata_file" | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"

    log_success "元数据验证通过"
    VERIFY_RESULTS+=("PASSED: 元数据验证")
    return 0
}

################################################################################
# 文件完整性验证
################################################################################

verify_file_integrity() {
    local backup_file="$1"
    log "验证文件完整性: $(basename $backup_file)"

    # 检查文件是否存在
    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在"
        VERIFY_RESULTS+=("FAILED: 文件不存在")
        return 1
    fi

    # 检查文件大小
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    if [[ $file_size -eq 0 ]]; then
        log_error "备份文件为空"
        VERIFY_RESULTS+=("FAILED: 文件为空")
        return 1
    fi

    log "文件大小: $(du -h $backup_file | cut -f1)"

    # 检查文件类型
    local file_type=$(file -b "$backup_file")
    log "文件类型: $file_type"

    # 验证压缩文件
    if [[ "$backup_file" == *.gz ]] || [[ "$file_type" == *gzip* ]]; then
        if gzip -t "$backup_file" 2>/dev/null; then
            log_success "Gzip 压缩文件完整"
        else
            log_error "Gzip 压缩文件损坏"
            VERIFY_RESULTS+=("FAILED: 压缩文件损坏")
            return 1
        fi
    fi

    log_success "文件完整性验证通过"
    VERIFY_RESULTS+=("PASSED: 文件完整性")
    return 0
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
        return 1
    fi

    openssl enc -aes-256-cbc -d \
        -in "$encrypted_file" \
        -out "$decrypted_file" \
        -k "$ENCRYPTION_KEY" \
        -pbkdf2

    if [[ ! -f "$decrypted_file" ]]; then
        log_error "解密失败"
        VERIFY_RESULTS+=("FAILED: 解密失败")
        return 1
    fi

    log_success "解密完成"
    VERIFY_RESULTS+=("PASSED: 解密成功")
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
        VERIFY_RESULTS+=("FAILED: 解压失败")
        return 1
    fi

    log_success "解压完成"
    echo "$decompressed_file"
}

################################################################################
# 准备测试数据库
################################################################################

prepare_test_database() {
    log "准备测试数据库..."

    # 删除已存在的测试数据库
    PGPASSWORD="$PGPASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" 2>/dev/null || true

    # 创建测试数据库
    PGPASSWORD="$PGPASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d postgres -c "CREATE DATABASE $TEST_DB_NAME;"

    if [[ $? -ne 0 ]]; then
        log_error "创建测试数据库失败"
        return 1
    fi

    log_success "测试数据库已创建: $TEST_DB_NAME"
}

################################################################################
# 恢复测试
################################################################################

verify_restore() {
    local backup_file="$1"
    log "执行恢复测试: $(basename $backup_file)"

    # 准备测试数据库
    if ! prepare_test_database; then
        VERIFY_RESULTS+=("FAILED: 测试数据库创建失败")
        return 1
    fi

    local restore_file="$backup_file"

    # 处理加密文件
    if [[ "$backup_file" == *.enc ]]; then
        restore_file=$(decrypt_backup "$backup_file")
        if [[ $? -ne 0 ]]; then
            return 1
        fi
    fi

    # 处理压缩文件
    if [[ "$restore_file" == *.gz ]]; then
        restore_file=$(decompress_backup "$restore_file")
        if [[ $? -ne 0 ]]; then
            return 1
        fi
    fi

    # 执行恢复
    log "恢复数据到测试数据库..."
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$TEST_DB_HOST" \
        -p "$TEST_DB_PORT" \
        -U "$TEST_DB_USER" \
        -d "$TEST_DB_NAME" \
        -f "$restore_file" \
        2>&1 | tee -a "$LOG_DIR/verify_${DATE_ONLY}.log"

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        log_error "恢复失败"
        VERIFY_RESULTS+=("FAILED: 数据恢复失败")
        cleanup_test_database
        return 1
    fi

    log_success "恢复完成"

    # 验证恢复的数据
    if ! verify_restored_data; then
        VERIFY_RESULTS+=("FAILED: 恢复数据验证失败")
        cleanup_test_database
        return 1
    fi

    log_success "恢复测试通过"
    VERIFY_RESULTS+=("PASSED: 恢复测试")

    # 清理测试数据库
    cleanup_test_database

    return 0
}

################################################################################
# 验证恢复的数据
################################################################################

verify_restored_data() {
    log "验证恢复的数据..."

    # 检查表数量
    local table_count=$(PGPASSWORD="$PGPASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    log "表数量: $table_count"

    if [[ $table_count -eq 0 ]]; then
        log_error "未找到任何表"
        return 1
    fi

    # 检查数据完整性
    local queries=(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public';"
        "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';"
    )

    for query in "${queries[@]}"; do
        local result=$(PGPASSWORD="$PGPASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d "$TEST_DB_NAME" -t -c "$query" 2>/dev/null)
        if [[ $? -ne 0 ]]; then
            log_error "查询失败: $query"
            return 1
        fi
        log "查询结果: $result"
    done

    log_success "数据验证通过"
    return 0
}

################################################################################
# 清理测试数据库
################################################################################

cleanup_test_database() {
    log "清理测试数据库..."

    PGPASSWORD="$PGPASSWORD" psql -h "$TEST_DB_HOST" -p "$TEST_DB_PORT" -U "$TEST_DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" 2>/dev/null

    log_success "测试数据库已清理"
}

################################################################################
# 批量验证
################################################################################

verify_all_backups() {
    log "批量验证所有备份..."

    local backup_files=$(find "$BACKUP_ROOT/full" -type f \( -name "*.gz" -o -name "*.gz.enc" \) | sort -r)

    if [[ -z "$backup_files" ]]; then
        log_error "未找到备份文件"
        return 1
    fi

    local total_count=$(echo "$backup_files" | wc -l)
    local current=0

    echo "$backup_files" | while read -r backup_file; do
        current=$((current + 1))
        log "验证备份 [$current/$total_count]: $(basename $backup_file)"

        # 只验证校验和和元数据，不执行恢复测试
        verify_checksum "$backup_file"
        verify_metadata "$backup_file"
        verify_file_integrity "$backup_file"

        echo "----------------------------------------"
    done

    log_success "批量验证完成"
}

################################################################################
# 生成验证报告
################################################################################

generate_report() {
    log "生成验证报告..."

    local report_file="$LOG_DIR/verify_report_${TIMESTAMP}.txt"

    cat > "$report_file" <<EOF
================================================================================
PostgreSQL 备份验证报告
================================================================================
日期: $(date)
验证模式: $VERIFY_MODE

验证结果:
--------------------------------------------------------------------------------
通过: $VERIFY_PASSED
失败: $VERIFY_FAILED

详细结果:
EOF

    for result in "${VERIFY_RESULTS[@]}"; do
        echo "  - $result" >> "$report_file"
    done

    cat >> "$report_file" <<EOF

================================================================================
EOF

    cat "$report_file"
    log_success "报告已生成: $report_file"

    # 返回状态
    if [[ $VERIFY_FAILED -gt 0 ]]; then
        return 1
    fi
    return 0
}

################################################################################
# 主函数
################################################################################

main() {
    log "========================================"
    log "PostgreSQL 备份验证脚本启动"
    log "========================================"

    # 初始化
    init_verify

    # 查找备份文件
    local backup_file=$(find_latest_backup)

    # 执行验证
    case "$VERIFY_MODE" in
        checksum)
            verify_checksum "$backup_file"
            verify_metadata "$backup_file"
            verify_file_integrity "$backup_file"
            ;;
        restore)
            verify_restore "$backup_file"
            ;;
        all)
            verify_checksum "$backup_file"
            verify_metadata "$backup_file"
            verify_file_integrity "$backup_file"
            verify_restore "$backup_file"
            ;;
        batch)
            verify_all_backups
            ;;
        *)
            log_error "未知的验证模式: $VERIFY_MODE"
            exit 1
            ;;
    esac

    # 生成报告
    generate_report

    if [[ $? -eq 0 ]]; then
        log_success "所有验证通过"
        exit 0
    else
        log_error "验证失败"
        exit 1
    fi
}

# 执行主函数
main "$@"
