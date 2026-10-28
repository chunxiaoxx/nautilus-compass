#!/bin/bash
# ============================================================================
# 生产数据库初始化脚本
# ============================================================================
# 功能: 创建数据库、用户、权限配置、初始数据导入
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
DB_PASSWORD="${DB_PASSWORD:-}"
DB_READONLY_USER="${DB_READONLY_USER:-nautilus_readonly}"
DB_READONLY_PASSWORD="${DB_READONLY_PASSWORD:-}"
REPLICATION_USER="${REPLICATION_USER:-replicator}"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# ============================================================================
# 检查必需的环境变量
# ============================================================================
check_environment() {
    log_info "检查环境变量..."

    if [ -z "$DB_PASSWORD" ]; then
        log_error "DB_PASSWORD 环境变量未设置"
        echo "请设置: export DB_PASSWORD='your_secure_password'"
        exit 1
    fi

    if [ -z "$DB_READONLY_PASSWORD" ]; then
        log_warning "DB_READONLY_PASSWORD 未设置，将跳过只读用户创建"
    fi

    if [ -z "$REPLICATION_PASSWORD" ]; then
        log_warning "REPLICATION_PASSWORD 未设置，将跳过复制用户创建"
    fi

    log_success "环境变量检查完成"
}

# ============================================================================
# 检查 PostgreSQL 是否运行
# ============================================================================
check_postgres() {
    log_info "检查 PostgreSQL 服务状态..."

    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        log_error "PostgreSQL 服务未运行或无法连接"
        log_info "请启动 PostgreSQL: sudo systemctl start postgresql"
        exit 1
    fi

    log_success "PostgreSQL 服务正常运行"
}

# ============================================================================
# 创建数据库
# ============================================================================
create_database() {
    log_info "创建数据库: $DB_NAME"

    # 检查数据库是否已存在
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_warning "数据库 $DB_NAME 已存在，跳过创建"
        return 0
    fi

    # 创建数据库
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE DATABASE $DB_NAME
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE $DB_NAME IS 'Nautilus Production Database';
EOF

    log_success "数据库 $DB_NAME 创建成功"
}

# ============================================================================
# 创建应用用户
# ============================================================================
create_app_user() {
    log_info "创建应用用户: $DB_USER"

    # 检查用户是否已存在
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        log_warning "用户 $DB_USER 已存在，更新密码"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
ALTER USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
EOF
    else
        # 创建用户
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE USER $DB_USER WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    ENCRYPTED PASSWORD '$DB_PASSWORD';

COMMENT ON ROLE $DB_USER IS 'Nautilus Application User';
EOF
        log_success "用户 $DB_USER 创建成功"
    fi
}

# ============================================================================
# 授予应用用户权限
# ============================================================================
grant_app_permissions() {
    log_info "授予应用用户权限..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" <<EOF
-- 授予数据库连接权限
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;

-- 授予 schema 权限
GRANT ALL ON SCHEMA public TO $DB_USER;

-- 授予所有表的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;

-- 授予所有序列的权限
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- 授予所有函数的权限
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

-- 设置默认权限（对未来创建的对象）
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;
EOF

    log_success "应用用户权限授予完成"
}

# ============================================================================
# 创建只读用户
# ============================================================================
create_readonly_user() {
    if [ -z "$DB_READONLY_PASSWORD" ]; then
        log_warning "跳过只读用户创建"
        return 0
    fi

    log_info "创建只读用户: $DB_READONLY_USER"

    # 检查用户是否已存在
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_READONLY_USER'" | grep -q 1; then
        log_warning "用户 $DB_READONLY_USER 已存在，更新密码"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
ALTER USER $DB_READONLY_USER WITH ENCRYPTED PASSWORD '$DB_READONLY_PASSWORD';
EOF
    else
        # 创建只读用户
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE USER $DB_READONLY_USER WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    ENCRYPTED PASSWORD '$DB_READONLY_PASSWORD';

COMMENT ON ROLE $DB_READONLY_USER IS 'Nautilus Read-Only User';
EOF
        log_success "用户 $DB_READONLY_USER 创建成功"
    fi

    # 授予只读权限
    log_info "授予只读用户权限..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" <<EOF
-- 授予数据库连接权限
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_READONLY_USER;

-- 授予 schema 使用权限
GRANT USAGE ON SCHEMA public TO $DB_READONLY_USER;

-- 授予所有表的 SELECT 权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $DB_READONLY_USER;

-- 授予所有序列的 SELECT 权限
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO $DB_READONLY_USER;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $DB_READONLY_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO $DB_READONLY_USER;
EOF

    log_success "只读用户权限授予完成"
}

