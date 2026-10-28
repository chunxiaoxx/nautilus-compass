#!/bin/bash

################################################################################
# PostgreSQL 数据库备份脚本
# 功能：全量备份、增量备份、压缩加密、远程存储
# 遵循 3-2-1 备份原则
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

# 备份配置
BACKUP_TYPE="${BACKUP_TYPE:-full}"  # full, incremental
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"
ENABLE_ENCRYPTION="${ENABLE_ENCRYPTION:-true}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

# 远程存储配置
ENABLE_REMOTE_UPLOAD="${ENABLE_REMOTE_UPLOAD:-false}"
REMOTE_TYPE="${REMOTE_TYPE:-s3}"  # s3, azure, gcs
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/postgres}"
AWS_REGION="${AWS_REGION:-us-east-1}"

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
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"
}

################################################################################
# 初始化
################################################################################

init_backup() {
    log "初始化备份环境..."

    # 创建必要目录
    mkdir -p "$BACKUP_ROOT"/{full,incremental,wal,temp,logs}
    mkdir -p "$LOG_DIR"

    # 检查依赖
    local deps=("pg_dump" "pg_basebackup" "gzip" "tar")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "缺少依赖: $dep"
            exit 1
        fi
    done

    # 检查加密工具
    if [[ "$ENABLE_ENCRYPTION" == "true" ]]; then
        if ! command -v openssl &> /dev/null; then
            log_error "加密已启用但缺少 openssl"
            exit 1
        fi
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            log_error "加密已启用但未设置 ENCRYPTION_KEY"
            exit 1
        fi
    fi

    # 检查数据库连接
    if ! PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        log_error "无法连接到数据库"
        exit 1
    fi

    log_success "初始化完成"
}

################################################################################
# 全量备份
################################################################################

full_backup() {
    log "开始全量备份..."

    local backup_dir="$BACKUP_ROOT/full"
    local backup_name="full_${DB_NAME}_${TIMESTAMP}"
    local backup_file="$backup_dir/${backup_name}.sql"
    local compressed_file="${backup_file}.gz"
    local final_file="$compressed_file"

    # 1. 执行 pg_dump
    log "导出数据库..."
    PGPASSWORD="$PGPASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --verbose \
        --no-owner \
        --no-acl \
        --file="$backup_file" 2>&1 | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"

    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件创建失败"
        exit 1
    fi

    local backup_size=$(du -h "$backup_file" | cut -f1)
    log_success "数据库导出完成，大小: $backup_size"

    # 2. 压缩
    log "压缩备份文件..."
    gzip -"$COMPRESSION_LEVEL" "$backup_file"

    if [[ ! -f "$compressed_file" ]]; then
        log_error "压缩失败"
        exit 1
    fi

    local compressed_size=$(du -h "$compressed_file" | cut -f1)
    log_success "压缩完成，大小: $compressed_size"

    # 3. 加密
    if [[ "$ENABLE_ENCRYPTION" == "true" ]]; then
        log "加密备份文件..."
        local encrypted_file="${compressed_file}.enc"

        openssl enc -aes-256-cbc \
            -salt \
            -in "$compressed_file" \
            -out "$encrypted_file" \
            -k "$ENCRYPTION_KEY" \
            -pbkdf2

        if [[ ! -f "$encrypted_file" ]]; then
            log_error "加密失败"
            exit 1
        fi

        rm -f "$compressed_file"
        final_file="$encrypted_file"
        log_success "加密完成"
    fi

    # 4. 生成校验和
    log "生成校验和..."
    sha256sum "$final_file" > "${final_file}.sha256"
    log_success "校验和已生成"

    # 5. 创建元数据
    create_metadata "$final_file" "full"

    # 6. 远程上传
    if [[ "$ENABLE_REMOTE_UPLOAD" == "true" ]]; then
        upload_to_remote "$final_file"
        upload_to_remote "${final_file}.sha256"
    fi

    log_success "全量备份完成: $final_file"
    echo "$final_file"
}

################################################################################
# 增量备份 (WAL归档)
################################################################################

incremental_backup() {
    log "开始增量备份 (WAL归档)..."

    local backup_dir="$BACKUP_ROOT/incremental"
    local wal_dir="$BACKUP_ROOT/wal"
    local backup_name="incremental_${DB_NAME}_${TIMESTAMP}"

    # 检查是否存在基础备份
    if [[ ! -d "$BACKUP_ROOT/full" ]] || [[ -z "$(ls -A $BACKUP_ROOT/full 2>/dev/null)" ]]; then
        log_warning "未找到全量备份，将执行全量备份"
        full_backup
        return
    fi

    # 1. 归档WAL文件
    log "归档WAL文件..."
    local wal_archive_dir="$wal_dir/${DATE_ONLY}"
    mkdir -p "$wal_archive_dir"

    # 获取当前WAL位置
    local wal_info=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_current_wal_lsn();")
    log "当前WAL位置: $wal_info"

    # 2. 创建增量备份标记
    local marker_file="$backup_dir/${backup_name}.marker"
    cat > "$marker_file" <<EOF
{
  "backup_type": "incremental",
  "timestamp": "$TIMESTAMP",
  "wal_position": "$wal_info",
  "database": "$DB_NAME",
  "host": "$DB_HOST"
}
EOF

    # 3. 压缩WAL文件
    if [[ -n "$(ls -A $wal_archive_dir 2>/dev/null)" ]]; then
        log "压缩WAL归档..."
        tar -czf "$backup_dir/${backup_name}_wal.tar.gz" -C "$wal_dir" "${DATE_ONLY}"
        log_success "WAL归档完成"
    fi

    log_success "增量备份完成"
}

