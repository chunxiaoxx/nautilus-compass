#!/bin/bash
# Performance Optimization Verification Script
# 验证所有性能优化是否正确实施

echo "=========================================="
echo "性能优化验证脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} 文件存在: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} 文件缺失: $1"
        ((FAILED++))
        return 1
    fi
}

check_content() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} 内容验证通过: $1 包含 '$2'"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} 内容验证失败: $1 不包含 '$2'"
        ((FAILED++))
        return 1
    fi
}

echo "1. 检查新增工具文件..."
echo "----------------------------------------"
check_file "utils/cache.py"
check_file "utils/performance_middleware.py"
check_file "utils/pool_monitor.py"
check_file "tests/test_performance.py"
check_file "add_performance_indexes.py"
check_file "analyze_query_performance.py"
check_file "benchmark_performance.py"
echo ""

echo "2. 检查文档文件..."
echo "----------------------------------------"
check_file "PERFORMANCE_OPTIMIZATION_REPORT.md"
check_file "PERFORMANCE_QUICK_START.txt"
check_file "PERFORMANCE_OPTIMIZATION_COMPLETE.md"
echo ""

echo "3. 验证数据库模型优化..."
echo "----------------------------------------"
check_content "models/database.py" "index=True"
check_content "models/database.py" "__table_args__"
echo ""

echo "4. 验证API优化..."
echo "----------------------------------------"
check_content "api/rewards.py" "func.sum"
check_content "api/rewards.py" "start_time = time.time()"
check_content "api/tasks.py" "Slow query"
check_content "api/agents.py" "elapsed = time.time()"
echo ""

echo "5. 验证主应用配置..."
echo "----------------------------------------"
check_content "main.py" "PerformanceMonitoringMiddleware"
check_content "main.py" "RequestCounterMiddleware"
check_content "main.py" "get_cache"
check_content "main.py" "/cache/stats"
check_content "main.py" "/performance/stats"
check_content "main.py" "/database/pool"
echo ""

echo "6. 验证数据库配置..."
echo "----------------------------------------"
check_content "utils/database.py" "get_engine"
check_content "utils/database.py" "DATABASE_POOL_SIZE"
check_content "utils/database.py" "pool_recycle"
echo ""

echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}${PASSED}${NC}"
echo -e "失败: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有验证通过！性能优化已正确实施。${NC}"
    echo ""
    echo "下一步操作："
    echo "1. 运行索引迁移: python add_performance_indexes.py"
    echo "2. 运行性能测试: pytest tests/test_performance.py -v"
    echo "3. 运行基准测试: python benchmark_performance.py"
    exit 0
else
    echo -e "${RED}✗ 有 ${FAILED} 项验证失败，请检查。${NC}"
    exit 1
fi
