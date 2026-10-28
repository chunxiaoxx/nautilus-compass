"""
数据库迁移脚本 - 添加区块链集成字段
Phase 2: Blockchain Integration

运行此脚本以添加区块链相关字段到现有数据库
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.database import Base
from utils.database import get_database_url

def migrate_database():
    """添加区块链字段到现有表"""

    database_url = get_database_url()
    engine = create_engine(database_url)

    print("🚀 开始数据库迁移...")
    print(f"📊 数据库: {database_url}")

    with engine.connect() as conn:
        try:
            # 添加Task表的区块链字段
            print("\n📝 添加Task表的区块链字段...")

            migrations = [
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockchain_tx_hash VARCHAR(66)",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockchain_accept_tx VARCHAR(66)",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockchain_submit_tx VARCHAR(66)",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockchain_complete_tx VARCHAR(66)",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockchain_status VARCHAR(20)",

                # 添加索引
                "CREATE INDEX IF NOT EXISTS idx_tasks_blockchain_tx ON tasks(blockchain_tx_hash)",

                # 添加Agent表的区块链字段
                "ALTER TABLE agents ADD COLUMN IF NOT EXISTS blockchain_registered BOOLEAN DEFAULT FALSE",
                "ALTER TABLE agents ADD COLUMN IF NOT EXISTS blockchain_tx_hash VARCHAR(66)",
                "ALTER TABLE agents ADD COLUMN IF NOT EXISTS blockchain_address VARCHAR(42)",
            ]

            for migration in migrations:
                try:
                    conn.execute(text(migration))
                    print(f"✅ {migration[:50]}...")
                except Exception as e:
                    print(f"⚠️ {migration[:50]}... (可能已存在)")

            conn.commit()

            print("\n✅ 数据库迁移完成！")
            print("\n📊 新增字段:")
            print("  Task表:")
            print("    - blockchain_tx_hash: 任务发布交易哈希")
            print("    - blockchain_accept_tx: 任务接受交易哈希")
            print("    - blockchain_submit_tx: 任务提交交易哈希")
            print("    - blockchain_complete_tx: 任务完成交易哈希")
            print("    - blockchain_status: 区块链同步状态")
            print("\n  Agent表:")
            print("    - blockchain_registered: 是否在链上注册")
            print("    - blockchain_tx_hash: Agent注册交易哈希")
            print("    - blockchain_address: Agent区块链地址")

        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Nautilus Phase 2 - 区块链集成数据库迁移")
    print("=" * 60)

    try:
        migrate_database()
        print("\n" + "=" * 60)
        print("🎉 迁移成功完成！")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 迁移失败: {e}")
        print("=" * 60)
        sys.exit(1)
