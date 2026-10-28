#!/bin/bash

# Nautilus Docker 部署脚本
# 用法: ./scripts/deploy-docker.sh [--dry-run]

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Dry-run 模式
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${BLUE}[INFO]${NC} Dry-run 模式：不会执行实际操作"
fi

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 错误处理
error_exit() {
    log_error "$1"
    exit 1
}

# 执行命令（支持 dry-run）
run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $1"
    else
        eval "$1"
    fi
}

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Nautilus Docker 部署脚本 v1.0       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Step 1: 环境检查
log_info "Step 1/10: 环境检查"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    error_exit "Docker 未安装。请先安装 Docker: https://docs.docker.com/get-docker/"
fi
log_success "Docker 已安装: $(docker --version)"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error_exit "Docker Compose 未安装。请先安装 Docker Compose"
fi
log_success "Docker Compose 已安装: $(docker-compose --version)"

# 检查 .env 文件
if [ ! -f .env ]; then
    log_warning ".env 文件不存在，从 .env.example 复制"
    run_cmd "cp .env.example .env"
    log_warning "请编辑 .env 文件，填入必需的配置"
    if [ "$DRY_RUN" = false ]; then
        read -p "按 Enter 继续..."
    fi
fi
log_success ".env 文件存在"

# Step 2: 备份当前版本
log_info "Step 2/10: 备份当前版本"

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
run_cmd "mkdir -p $BACKUP_DIR"

if docker-compose ps | grep -q "Up"; then
    log_info "备份当前运行的容器配置"
    run_cmd "docker-compose ps > $BACKUP_DIR/containers.txt"
    run_cmd "docker-compose logs --tail=100 > $BACKUP_DIR/logs.txt"
    log_success "备份完成: $BACKUP_DIR"
else
    log_info "没有运行中的容器，跳过备份"
fi

# Step 3: 拉取最新代码
log_info "Step 3/10: 拉取最新代码"

if [ -d .git ]; then
    CURRENT_BRANCH=$(git branch --show-current)
    log_info "当前分支: $CURRENT_BRANCH"
    run_cmd "git pull origin $CURRENT_BRANCH"
    log_success "代码已更新"
else
    log_warning "不是 Git 仓库，跳过代码拉取"
fi

# Step 4: 构建 Docker 镜像
log_info "Step 4/10: 构建 Docker 镜像"

run_cmd "docker-compose build --no-cache"
log_success "镜像构建完成"

# Step 5: 停止旧容器
log_info "Step 5/10: 停止旧容器"

if docker-compose ps | grep -q "Up"; then
    run_cmd "docker-compose down"
    log_success "旧容器已停止"
else
    log_info "没有运行中的容器"
fi

# Step 6: 启动新容器
log_info "Step 6/10: 启动新容器"

run_cmd "docker-compose up -d"
log_success "新容器已启动"

# Step 7: 等待服务就绪
log_info "Step 7/10: 等待服务就绪"

if [ "$DRY_RUN" = false ]; then
    log_info "等待 PostgreSQL..."
    sleep 5
    
    log_info "等待 Backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            log_success "Backend 已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            error_exit "Backend 启动超时"
        fi
        sleep 2
    done
    
    log_info "等待 Frontend..."
    for i in {1..30}; do
        if curl -s http://localhost/ > /dev/null 2>&1; then
            log_success "Frontend 已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            error_exit "Frontend 启动超时"
        fi
        sleep 2
    done
else
    log_info "[DRY-RUN] 跳过服务就绪检查"
fi

# Step 8: 数据库迁移
log_info "Step 8/10: 数据库迁移"

run_cmd "docker-compose exec -T backend alembic upgrade head"
log_success "数据库迁移完成"

# Step 9: 健康检查
log_info "Step 9/10: 健康检查"

if [ "$DRY_RUN" = false ]; then
    # 检查 Backend
    BACKEND_HEALTH=$(curl -s http://localhost:8001/health)
    if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
        log_success "Backend 健康检查通过"
    else
        log_error "Backend 健康检查失败: $BACKEND_HEALTH"
    fi
    
    # 检查 Frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
    if [ "$FRONTEND_STATUS" = "200" ]; then
        log_success "Frontend 健康检查通过"
    else
        log_error "Frontend 健康检查失败: HTTP $FRONTEND_STATUS"
    fi
    
    # 检查数据库
    DB_CHECK=$(docker-compose exec -T postgres pg_isready -U nautilus)
    if echo "$DB_CHECK" | grep -q "accepting connections"; then
        log_success "数据库健康检查通过"
    else
        log_error "数据库健康检查失败: $DB_CHECK"
    fi
    
    # 检查 Redis
    REDIS_CHECK=$(docker-compose exec -T redis redis-cli PING)
    if echo "$REDIS_CHECK" | grep -q "PONG"; then
        log_success "Redis 健康检查通过"
    else
        log_error "Redis 健康检查失败: $REDIS_CHECK"
    fi
else
    log_info "[DRY-RUN] 跳过健康检查"
fi

# Step 10: 显示部署信息
log_info "Step 10/10: 部署信息"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        部署成功！                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  前端:      http://localhost"
echo -e "  后端 API:  http://localhost:8001"
echo -e "  API 文档:  http://localhost:8001/docs"
echo -e "  Grafana:   http://localhost:3000 (admin/admin)"
echo -e "  Prometheus: http://localhost:9090"
echo ""
echo -e "${BLUE}常用命令:${NC}"
echo -e "  查看日志:   docker-compose logs -f"
echo -e "  查看状态:   docker-compose ps"
echo -e "  停止服务:   docker-compose down"
echo -e "  重启服务:   docker-compose restart"
echo ""
echo -e "${BLUE}备份位置:${NC} $BACKUP_DIR"
echo ""

# 显示容器状态
if [ "$DRY_RUN" = false ]; then
    log_info "容器状态:"
    docker-compose ps
fi

log_success "部署完成！"
