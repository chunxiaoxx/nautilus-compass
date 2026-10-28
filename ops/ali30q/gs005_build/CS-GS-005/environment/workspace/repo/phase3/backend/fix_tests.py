#!/usr/bin/env python3
"""
测试修复脚本
1. 初始化测试数据库
2. 运行测试并收集失败信息
3. 生成修复报告
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def init_test_database():
    """初始化测试数据库"""
    print("🔧 初始化测试数据库...")

    # 设置测试环境变量
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["TESTING"] = "true"

    from models.database import Base, engine

    # 删除旧数据库
    test_db_files = ["test.db", "test_nautilus.db", "test_gas_api.db"]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ 已删除旧数据库: {db_file}")

    # 创建新数据库
    Base.metadata.create_all(engine)
    print(f"✅ 已创建新数据库表")

    # 验证表结构
    from sqlalchemy import inspect
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(f"\n📊 创建的表: {', '.join(tables)}")

    return True

def run_tests_and_collect_failures():
    """
    运行测试并收集失败信息

    Security Note: Using subprocess with hardcoded command arguments.
    No user input is passed to subprocess, preventing command injection.
    """
    print("\n🧪 运行测试套件...")

    # Hardcoded command arguments (safe from command injection)
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-x"]

    # Run tests with shell=False (secure)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        shell=False  # Explicitly set to False for security
    )

    return result.stdout + result.stderr

def main():
    """主函数"""
    print("=" * 80)
    print("测试修复工具")
    print("=" * 80)

    try:
        # 步骤1: 初始化数据库
        init_test_database()

        # 步骤2: 运行测试
        output = run_tests_and_collect_failures()

        # 保存输出
        with open("test_output.txt", "w", encoding="utf-8") as f:
            f.write(output)

        print("\n✅ 测试输出已保存到 test_output.txt")

        # 显示摘要
        if "passed" in output:
            lines = output.split("\n")
            for line in lines:
                if "passed" in line or "failed" in line or "error" in line:
                    print(line)

        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
