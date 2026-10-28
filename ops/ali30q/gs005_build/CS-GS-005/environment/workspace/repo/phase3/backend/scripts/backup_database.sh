#!/bin/bash
# ============================================================================
# 数据库备份脚本
# ============================================================================
# 功能: 自动备份 PostgreSQL 数据库（逻辑备份和物理备份）
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
DB_NAME="${DB_NAME:-nautilus_production}"
DB_USER="${DB_USER:-nautilus_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_TYPE="${BACKUP_TYPE:-logical}"  # logical, physical, or both
S3_BUCKET="${S3_BUCKET:-}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-}"

# 时间戳
DATE=$(date +%Y%m%d_%H%M%S)
DATE_SIMPLE=$(date +%Y%m%d)

# 备份文件路径
LOGICAL_BACKUP_DIR="${BACKUP_DIR}/logical"
PHYSICAL_BACKUP_DIR="${BACKUP_DIR}/physical"
LOGICAL_BACKUP_FILE="${LOGICAL_BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"
PHYSICAL_BACKUP_DIR_FULL="${PHYSICAL_BACKUP_DIR}/${DATE}"

# 日志文件
LOG_FILE="${BACKUP_DIR}/backup_${DATE_SIMPLE}.log"

# ============================================================================
# 初始化
# ============================================================================
initialize() {
    log_info "初始化备份环境..."

    # 创建备份目录
    mkdir -p "$LOGICAL_BACKUP_DIR"
    mkdir -p "$PHYSICAL_BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"

    # 检查 PostgreSQL 是否运行
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        log_error "PostgreSQL 服务未运行或无法连接"
        exit 1
    fi

    log_success "初始化完成"
}

# ============================================================================
# 逻辑备份（pg_dump）
# ============================================================================
logical_backup() {
    log_info "开始逻辑备份: $DB_NAME"

    local start_time=$(date +%s)

    # 执行备份
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${LOGICAL_BACKUP_FILE%.gz}" 2>&1 | tee -a "$LOG_FILE"; then

        # 压缩备份文件
        gzip -f "${LOGICAL_BACKUP_FILE%.gz}"

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local backup_size=$(du -h "$LOGICAL_BACKUP_FILE" | cut -f1)

        log_success "逻辑备份完成"
        log_info "备份文件: $LOGICAL_BACKUP_FILE"
        log_info "备份大小: $backup_size"
        log_info "耗时: ${duration}秒"

        # 验证备份
        verify_logical_backup "$LOGICAL_BACKUP_FILE"

        return 0
    else
        log_error "逻辑备份失败"
        return 1
    fi
}

# ============================================================================
# 物理备份（pg_basebackup）
# ============================================================================
physical_backup() {
    log_info "开始物理备份: $DB_NAME"

    local start_time=$(date +%s)

    # 执行物理备份
    if pg_basebackup -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -D "$PHYSICAL_BACKUP_DIR_FULL" \
        -Ft -z -Xs -P \
        --checkpoint=fast \
        --label="backup_${DATE}" 2>&1 | tee -a "$LOG_FILE"; then

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local backup_size=$(du -sh "$PHYSICAL_BACKUP_DIR_FULL" | cut -f1)

        log_success "物理备份完成"
        log_info "备份目录: $PHYSICAL_BACKUP_DIR_FULL"
        log_info "备份大小: $backup_size"
        log_info "耗时: ${duration}秒"

        return 0
    else
        log_error "物理备份失败"
        return 1
    fi
}

# ============================================================================
# 验证逻辑备份
# ============================================================================
verify_logical_backup() {
    local backup_file="$1"

    log_info "验证备份文件: $backup_file"

    # 检查文件是否存在
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        return 1
    fi

    # 检查文件大小
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [ "$file_size" -lt 1024 ]; then
        log_error "备份文件太小，可能损坏: $file_size bytes"
        return 1
    fi

    # 检查压缩文件完整性
    if gzip -t "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "备份文件验证通过"
        return 0
    else
        log_error "备份文件验证失败"
        return 1
    fi
}

