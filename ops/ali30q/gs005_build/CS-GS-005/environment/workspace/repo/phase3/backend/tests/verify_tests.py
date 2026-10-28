#!/usr/bin/env python
"""
测试验证脚本 - 验证测试文件的完整性和正确性

使用方法:
    python verify_tests.py
"""

import sys
import os
import ast
import importlib.util

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def check_file_exists(filepath):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ 文件存在: {filepath}")
        return True
    else:
        print(f"❌ 文件不存在: {filepath}")
        return False


def check_syntax(filepath):
    """检查Python语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"✅ 语法正确: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误: {filepath}")
        print(f"   行 {e.lineno}: {e.msg}")
        return False


def check_imports(filepath):
    """检查导入是否正确"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", filepath)
        if spec is None:
            print(f"❌ 无法加载模块: {filepath}")
            return False

        module = importlib.util.module_from_spec(spec)
        # 不执行，只检查是否能加载
        print(f"✅ 导入检查通过: {filepath}")
        return True
    except Exception as e:
        print(f"❌ 导入错误: {filepath}")
        print(f"   {e}")
        return False


def count_test_functions(filepath):
    """统计测试函数数量"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)
        test_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node.name)

        print(f"✅ 找到 {len(test_functions)} 个测试函数:")
        for i, func_name in enumerate(test_functions, 1):
            print(f"   {i}. {func_name}")

        return len(test_functions)
    except Exception as e:
        print(f"❌ 统计测试函数失败: {e}")
        return 0


def check_test_structure(filepath):
    """检查测试结构"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)

        # 检查是否有 pytest.mark.asyncio 装饰器
        has_asyncio_decorator = False
        has_cleanup = False
        has_assertions = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    # 检查装饰器
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Attribute):
                            if decorator.attr == 'asyncio':
                                has_asyncio_decorator = True

                    # 检查是否有 try-finally
                    for item in ast.walk(node):
                        if isinstance(item, ast.Try):
                            if item.finalbody:
                                has_cleanup = True
                        if isinstance(item, ast.Assert):
                            has_assertions = True

        print(f"✅ 测试结构检查:")
        print(f"   - 异步装饰器: {'✅' if has_asyncio_decorator else '❌'}")
        print(f"   - 资源清理: {'✅' if has_cleanup else '❌'}")
        print(f"   - 断言语句: {'✅' if has_assertions else '❌'}")

        return has_asyncio_decorator and has_cleanup and has_assertions
    except Exception as e:
        print(f"❌ 检查测试结构失败: {e}")
        return False


def check_dependencies():
    """检查依赖是否安装"""
    dependencies = [
        'pytest',
        'pytest_asyncio',
        'socketio',
        'aiohttp',
    ]

    all_installed = True
    print("\n检查依赖:")

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装")
            all_installed = False

    if not all_installed:
        print("\n安装缺失的依赖:")
        print("  pip install pytest pytest-asyncio python-socketio aiohttp")

    return all_installed


def check_nexus_files():
    """检查 Nexus 相关文件"""
    base_path = os.path.join(os.path.dirname(__file__), '..')

    files_to_check = [
        'nexus_server.py',
        'nexus_protocol/types.py',
        'nexus_protocol/__init__.py',
    ]

    agent_engine_path = os.path.join(os.path.dirname(__file__), '..', '..', 'agent-engine')
    agent_files = [
        'nexus_client.py',
    ]

    all_exist = True
    print("\n检查 Nexus 文件:")

    for file in files_to_check:
        filepath = os.path.join(base_path, file)
        if os.path.exists(filepath):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 不存在")
            all_exist = False

    for file in agent_files:
        filepath = os.path.join(agent_engine_path, file)
        if os.path.exists(filepath):
            print(f"✅ agent-engine/{file}")
        else:
            print(f"❌ agent-engine/{file} 不存在")
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("="*80)
    print("测试验证脚本")
    print("="*80 + "\n")

    test_file = os.path.join(os.path.dirname(__file__), 'test_workflow_integration.py')

    results = []

    # 1. 检查文件存在
    print("1. 检查测试文件")
    print("-" * 80)
    results.append(check_file_exists(test_file))
    print()

    # 2. 检查语法
    print("2. 检查语法")
    print("-" * 80)
    results.append(check_syntax(test_file))
    print()

    # 3. 统计测试函数
    print("3. 统计测试函数")
    print("-" * 80)
    test_count = count_test_functions(test_file)
    results.append(test_count >= 8)
    print()

    # 4. 检查测试结构
    print("4. 检查测试结构")
    print("-" * 80)
    results.append(check_test_structure(test_file))
    print()

    # 5. 检查依赖
    print("5. 检查依赖")
    print("-" * 80)
    results.append(check_dependencies())
    print()

    # 6. 检查 Nexus 文件
    print("6. 检查 Nexus 文件")
    print("-" * 80)
    results.append(check_nexus_files())
    print()

    # 总结
    print("="*80)
    print("验证总结")
    print("="*80)

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")

    if all(results):
        print("\n✅ 所有检查通过！测试文件已准备就绪。")
        print("\n下一步:")
        print("  1. 启动 Nexus Server: python nexus_server.py")
        print("  2. 运行测试: python tests/run_workflow_tests.py")
        return 0
    else:
        print("\n❌ 部分检查失败，请修复上述问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
