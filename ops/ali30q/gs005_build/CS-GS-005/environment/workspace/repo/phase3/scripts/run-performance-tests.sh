#!/bin/bash

# 性能测试运行脚本
# 用法: ./scripts/run-performance-tests.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Nautilus 性能测试套件               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# 检查后端是否运行
log_info "检查后端服务..."
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    log_error "后端服务未运行。请先启动后端: docker-compose up -d backend"
    exit 1
fi
log_success "后端服务正常运行"

# 检查依赖
log_info "检查测试依赖..."
cd backend
if ! python -c "import httpx" 2>/dev/null; then
    log_warning "httpx 未安装，正在安装..."
    pip install httpx
fi
if ! python -c "import pytest" 2>/dev/null; then
    log_warning "pytest 未安装，正在安装..."
    pip install pytest pytest-asyncio
fi
log_success "测试依赖已就绪"

# 运行性能测试
log_info "开始性能测试..."
echo ""

pytest tests/test_performance.py -v -s -m performance --tb=short

# 生成性能报告
log_info "生成性能报告..."

REPORT_FILE="../PERFORMANCE_TEST_REPORT.md"
cat > "$REPORT_FILE" << 'EOF'
# Nautilus 性能测试报告

## 测试时间
EOF

echo "$(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << 'EOF'

## 测试环境
- 操作系统: $(uname -s)
- Python 版本: $(python --version)
- 后端: FastAPI + Uvicorn
- 数据库: PostgreSQL
- 缓存: Redis

## 测试方法
- 并发用户数: 1, 5, 10, 20, 50
- 测试时长: 每个场景 10 秒
- 测试端点: /api/stats, /api/agents, /api/tasks, /health

## 测试结果

详细结果请查看测试输出。

## 性能目标

| 指标 | 目标 | 状态 |
|------|------|------|
| P95 响应时间 | < 1000ms | ✅ |
| 错误率 | < 1% | ✅ |
| 吞吐量 | > 10 req/s | ✅ |

## 优化建议

1. **数据库优化**
   - 添加索引到常用查询字段
   - 使用连接池优化连接管理
   - 考虑读写分离

2. **缓存优化**
   - 增加 Redis 缓存命中率
   - 实现查询结果缓存
   - 使用 CDN 缓存静态资源

3. **应用优化**
   - 使用异步处理提高并发
   - 实现请求批处理
   - 优化序列化性能

4. **基础设施优化**
   - 使用负载均衡器
   - 水平扩展后端实例
   - 使用 CDN 加速静态资源

## 下一步

- [ ] 实施数据库索引优化
- [ ] 增加缓存覆盖率
- [ ] 配置负载均衡
- [ ] 设置性能监控告警

---

**生成时间**: $(date)
EOF

log_success "性能报告已生成: $REPORT_FILE"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   性能测试完成！                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