# ============================================================================
# 清理旧备份
# ============================================================================
cleanup_old_backups() {
    log_info "清理 ${RETENTION_DAYS} 天前的旧备份..."

    local deleted_count=0

    # 清理逻辑备份
    if [ -d "$LOGICAL_BACKUP_DIR" ]; then
        deleted_count=$(find "$LOGICAL_BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
        log_info "删除了 $deleted_count 个旧的逻辑备份文件"
    fi

    # 清理物理备份
    if [ -d "$PHYSICAL_BACKUP_DIR" ]; then
        deleted_count=$(find "$PHYSICAL_BACKUP_DIR" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \; -print | wc -l)
        log_info "删除了 $deleted_count 个旧的物理备份目录"
    fi

    # 清理旧日志
    find "$(dirname "$LOG_FILE")" -name "backup_*.log" -mtime +${RETENTION_DAYS} -delete

    log_success "旧备份清理完成"
}

# ============================================================================
# 上传到 S3
# ============================================================================
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_warning "未配置 S3_BUCKET，跳过上传"
        return 0
    fi

    log_info "上传备份到 S3: $S3_BUCKET"

    # 检查 AWS CLI 是否安装
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI 未安装，无法上传到 S3"
        return 1
    fi

    # 上传逻辑备份
    if [ -f "$LOGICAL_BACKUP_FILE" ]; then
        local s3_path="s3://${S3_BUCKET}/postgresql/logical/${DB_NAME}_${DATE}.sql.gz"
        if aws s3 cp "$LOGICAL_BACKUP_FILE" "$s3_path" 2>&1 | tee -a "$LOG_FILE"; then
            log_success "逻辑备份上传成功: $s3_path"
        else
            log_error "逻辑备份上传失败"
            return 1
        fi
    fi

    # 上传物理备份
    if [ -d "$PHYSICAL_BACKUP_DIR_FULL" ]; then
        local s3_path="s3://${S3_BUCKET}/postgresql/physical/${DATE}/"
        if aws s3 sync "$PHYSICAL_BACKUP_DIR_FULL" "$s3_path" 2>&1 | tee -a "$LOG_FILE"; then
            log_success "物理备份上传成功: $s3_path"
        else
            log_error "物理备份上传失败"
            return 1
        fi
    fi

    log_success "S3 上传完成"
}

# ============================================================================
# 生成备份报告
# ============================================================================
generate_report() {
    log_info "生成备份报告..."

    local report_file="${BACKUP_DIR}/backup_report_${DATE}.txt"

    cat > "$report_file" <<EOF
========================================
数据库备份报告
========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
数据库名称: $DB_NAME
备份类型: $BACKUP_TYPE
保留天数: $RETENTION_DAYS

----------------------------------------
逻辑备份信息
----------------------------------------
EOF

    if [ -f "$LOGICAL_BACKUP_FILE" ]; then
        echo "备份文件: $LOGICAL_BACKUP_FILE" >> "$report_file"
        echo "文件大小: $(du -h "$LOGICAL_BACKUP_FILE" | cut -f1)" >> "$report_file"
        echo "状态: 成功" >> "$report_file"
    else
        echo "状态: 未执行或失败" >> "$report_file"
    fi

    cat >> "$report_file" <<EOF

----------------------------------------
物理备份信息
----------------------------------------
EOF

    if [ -d "$PHYSICAL_BACKUP_DIR_FULL" ]; then
        echo "备份目录: $PHYSICAL_BACKUP_DIR_FULL" >> "$report_file"
        echo "目录大小: $(du -sh "$PHYSICAL_BACKUP_DIR_FULL" | cut -f1)" >> "$report_file"
        echo "状态: 成功" >> "$report_file"
    else
        echo "状态: 未执行或失败" >> "$report_file"
    fi

    cat >> "$report_file" <<EOF

----------------------------------------
存储空间使用情况
----------------------------------------
$(df -h "$BACKUP_DIR" | tail -1)

----------------------------------------
备份文件列表（最近10个）
----------------------------------------
$(ls -lht "$LOGICAL_BACKUP_DIR" 2>/dev/null | head -11 || echo "无逻辑备份文件")

========================================
EOF

    log_success "备份报告已生成: $report_file"

    # 显示报告内容
    cat "$report_file"
}

