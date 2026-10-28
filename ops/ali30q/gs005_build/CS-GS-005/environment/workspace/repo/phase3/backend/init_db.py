#!/usr/bin/env python3
"""
简单的数据库初始化脚本
用于Staging环境部署
"""

import os
import sys
from sqlalchemy import create_engine, text

# 从环境变量或使用默认值
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://nautilus:nautilus_staging_2024@localhost:5432/nautilus_staging'
)

def init_database():
    """初始化数据库"""
    print("🔄 开始初始化数据库...")
    print(f"📍 数据库URL: {DATABASE_URL.replace('nautilus_staging_2024', '***')}")

    try:
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)

        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功!")
            print(f"📊 PostgreSQL版本: {version.split(',')[0]}")

        # 导入模型并创建表
        print("🔄 导入数据库模型...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from models.database import Base

        print("🔄 创建数据库表...")
        Base.metadata.create_all(bind=engine)

        # 检查创建的表
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ 成功创建 {len(tables)} 个表:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  没有创建任何表")

        print("✅ 数据库初始化完成!")
        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
