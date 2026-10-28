#!/bin/bash
# Application Performance Verification Script for Linux/Mac
# 应用性能验证脚本 (Linux/Mac)

set -e

echo "================================================================================"
echo "NAUTILUS PHASE 3 - 应用性能验证"
echo "================================================================================"
echo ""

cd "$(dirname "$0")"

echo "[1/7] 检查Python环境..."
python3 --version || python --version

echo ""
echo "[2/7] 检查依赖..."
python3 -c "import fastapi, sqlalchemy, uvicorn" 2>/dev/null || {
    echo "警告: 部分依赖未安装，正在安装..."
    pip3 install -r requirements.txt || pip install -r requirements.txt
}

echo ""
echo "[3/7] 运行性能验证脚本..."
echo ""
python3 verify_application_performance.py || python verify_application_performance.py

echo ""
echo "================================================================================"
echo "验证完成!"
echo "================================================================================"
echo ""
echo "查看详细报告: APPLICATION_PERFORMANCE_REPORT.md"
echo ""
