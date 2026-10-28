#!/usr/bin/env python3
"""
应用性能索引到数据库
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from utils.database import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_indexes():
    """应用性能索引"""
    engine = get_engine()

    # 读取迁移文件
    migration_file = project_root / "migrations" / "add_performance_indexes.sql"

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    logger.info(f"Reading migration file: {migration_file}")

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割 SQL 语句
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

    logger.info(f"Found {len(statements)} SQL statements to execute")

    # 执行每个语句
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            # 跳过注释和空语句
            if not statement or statement.startswith('--'):
                continue

            try:
                logger.info(f"Executing statement {i}/{len(statements)}")
                conn.execute(text(statement))
                conn.commit()
                logger.info(f"✓ Statement {i} executed successfully")
            except Exception as e:
                logger.error(f"✗ Error executing statement {i}: {e}")
                logger.error(f"Statement: {statement[:100]}...")
                # 继续执行其他语句
                continue

    logger.info("Migration completed!")
    return True


def verify_indexes():
    """验证索引是否创建成功"""
    engine = get_engine()

    logger.info("\n" + "="*60)
    logger.info("Verifying indexes...")
    logger.info("="*60)

    with engine.connect() as conn:
        # 查询所有索引
        result = conn.execute(text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """))

        indexes = result.fetchall()

        logger.info(f"\nTotal indexes: {len(indexes)}")
        logger.info("\nIndexes by table:")

        current_table = None
        for row in indexes:
            if row[1] != current_table:
                current_table = row[1]
                logger.info(f"\n{current_table}:")
            logger.info(f"  - {row[2]}")

        # 查询索引大小
        logger.info("\n" + "="*60)
        logger.info("Index sizes:")
        logger.info("="*60)

        result = conn.execute(text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 20;
        """))

        for row in result:
            logger.info(f"{row[1]}.{row[2]}: {row[3]}")


def main():
    """主函数"""
    logger.info("Starting database performance optimization...")

    # 应用索引
    if apply_indexes():
        # 验证索引
        verify_indexes()
        logger.info("\n✓ Performance indexes applied successfully!")
        return 0
    else:
        logger.error("\n✗ Failed to apply performance indexes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
