"""
数据库性能优化工具集
包含查询优化、缓存管理等实用函数
"""
import logging
from typing import Optional, List, Dict, Any
from functools import wraps
import time

from sqlalchemy.orm import Session
from sqlalchemy import text

from utils.cache import get_cache
from utils.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


def query_with_cache(
    cache_key: str,
    query_func,
    ttl: int = 300,
    use_redis: bool = False
):
    """
    带缓存的查询包装器

    Args:
        cache_key: 缓存键
        query_func: 查询函数
        ttl: 缓存过期时间（秒）
        use_redis: 是否使用 Redis 缓存

    Returns:
        查询结果
    """
    # 选择缓存后端
    if use_redis:
        cache = get_redis_cache()
        if cache is None:
            logger.warning("Redis cache not available, falling back to memory cache")
            cache = get_cache()
    else:
        cache = get_cache()

    # 尝试从缓存获取
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit: {cache_key}")
        return cached_result

    # 执行查询
    logger.debug(f"Cache miss: {cache_key}")
    result = query_func()

    # 缓存结果
    cache.set(cache_key, result, ttl)

    return result


def invalidate_cache_pattern(pattern: str, use_redis: bool = False):
    """
    使匹配模式的缓存失效

    Args:
        pattern: 缓存键模式
        use_redis: 是否使用 Redis 缓存
    """
    if use_redis:
        cache = get_redis_cache()
        if cache:
            keys = cache.keys(f"{pattern}*")
            if keys:
                cache.delete(*keys)
                logger.info(f"Invalidated {len(keys)} Redis cache entries matching '{pattern}'")
    else:
        cache = get_cache()
        # 内存缓存需要遍历所有键
        keys_to_delete = [k for k in cache._cache.keys() if k.startswith(pattern)]
        for key in keys_to_delete:
            cache.delete(key)
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")


def optimize_query_pagination(
    query,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
):
    """
    优化分页查询

    Args:
        query: SQLAlchemy 查询对象
        page: 页码（从1开始）
        page_size: 每页大小
        max_page_size: 最大每页大小

    Returns:
        分页后的查询结果和元数据
    """
    # 限制每页大小
    page_size = min(page_size, max_page_size)

    # 计算偏移量
    offset = (page - 1) * page_size

    # 执行查询
    items = query.offset(offset).limit(page_size).all()

    # 获取总数（可以缓存）
    total = query.count()

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    }


def batch_query(
    session: Session,
    model,
    ids: List[int],
    batch_size: int = 100
) -> List[Any]:
    """
    批量查询优化

    Args:
        session: 数据库会话
        model: 模型类
        ids: ID 列表
        batch_size: 批次大小

    Returns:
        查询结果列表
    """
    results = []

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_results = session.query(model).filter(model.id.in_(batch_ids)).all()
        results.extend(batch_results)

    return results


def explain_query(session: Session, query_str: str) -> Dict[str, Any]:
    """
    分析查询执行计划

    Args:
        session: 数据库会话
        query_str: SQL 查询字符串

    Returns:
        执行计划信息
    """
    try:
        result = session.execute(text(f"EXPLAIN ANALYZE {query_str}"))
        plan = [row[0] for row in result]

        return {
            "query": query_str,
            "plan": plan
        }
    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        return {
            "query": query_str,
            "error": str(e)
        }


def get_table_stats(session: Session, table_name: str) -> Dict[str, Any]:
    """
    获取表统计信息

    Args:
        session: 数据库会话
        table_name: 表名

    Returns:
        表统计信息
    """
    try:
        # 获取表大小
        size_result = session.execute(text(f"""
            SELECT pg_size_pretty(pg_total_relation_size('{table_name}')) AS size
        """))
        size = size_result.fetchone()[0]

        # 获取行数
        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = count_result.fetchone()[0]

        # 获取索引信息
        index_result = session.execute(text(f"""
            SELECT
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE tablename = '{table_name}'
            ORDER BY pg_relation_size(indexrelid) DESC
        """))
        indexes = [{"name": row[0], "size": row[1]} for row in index_result]

        return {
            "table": table_name,
            "size": size,
            "row_count": count,
            "indexes": indexes
        }
    except Exception as e:
        logger.error(f"Error getting table stats for {table_name}: {e}")
        return {
            "table": table_name,
            "error": str(e)
        }


def monitor_slow_queries(threshold_ms: int = 100):
    """
    慢查询监控装饰器

    Args:
        threshold_ms: 慢查询阈值（毫秒）

    Usage:
        @monitor_slow_queries(threshold_ms=200)
        def my_query_function():
            return db.query(Model).all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000

            if elapsed > threshold_ms:
                logger.warning(
                    f"Slow query detected: {func.__name__} took {elapsed:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )

            return result

        return wrapper
    return decorator


def vacuum_analyze(session: Session, table_name: Optional[str] = None):
    """
    执行 VACUUM ANALYZE 优化表

    Args:
        session: 数据库会话
        table_name: 表名（可选，不指定则优化所有表）
    """
    try:
        if table_name:
            session.execute(text(f"VACUUM ANALYZE {table_name}"))
            logger.info(f"VACUUM ANALYZE completed for table: {table_name}")
        else:
            session.execute(text("VACUUM ANALYZE"))
            logger.info("VACUUM ANALYZE completed for all tables")
    except Exception as e:
        logger.error(f"Error during VACUUM ANALYZE: {e}")


def get_index_usage_stats(session: Session) -> List[Dict[str, Any]]:
    """
    获取索引使用统计

    Args:
        session: 数据库会话

    Returns:
        索引使用统计列表
    """
    try:
        result = session.execute(text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
            LIMIT 50;
        """))

        stats = []
        for row in result:
            stats.append({
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "scans": row[3],
                "tuples_read": row[4],
                "tuples_fetched": row[5]
            })

        return stats
    except Exception as e:
        logger.error(f"Error getting index usage stats: {e}")
        return []
