#!/usr/bin/env python3
"""
应用性能优化索引到数据库

使用方法:
    python scripts/apply_performance_indexes.py
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_indexes():
    """应用性能优化索引"""

    # 获取数据库连接
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL 环境变量未设置")
        return False

    logger.info(f"连接到数据库: {database_url.split('@')[1] if '@' in database_url else 'local'}")

    try:
        engine = create_engine(database_url)

        # 读取 SQL 文件
        sql_file = project_root / "migrations" / "add_performance_indexes.sql"
        if not sql_file.exists():
            logger.error(f"SQL 文件不存在: {sql_file}")
            return False

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割 SQL 语句
        statements = [
            stmt.strip()
            for stmt in sql_content.split(';')
            if stmt.strip() and not stmt.strip().startswith('--')
        ]

        # 执行每个语句
        with engine.connect() as conn:
            logger.info("开始创建索引...")

            for i, statement in enumerate(statements, 1):
                # 跳过注释和空语句
                if not statement or statement.startswith('--'):
                    continue

                # 跳过 SELECT 查询（验证查询）
                if statement.upper().startswith('SELECT'):
                    continue

                try:
                    logger.info(f"执行语句 {i}/{len(statements)}: {statement[:80]}...")
                    conn.execute(text(statement))
                    conn.commit()
                    logger.info(f"✓ 语句 {i} 执行成功")
                except Exception as e:
                    logger.warning(f"✗ 语句 {i} 执行失败: {e}")
                    # 继续执行其他语句
                    continue

            logger.info("索引创建完成！")

            # 验证索引
            logger.info("\n验证索引创建情况...")
            result = conn.execute(text("""
                SELECT
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                    AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """))

            indexes = result.fetchall()
            logger.info(f"\n当前数据库中的索引 (共 {len(indexes)} 个):")

            current_table = None
            for table, index in indexes:
                if table != current_table:
                    logger.info(f"\n表: {table}")
                    current_table = table
                logger.info(f"  - {index}")

        return True

    except Exception as e:
        logger.error(f"应用索引失败: {e}")
        return False


def check_index_usage():
    """检查索引使用情况"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            logger.info("\n索引使用统计:")
            result = conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan AS scans,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 20;
            """))

            rows = result.fetchall()
            if rows:
                logger.info(f"\n{'表名':<20} {'索引名':<40} {'扫描次数':<12} {'大小':<10}")
                logger.info("-" * 85)
                for schema, table, index, scans, size in rows:
                    logger.info(f"{table:<20} {index:<40} {scans:<12} {size:<10}")
            else:
                logger.info("暂无索引使用统计数据")

    except Exception as e:
        logger.error(f"检查索引使用情况失败: {e}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Nautilus 性能优化 - 索引创建脚本")
    logger.info("=" * 60)

    success = apply_indexes()

    if success:
        logger.info("\n✓ 索引应用成功！")
        check_index_usage()
    else:
        logger.error("\n✗ 索引应用失败")
        sys.exit(1)