# ============================================================================
# 创建复制用户
# ============================================================================
create_replication_user() {
    if [ -z "$REPLICATION_PASSWORD" ]; then
        log_warning "跳过复制用户创建"
        return 0
    fi

    log_info "创建复制用户: $REPLICATION_USER"

    # 检查用户是否已存在
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$REPLICATION_USER'" | grep -q 1; then
        log_warning "用户 $REPLICATION_USER 已存在，更新密码"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
ALTER USER $REPLICATION_USER WITH ENCRYPTED PASSWORD '$REPLICATION_PASSWORD';
EOF
    else
        # 创建复制用户
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<EOF
CREATE USER $REPLICATION_USER WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    REPLICATION
    ENCRYPTED PASSWORD '$REPLICATION_PASSWORD';

COMMENT ON ROLE $REPLICATION_USER IS 'Nautilus Replication User';
EOF
        log_success "用户 $REPLICATION_USER 创建成功"
    fi
}

# ============================================================================
# 安装扩展
# ============================================================================
install_extensions() {
    log_info "安装 PostgreSQL 扩展..."

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" <<EOF
-- 性能监控扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- UUID 生成扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 加密扩展
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 全文搜索扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 表膨胀检查扩展
CREATE EXTENSION IF NOT EXISTS pgstattuple;
EOF

    log_success "扩展安装完成"
}

# ============================================================================
# 创建 WAL 归档目录
# ============================================================================
create_wal_archive_dir() {
    log_info "创建 WAL 归档目录..."

    WAL_ARCHIVE_DIR="/var/lib/postgresql/wal_archive"

    if [ ! -d "$WAL_ARCHIVE_DIR" ]; then
        sudo mkdir -p "$WAL_ARCHIVE_DIR"
        sudo chown postgres:postgres "$WAL_ARCHIVE_DIR"
        sudo chmod 700 "$WAL_ARCHIVE_DIR"
        log_success "WAL 归档目录创建成功: $WAL_ARCHIVE_DIR"
    else
        log_warning "WAL 归档目录已存在: $WAL_ARCHIVE_DIR"
    fi
}

# ============================================================================
# 运行数据库迁移
# ============================================================================
run_migrations() {
    log_info "运行数据库迁移..."

    # 检查是否存在 Alembic
    if [ -f "alembic.ini" ]; then
        log_info "使用 Alembic 运行迁移..."
        alembic upgrade head
        log_success "数据库迁移完成"
    else
        log_warning "未找到 alembic.ini，跳过迁移"
    fi
}

# ============================================================================
# 导入初始数据
# ============================================================================
import_initial_data() {
    log_info "导入初始数据..."

    INIT_DATA_FILE="scripts/initial_data.sql"

    if [ -f "$INIT_DATA_FILE" ]; then
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$INIT_DATA_FILE"
        log_success "初始数据导入完成"
    else
        log_warning "未找到初始数据文件: $INIT_DATA_FILE"
    fi
}

# ============================================================================
# 验证数据库配置
# ============================================================================
verify_database() {
    log_info "验证数据库配置..."

    # 测试连接
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        log_success "数据库连接测试成功"
    else
        log_error "数据库连接测试失败"
        exit 1
    fi

    # 显示数据库信息
    log_info "数据库信息:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" <<EOF
SELECT
    'Database' as type,
    datname as name,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname = '$DB_NAME';

SELECT
    'Extensions' as info,
    extname as name,
    extversion as version
FROM pg_extension
WHERE extname NOT IN ('plpgsql');
EOF
}

# ============================================================================
# 显示连接信息
# ============================================================================
show_connection_info() {
    log_success "数据库初始化完成！"
    echo ""
    echo "=========================================="
    echo "数据库连接信息"
    echo "=========================================="
    echo "数据库名称: $DB_NAME"
    echo "主机地址: $DB_HOST"
    echo "端口: $DB_PORT"
    echo "应用用户: $DB_USER"
    echo ""
    echo "连接字符串:"
    echo "postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
    echo "环境变量配置:"
    echo "export DATABASE_URL=\"postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME\""
    echo "=========================================="
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    log_info "开始初始化生产数据库..."
    echo ""

    # 执行初始化步骤
    check_environment
    check_postgres
    create_database
    create_app_user
    grant_app_permissions
    create_readonly_user
    create_replication_user
    install_extensions
    create_wal_archive_dir
    run_migrations
    import_initial_data
    verify_database
    show_connection_info

    log_success "所有初始化步骤完成！"
}

# ============================================================================
# 脚本入口
# ============================================================================
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
