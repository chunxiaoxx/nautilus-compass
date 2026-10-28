#!/bin/bash

################################################################################
# Nautilus Phase 3 Backend - Staging环境部署脚本
################################################################################

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@"
}

error_exit() {
    log_error "$1"
    exit 1
}

# 主函数
main() {
    log_info "=========================================="
    log_info "🚀 Nautilus Staging环境部署"
    log_info "=========================================="
    log_info "时间: $(date)"
    log_info "=========================================="

    # 1. 检查环境
    log_info "📋 步骤1/10: 检查部署环境..."

    if [ ! -f ".env.staging" ]; then
        log_warning ".env.staging文件不存在，创建模板..."
        cat > .env.staging << 'EOF'
# 应用配置
ENVIRONMENT=staging
DEBUG=False
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://nautilus:nautilus_staging_2024@localhost:5432/nautilus_staging

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 区块链配置
BLOCKCHAIN_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
BLOCKCHAIN_NETWORK=sepolia

# 监控配置
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# API配置
API_HOST=0.0.0.0
API_PORT=8001
EOF
        log_warning "请编辑.env.staging文件，填入正确的配置"
        log_warning "特别是BLOCKCHAIN_RPC_URL需要填入有效的Infura密钥"
        read -p "按Enter继续..."
    fi

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker未安装，请先安装Docker"
    fi

    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose未安装，请先安装Docker Compose"
    fi

    log_success "环境检查通过"

    # 2. 拉取最新代码
    log_info "📥 步骤2/10: 拉取最新代码..."
    git pull origin master || log_warning "Git pull失败，继续使用当前代码"
    log_success "代码更新完成"

    # 3. 停止旧服务
    log_info "🛑 步骤3/10: 停止旧服务..."
    docker-compose -f docker-compose.staging.yml down || true
    log_success "旧服务已停止"

    # 4. 清理旧数据（可选）
    read -p "是否清理旧数据？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_warning "清理旧数据..."
        docker volume rm nautilus_postgres_data_staging 2>/dev/null || true
        docker volume rm nautilus_redis_data_staging 2>/dev/null || true
        log_success "旧数据已清理"
    fi

    # 5. 构建镜像
    log_info "🔨 步骤4/10: 构建Docker镜像..."
    docker-compose -f docker-compose.staging.yml build --no-cache
    log_success "镜像构建完成"

    # 6. 启动数据库和Redis
    log_info "🗄️ 步骤5/10: 启动数据库和Redis..."
    docker-compose -f docker-compose.staging.yml up -d postgres redis
    log_success "数据库和Redis已启动"

    # 7. 等待数据库启动
    log_info "⏳ 步骤6/10: 等待数据库启动..."
    sleep 10

    # 检查数据库连接
    for i in {1..30}; do
        if docker exec nautilus-postgres-staging pg_isready -U nautilus > /dev/null 2>&1; then
            log_success "数据库已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            error_exit "数据库启动超时"
        fi
        echo -n "."
        sleep 2
    done

    # 8. 运行数据库迁移
    log_info "🔄 步骤7/10: 运行数据库迁移..."
    docker-compose -f docker-compose.staging.yml run --rm backend python -c "
from models.database import init_db
init_db()
print('Database initialized successfully')
" || log_warning "数据库迁移可能失败，请检查"
    log_success "数据库迁移完成"

    # 9. 启动所有服务
    log_info "🚀 步骤8/10: 启动所有服务..."
    docker-compose -f docker-compose.staging.yml up -d
    log_success "所有服务已启动"

    # 10. 等待服务启动
    log_info "⏳ 步骤9/10: 等待服务启动..."
    sleep 15

    # 11. 健康检查
    log_info "🏥 步骤10/10: 执行健康检查..."
    for i in {1..30}; do
        if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
            log_success "服务健康检查通过！"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "健康检查超时"
            log_error "查看日志:"
            docker-compose -f docker-compose.staging.yml logs --tail 50 backend
            exit 1
        fi
        echo -n "."
        sleep 2
    done

    # 12. 显示服务状态
    echo ""
    log_info "=========================================="
    log_info "📊 服务状态"
    log_info "=========================================="
    docker-compose -f docker-compose.staging.yml ps

    echo ""
    log_success "=========================================="
    log_success "✅ Staging环境部署完成！"
    log_success "=========================================="
    echo ""
    log_info "🔗 访问地址:"
    log_info "  - API: http://localhost:8001"
    log_info "  - Health: http://localhost:8001/health"
    log_info "  - Docs: http://localhost:8001/docs"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    log_info "📝 常用命令:"
    log_info "  - 查看日志: docker-compose -f docker-compose.staging.yml logs -f backend"
    log_info "  - 停止服务: docker-compose -f docker-compose.staging.yml down"
    log_info "  - 重启服务: docker-compose -f docker-compose.staging.yml restart"
    echo ""
    log_info "🧪 运行测试:"
    log_info "  - 单元测试: docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/ -v"
    log_info "  - 健康检查: curl http://localhost:8001/health"
    echo ""
    log_success "=========================================="
}

# 执行主函数
main "$@"
