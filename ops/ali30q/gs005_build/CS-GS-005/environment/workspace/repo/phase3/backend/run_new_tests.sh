#!/bin/bash
# 测试覆盖率提升验证脚本
# 运行新增的测试并生成覆盖率报告

echo "=========================================="
echo "测试覆盖率提升验证脚本"
echo "=========================================="
echo ""

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}错误: pytest未安装${NC}"
    echo "请运行: pip install pytest pytest-cov"
    exit 1
fi

echo -e "${YELLOW}步骤 1: 运行新增的认证API测试${NC}"
pytest tests/test_api_auth_extended.py -v --tb=short
AUTH_RESULT=$?

echo ""
echo -e "${YELLOW}步骤 2: 运行新增的奖励API测试${NC}"
pytest tests/test_api_rewards_extended.py -v --tb=short
REWARDS_RESULT=$?

echo ""
echo -e "${YELLOW}步骤 3: 运行新增的任务API测试${NC}"
pytest tests/test_api_tasks_extended.py -v --tb=short
TASKS_RESULT=$?

echo ""
echo -e "${YELLOW}步骤 4: 运行新增的区块链服务Mock测试${NC}"
pytest tests/test_blockchain_service_mock.py -v --tb=short
BLOCKCHAIN_RESULT=$?

echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="

if [ $AUTH_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 认证API测试: 通过${NC}"
else
    echo -e "${RED}✗ 认证API测试: 失败${NC}"
fi

if [ $REWARDS_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 奖励API测试: 通过${NC}"
else
    echo -e "${RED}✗ 奖励API测试: 失败${NC}"
fi

if [ $TASKS_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 任务API测试: 通过${NC}"
else
    echo -e "${RED}✗ 任务API测试: 失败${NC}"
fi

if [ $BLOCKCHAIN_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 区块链服务测试: 通过${NC}"
else
    echo -e "${RED}✗ 区块链服务测试: 失败${NC}"
fi

echo ""
echo -e "${YELLOW}步骤 5: 生成覆盖率报告${NC}"
pytest tests/test_api_auth_extended.py tests/test_api_rewards_extended.py tests/test_api_tasks_extended.py tests/test_blockchain_service_mock.py \
    --cov=api --cov=blockchain --cov-report=term-missing --cov-report=html -v

echo ""
echo "=========================================="
echo "覆盖率报告已生成"
echo "=========================================="
echo "HTML报告位置: htmlcov/index.html"
echo ""
echo "查看报告:"
echo "  Windows: start htmlcov/index.html"
echo "  Mac: open htmlcov/index.html"
echo "  Linux: xdg-open htmlcov/index.html"
echo ""

# 计算总体结果
TOTAL_RESULT=$((AUTH_RESULT + REWARDS_RESULT + TASKS_RESULT + BLOCKCHAIN_RESULT))

if [ $TOTAL_RESULT -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "所有新增测试通过！"
    echo "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "部分测试失败，请检查错误信息"
    echo "==========================================${NC}"
    exit 1
fi
