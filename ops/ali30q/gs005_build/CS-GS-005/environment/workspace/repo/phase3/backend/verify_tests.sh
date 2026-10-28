#!/bin/bash
# Nautilus 测试快速验证脚本

echo "=========================================="
echo "Nautilus 测试文件验证"
echo "=========================================="

# 检查测试目录
echo -e "\n1. 检查测试目录结构..."
if [ -d "tests/e2e" ]; then
    echo "✓ E2E 测试目录存在"
    ls -1 tests/e2e/*.py 2>/dev/null | wc -l | xargs echo "  - 文件数:"
else
    echo "✗ E2E 测试目录不存在"
fi

if [ -d "tests/performance" ]; then
    echo "✓ 性能测试目录存在"
    ls -1 tests/performance/*.py 2>/dev/null | wc -l | xargs echo "  - 文件数:"
else
    echo "✗ 性能测试目录不存在"
fi

if [ -d "tests/security" ]; then
    echo "✓ 安全测试目录存在"
    ls -1 tests/security/*.py 2>/dev/null | wc -l | xargs echo "  - 文件数:"
else
    echo "✗ 安全测试目录不存在"
fi

# 检查测试脚本
echo -e "\n2. 检查测试脚本..."
for script in "tests/run_all_tests.py" "tests/run_quick_tests.py" "tests/analyze_coverage.py"; do
    if [ -f "$script" ]; then
        echo "✓ $script"
    else
        echo "✗ $script 不存在"
    fi
done

# 检查文档
echo -e "\n3. 检查文档..."
for doc in "TEST_COMPLETION_REPORT.md" "TESTING_GUIDE.md" "TESTING_SUMMARY.md"; do
    if [ -f "$doc" ]; then
        echo "✓ $doc"
    else
        echo "✗ $doc 不存在"
    fi
done

# 统计测试用例
echo -e "\n4. 统计测试用例..."
echo "总测试文件数: $(find tests/ -name 'test_*.py' | wc -l)"
echo "新增 E2E 测试: $(grep -r "def test_" tests/e2e/ 2>/dev/null | wc -l)"
echo "新增性能测试: $(grep -r "def test_" tests/performance/ 2>/dev/null | wc -l)"
echo "新增安全测试: $(grep -r "def test_" tests/security/ 2>/dev/null | wc -l)"

# 检查依赖
echo -e "\n5. 检查关键依赖..."
python -c "import pytest; print('✓ pytest')" 2>/dev/null || echo "✗ pytest 未安装"
python -c "import httpx; print('✓ httpx')" 2>/dev/null || echo "✗ httpx 未安装"
python -c "import asteval; print('✓ asteval')" 2>/dev/null || echo "✗ asteval 未安装"
python -c "import pytest_cov; print('✓ pytest-cov')" 2>/dev/null || echo "✗ pytest-cov 未安装"

echo -e "\n=========================================="
echo "验证完成"
echo "=========================================="