# ============================================================================
# 发送通知邮件
# ============================================================================
send_notification() {
    local status="$1"
    local message="$2"

    if [ -z "$NOTIFICATION_EMAIL" ]; then
        return 0
    fi

    log_info "发送通知邮件到: $NOTIFICATION_EMAIL"

    local subject="[Nautilus] 数据库备份${status}: $DB_NAME"
    local body="数据库: $DB_NAME\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n状态: ${status}\n\n${message}"

    # 使用 mail 命令发送邮件
    if command -v mail &> /dev/null; then
        echo -e "$body" | mail -s "$subject" "$NOTIFICATION_EMAIL"
        log_success "通知邮件已发送"
    else
        log_warning "mail 命令未安装，无法发送邮件通知"
    fi
}

# ============================================================================
# 显示使用帮助
# ============================================================================
show_usage() {
    cat <<EOF
用法: $0 [选项]

选项:
    -t, --type TYPE         备份类型: logical, physical, both (默认: logical)
    -d, --database NAME     数据库名称 (默认: nautilus_production)
    -u, --user USER         数据库用户 (默认: nautilus_user)
    -h, --host HOST         数据库主机 (默认: localhost)
    -p, --port PORT         数据库端口 (默认: 5432)
    -b, --backup-dir DIR    备份目录 (默认: /var/backups/postgresql)
    -r, --retention DAYS    保留天数 (默认: 30)
    -s, --s3-bucket BUCKET  S3 存储桶名称
    -e, --email EMAIL       通知邮件地址
    --help                  显示此帮助信息

环境变量:
    DB_NAME                 数据库名称
    DB_USER                 数据库用户
    DB_HOST                 数据库主机
    DB_PORT                 数据库端口
    BACKUP_DIR              备份目录
    RETENTION_DAYS          保留天数
    BACKUP_TYPE             备份类型
    S3_BUCKET               S3 存储桶
    NOTIFICATION_EMAIL      通知邮件

示例:
    # 逻辑备份
    $0 --type logical

    # 物理备份
    $0 --type physical

    # 同时执行逻辑和物理备份
    $0 --type both

    # 备份并上传到 S3
    $0 --type logical --s3-bucket my-backup-bucket

    # 自定义保留天数
    $0 --retention 60
EOF
}

# ============================================================================
# 解析命令行参数
# ============================================================================
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            -d|--database)
                DB_NAME="$2"
                shift 2
                ;;
            -u|--user)
                DB_USER="$2"
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
            -b|--backup-dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -s|--s3-bucket)
                S3_BUCKET="$2"
                shift 2
                ;;
            -e|--email)
                NOTIFICATION_EMAIL="$2"
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
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    local backup_status="成功"
    local backup_message=""

    # 解析参数
    parse_arguments "$@"

    log_info "开始数据库备份..."
    log_info "备份类型: $BACKUP_TYPE"
    log_info "数据库: $DB_NAME"
    log_info "备份目录: $BACKUP_DIR"

    # 初始化
    initialize

    # 执行备份
    case "$BACKUP_TYPE" in
        logical)
            if ! logical_backup; then
                backup_status="失败"
                backup_message="逻辑备份失败"
            fi
            ;;
        physical)
            if ! physical_backup; then
                backup_status="失败"
                backup_message="物理备份失败"
            fi
            ;;
        both)
            local logical_ok=true
            local physical_ok=true

            if ! logical_backup; then
                logical_ok=false
            fi

            if ! physical_backup; then
                physical_ok=false
            fi

            if [ "$logical_ok" = false ] || [ "$physical_ok" = false ]; then
                backup_status="部分失败"
                backup_message="逻辑备份: $logical_ok, 物理备份: $physical_ok"
            fi
            ;;
        *)
            log_error "无效的备份类型: $BACKUP_TYPE"
            show_usage
            exit 1
            ;;
    esac

    # 清理旧备份
    cleanup_old_backups

    # 上传到 S3
    if [ "$backup_status" = "成功" ]; then
        upload_to_s3
    fi

    # 生成报告
    generate_report

    # 发送通知
    send_notification "$backup_status" "$backup_message"

    if [ "$backup_status" = "成功" ]; then
        log_success "数据库备份完成！"
        exit 0
    else
        log_error "数据库备份失败: $backup_message"
        exit 1
    fi
}

# ============================================================================
# 脚本入口
# ============================================================================
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
