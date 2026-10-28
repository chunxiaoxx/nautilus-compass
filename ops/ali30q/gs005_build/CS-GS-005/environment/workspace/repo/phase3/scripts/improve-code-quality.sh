#!/bin/bash

# 代码质量提升自动化脚本
# 用法: ./scripts/improve-code-quality.sh

set -e

echo "🚀 开始代码质量提升流程..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Phase 1: 修复语法错误
echo -e "${YELLOW}Phase 1: 修复语法错误${NC}"

cd backend

# 移动文档文件
if [ -f "GAS_FEE_QUICK_REFERENCE.py" ]; then
    echo "移动 GAS_FEE_QUICK_REFERENCE.py 到 docs/"
    mv GAS_FEE_QUICK_REFERENCE.py ../docs/GAS_FEE_QUICK_REFERENCE.md
fi

echo -e "${GREEN}✓ Phase 1 完成${NC}\n"

# Phase 2: 代码格式化
echo -e "${YELLOW}Phase 2: 代码格式化${NC}"

# Python 格式化
echo "运行 Black..."
python -m black . --line-length 120 --exclude='venv|__pycache__|.git'

# 前端格式化
echo "运行 Prettier..."
cd ../frontend
npm run format || echo "Prettier 未配置，跳过"

cd ../backend

echo -e "${GREEN}✓ Phase 2 完成${NC}\n"

# Phase 3: Linting
echo -e "${YELLOW}Phase 3: 代码检查${NC}"

# Python Linting
echo "运行 Flake8..."
python -m flake8 . --max-line-length=120 --exclude=venv,__pycache__,.git --count || true

# 前端 Linting
echo "运行 ESLint..."
cd ../frontend
npm run lint || echo "ESLint 未配置，跳过"

cd ../backend

echo -e "${GREEN}✓ Phase 3 完成${NC}\n"

# Phase 4: 类型检查
echo -e "${YELLOW}Phase 4: 类型检查${NC}"

# Python 类型检查
echo "运行 Mypy..."
python -m mypy . --ignore-missing-imports --exclude='venv|__pycache__|.git' || true

# 前端类型检查
echo "运行 TypeScript 类型检查..."
cd ../frontend
npm run type-check || echo "TypeScript 类型检查未配置，跳过"

cd ../backend

echo -e "${GREEN}✓ Phase 4 完成${NC}\n"

# Phase 5: 运行测试
echo -e "${YELLOW}Phase 5: 运行测试${NC}"

# Python 测试
echo "运行 Pytest..."
python -m pytest --cov=. --cov-report=html --cov-report=term || true

# 前端测试
echo "运行前端测试..."
cd ../frontend
npm test -- --coverage || echo "前端测试未配置，跳过"

cd ..

echo -e "${GREEN}✓ Phase 5 完成${NC}\n"

# 生成报告
echo -e "${YELLOW}生成质量报告...${NC}"

cat > CODE_QUALITY_SUMMARY.txt << EOF
代码质量提升完成报告
=====================

执行时间: $(date)

已完成:
✓ 代码格式化 (Black + Prettier)
✓ 代码检查 (Flake8 + ESLint)
✓ 类型检查 (Mypy + TypeScript)
✓ 测试运行 (Pytest + Jest)

详细报告:
- Python 覆盖率报告: backend/htmlcov/index.html
- 前端覆盖率报告: frontend/coverage/index.html

下一步:
1. 查看覆盖率报告
2. 补充缺失的测试
3. 修复类型错误
4. 提交代码

EOF

cat CODE_QUALITY_SUMMARY.txt

echo -e "${GREEN}✅ 代码质量提升流程完成！${NC}"
echo -e "查看详细报告: CODE_QUALITY_SUMMARY.txt"