################################################################################
# 基础备份 (pg_basebackup)
################################################################################

base_backup() {
    log "开始物理基础备份..."

    local backup_dir="$BACKUP_ROOT/full"
    local backup_name="base_${DB_NAME}_${TIMESTAMP}"
    local backup_path="$backup_dir/$backup_name"

    mkdir -p "$backup_path"

    # 执行 pg_basebackup
    PGPASSWORD="$PGPASSWORD" pg_basebackup \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -D "$backup_path" \
        -Ft \
        -z \
        -P \
        -X fetch \
        --checkpoint=fast 2>&1 | tee -a "$LOG_DIR/backup_${DATE_ONLY}.log"

    if [[ $? -ne 0 ]]; then
        log_error "物理备份失败"
        exit 1
    fi

    log_success "物理基础备份完成: $backup_path"
}

################################################################################
# 创建元数据
################################################################################

create_metadata() {
    local backup_file="$1"
    local backup_type="$2"
    local metadata_file="${backup_file}.meta.json"

    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    local checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)

    cat > "$metadata_file" <<EOF
{
  "backup_type": "$backup_type",
  "database": "$DB_NAME",
  "host": "$DB_HOST",
  "timestamp": "$TIMESTAMP",
  "date": "$(date -Iseconds)",
  "file_name": "$(basename $backup_file)",
  "file_size": $file_size,
  "file_size_human": "$(du -h $backup_file | cut -f1)",
  "checksum": "$checksum",
  "compression": "gzip",
  "compression_level": $COMPRESSION_LEVEL,
  "encrypted": $ENABLE_ENCRYPTION,
  "postgres_version": "$(PGPASSWORD=$PGPASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c 'SELECT version();' | xargs)"
}
EOF

    log_success "元数据已创建: $metadata_file"
}

################################################################################
# 远程上传
################################################################################

upload_to_remote() {
    local file="$1"
    local filename=$(basename "$file")

    log "上传到远程存储: $filename"

    case "$REMOTE_TYPE" in
        s3)
            upload_to_s3 "$file"
            ;;
        azure)
            upload_to_azure "$file"
            ;;
        gcs)
            upload_to_gcs "$file"
            ;;
        *)
            log_error "不支持的远程存储类型: $REMOTE_TYPE"
            return 1
            ;;
    esac
}

upload_to_s3() {
    local file="$1"
    local filename=$(basename "$file")
    local s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_ONLY}/${filename}"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI 未安装"
        return 1
    fi

    aws s3 cp "$file" "$s3_path" \
        --region "$AWS_REGION" \
        --storage-class STANDARD_IA \
        --metadata "backup-date=$TIMESTAMP,database=$DB_NAME"

    if [[ $? -eq 0 ]]; then
        log_success "已上传到 S3: $s3_path"
    else
        log_error "S3 上传失败"
        return 1
    fi
}

upload_to_azure() {
    local file="$1"
    log_warning "Azure 上传功能待实现"
}

upload_to_gcs() {
    local file="$1"
    log_warning "GCS 上传功能待实现"
}

################################################################################
# 清理旧备份
################################################################################

cleanup_old_backups() {
    log "清理旧备份 (保留 $RETENTION_DAYS 天)..."

    local dirs=("$BACKUP_ROOT/full" "$BACKUP_ROOT/incremental" "$BACKUP_ROOT/wal")

    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -type f -mtime +$RETENTION_DAYS -delete
            log "已清理 $dir 中的旧文件"
        fi
    done

    # 清理旧日志
    find "$LOG_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS -delete

    log_success "清理完成"
}

################################################################################
# 备份报告
################################################################################

generate_report() {
    log "生成备份报告..."

    local report_file="$LOG_DIR/backup_report_${DATE_ONLY}.txt"

    cat > "$report_file" <<EOF
================================================================================
PostgreSQL 备份报告
================================================================================
日期: $(date)
数据库: $DB_NAME
主机: $DB_HOST
备份类型: $BACKUP_TYPE

备份统计:
--------------------------------------------------------------------------------
EOF

    # 统计备份文件
    if [[ -d "$BACKUP_ROOT/full" ]]; then
        echo "全量备份数量: $(find $BACKUP_ROOT/full -type f -name "*.gz*" | wc -l)" >> "$report_file"
        echo "全量备份大小: $(du -sh $BACKUP_ROOT/full | cut -f1)" >> "$report_file"
    fi

    if [[ -d "$BACKUP_ROOT/incremental" ]]; then
        echo "增量备份数量: $(find $BACKUP_ROOT/incremental -type f | wc -l)" >> "$report_file"
        echo "增量备份大小: $(du -sh $BACKUP_ROOT/incremental | cut -f1)" >> "$report_file"
    fi

    echo "" >> "$report_file"
    echo "总备份大小: $(du -sh $BACKUP_ROOT | cut -f1)" >> "$report_file"
    echo "================================================================================" >> "$report_file"

    cat "$report_file"
    log_success "报告已生成: $report_file"
}

################################################################################
# 主函数
################################################################################

main() {
    log "========================================"
    log "PostgreSQL 备份脚本启动"
    log "========================================"

    # 初始化
    init_backup

    # 执行备份
    case "$BACKUP_TYPE" in
        full)
            full_backup
            ;;
        incremental)
            incremental_backup
            ;;
        base)
            base_backup
            ;;
        *)
            log_error "未知的备份类型: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # 清理旧备份
    cleanup_old_backups

    # 生成报告
    generate_report

    log_success "备份流程完成"
}

# 执行主函数
main "$@"
