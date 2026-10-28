#!/bin/bash
# 性能优化一键部署脚本
# 自动执行所有性能优化措施

set -e

echo "=================================="
echo "🚀 Nautilus Phase 3 性能优化部署"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python环境
echo "📋 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3 已安装${NC}"

# 检查Redis
echo "📋 检查Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis 运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis 未运行，某些缓存功能可能不可用${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis 未安装，将使用内存缓存${NC}"
fi

# 检查PostgreSQL
echo "📋 检查数据库..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL 未安装，将使用SQLite${NC}"
fi

echo ""
echo "=================================="
echo "📦 步骤 1: 安装依赖"
echo "=================================="

# 检查requirements.txt
if [ -f "requirements.txt" ]; then
    echo "安装Python依赖..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${RED}❌ requirements.txt 未找到${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo "🗄️  步骤 2: 数据库优化"
echo "=================================="

# 添加性能索引
if [ -f "add_performance_indexes.py" ]; then
    echo "创建性能索引..."
    python3 add_performance_indexes.py
    echo -e "${GREEN}✅ 性能索引创建完成${NC}"
else
    echo -e "${YELLOW}⚠️  索引脚本未找到，跳过${NC}"
fi

echo ""
echo "=================================="
echo "🔄 步骤 3: 配置缓存"
echo "=================================="

# 检查Redis配置
if [ -f ".env" ]; then
    if grep -q "REDIS_URL" .env; then
        echo -e "${GREEN}✅ Redis配置已存在${NC}"
    else
        echo "添加Redis配置..."
        echo "" >> .env
        echo "# Redis缓存配置" >> .env
        echo "REDIS_URL=redis://localhost:6379/0" >> .env
        echo "REDIS_MAX_CONNECTIONS=50" >> .env
        echo -e "${GREEN}✅ Redis配置已添加${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env文件未找到，请手动配置${NC}"
fi

# 配置缓存TTL
if [ -f ".env" ]; then
    if ! grep -q "CACHE_TTL" .env; then
        echo "添加缓存TTL配置..."
        echo "" >> .env
        echo "# 缓存TTL配置" >> .env
        echo "CACHE_TTL_AGENT=300" >> .env
        echo "CACHE_TTL_TASK=30" >> .env
        echo "CACHE_TTL_BALANCE=60" >> .env
        echo -e "${GREEN}✅ 缓存TTL配置已添加${NC}"
    fi
fi

echo ""
echo "=================================="
echo "📊 步骤 4: 配置监控"
echo "=================================="

# 检查监控配置
if [ -f "monitoring_config.py" ]; then
    echo -e "${GREEN}✅ 监控配置已存在${NC}"
else
    echo -e "${YELLOW}⚠️  监控配置未找到${NC}"
fi

echo ""
echo "=================================="
echo "🧪 步骤 5: 运行验证"
echo "=================================="

# 运行性能验证
if [ -f "validate_performance_optimization.py" ]; then
    echo "验证性能优化..."
    python3 validate_performance_optimization.py
else
    echo -e "${YELLOW}⚠️  验证脚本未找到，跳过${NC}"
fi

echo ""
echo "=================================="
echo "📈 步骤 6: 运行基准测试"
echo "=================================="

# 询问是否运行基准测试
read -p "是否运行基准测试？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "benchmark_performance.py" ]; then
        echo "运行基准测试..."
        python3 benchmark_performance.py
    else
        echo -e "${YELLOW}⚠️  基准测试脚本未找到${NC}"
    fi
else
    echo "跳过基准测试"
fi

echo ""
echo "=================================="
echo "✅ 部署完成"
echo "=================================="
echo ""
echo "📊 性能优化措施已部署："
echo "  ✅ 数据库索引优化"
echo "  ✅ 缓存配置"
echo "  ✅ 监控配置"
echo "  ✅ 性能验证"
echo ""
echo "🚀 下一步："
echo "  1. 启动应用: python3 main.py"
echo "  2. 查看性能统计: curl http://localhost:8000/performance/stats"
echo "  3. 查看缓存统计: curl http://localhost:8000/cache/stats"
echo "  4. 查看监控指标: curl http://localhost:8000/metrics"
echo ""
echo "📚 文档："
echo "  - PERFORMANCE_QUICK_GUIDE.md - 快速参考"
echo "  - PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md - 详细报告"
echo "  - CDN_SETUP_GUIDE.md - CDN配置指南"
echo ""
echo "=================================="
