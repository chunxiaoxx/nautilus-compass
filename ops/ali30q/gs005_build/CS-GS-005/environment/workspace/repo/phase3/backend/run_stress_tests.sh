#!/bin/bash

# Nexus Protocol 压力测试启动脚本
#
# 用途: 启动Nexus服务器并运行压力测试
# 版本: 1.0.0

set -e

echo "========================================================================"
echo "Nexus Protocol 压力测试套件"
echo "========================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python环境
echo "检查Python环境..."
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到Python${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查依赖
echo ""
echo "检查依赖包..."
REQUIRED_PACKAGES=("fastapi" "uvicorn" "python-socketio" "pytest" "pytest-asyncio")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import ${package//-/_}" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}警告: 缺少以下依赖包: ${MISSING_PACKAGES[*]}${NC}"
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    echo -e "${GREEN}✓ 所有依赖已安装${NC}"
fi

# 检查服务器是否运行
echo ""
echo "检查Nexus服务器状态..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Nexus服务器已运行${NC}"
    SERVER_RUNNING=true
else
    echo -e "${YELLOW}⚠ Nexus服务器未运行${NC}"
    SERVER_RUNNING=false
fi

# 如果服务器未运行，询问是否启动
if [ "$SERVER_RUNNING" = false ]; then
    echo ""
    echo "是否启动Nexus服务器? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "启动Nexus服务器..."
        python nexus_server.py > nexus_server.log 2>&1 &
        SERVER_PID=$!
        echo "服务器PID: $SERVER_PID"

        # 等待服务器启动
        echo "等待服务器启动..."
        for i in {1..30}; do
            if curl -s http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ 服务器启动成功${NC}"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo ""
    else
        echo -e "${RED}错误: 需要运行Nexus服务器才能执行压力测试${NC}"
        exit 1
    fi
fi

# 选择测试级别
echo ""
echo "========================================================================"
echo "选择测试级别:"
echo "  1) quick    - 快速测试 (5-10分钟)"
echo "  2) standard - 标准测试 (20-30分钟)"
echo "  3) full     - 完整测试 (1-2小时)"
echo "========================================================================"
echo -n "请选择 [1-3] (默认: 1): "
read -r level_choice

case $level_choice in
    2)
        TEST_LEVEL="standard"
        ;;
    3)
        TEST_LEVEL="full"
        ;;
    *)
        TEST_LEVEL="quick"
        ;;
esac

echo -e "${GREEN}选择的测试级别: $TEST_LEVEL${NC}"

# 选择测试类型
echo ""
echo "========================================================================"
echo "选择测试类型:"
echo "  1) all        - 所有测试"
echo "  2) concurrent - 并发连接测试"
echo "  3) throughput - 消息吞吐量测试"
echo "  4) longrun    - 长时间运行测试"
echo "  5) memory     - 内存泄漏检测"
echo "========================================================================"
echo -n "请选择 [1-5] (默认: 1): "
read -r test_choice

case $test_choice in
    2)
        TEST_TYPE="concurrent"
        ;;
    3)
        TEST_TYPE="throughput"
        ;;
    4)
        TEST_TYPE="longrun"
        ;;
    5)
        TEST_TYPE="memory"
        ;;
    *)
        TEST_TYPE="all"
        ;;
esac

echo -e "${GREEN}选择的测试类型: $TEST_TYPE${NC}"

# 运行测试
echo ""
echo "========================================================================"
echo "开始压力测试"
echo "========================================================================"
echo "测试级别: $TEST_LEVEL"
echo "测试类型: $TEST_TYPE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================================"
echo ""

# 执行测试
python tests/run_stress_tests.py --level "$TEST_LEVEL" --test "$TEST_TYPE" --verbose

TEST_RESULT=$?

# 测试完成
echo ""
echo "========================================================================"
echo "测试完成"
echo "========================================================================"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过${NC}"
else
    echo -e "${RED}❌ 部分测试失败 (退出码: $TEST_RESULT)${NC}"
fi

# 如果我们启动了服务器，询问是否关闭
if [ ! -z "$SERVER_PID" ]; then
    echo ""
    echo "是否关闭Nexus服务器? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "关闭服务器 (PID: $SERVER_PID)..."
        kill $SERVER_PID
        echo -e "${GREEN}✓ 服务器已关闭${NC}"
    else
        echo "服务器继续运行 (PID: $SERVER_PID)"
        echo "使用 'kill $SERVER_PID' 手动关闭"
    fi
fi

echo ""
echo "========================================================================"
echo "查看详细报告: PERFORMANCE_REPORT.md"
echo "========================================================================"

exit $TEST_RESULT
