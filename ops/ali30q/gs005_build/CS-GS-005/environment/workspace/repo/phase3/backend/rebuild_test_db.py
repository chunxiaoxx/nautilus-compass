#!/usr/bin/env python3
"""
重建测试数据库
删除旧的测试数据库并创建新的，包含所有最新字段
"""
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from models.database import Base
from sqlalchemy import create_engine

def rebuild_test_database():
    """重建测试数据库"""

    # 测试数据库路径
    test_db_path = "test_nautilus.db"

    print("🔧 重建测试数据库...")

    # 删除旧数据库
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✅ 已删除旧数据库: {test_db_path}")

    # 创建新数据库
    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(engine)
    print(f"✅ 已创建新数据库: {test_db_path}")

    # 验证表结构
    from sqlalchemy import inspect
    inspector = inspect(engine)

    print("\n📊 数据库表结构:")
    for table_name in inspector.get_table_names():
        print(f"\n表: {table_name}")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

    print("\n✅ 测试数据库重建完成！")
    return True

if __name__ == "__main__":
    try:
        rebuild_test_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 重建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
