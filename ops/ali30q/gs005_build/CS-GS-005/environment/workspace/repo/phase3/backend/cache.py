import redis
from functools import wraps
import json
from typing import Any, Callable
import hashlib
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Redis连接池
redis_pool = redis.ConnectionPool(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD', None),
    max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', 50)),
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    缓存函数结果装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            key_parts = [key_prefix or func.__name__]

            # 添加参数到键
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            # 使用hash避免键过长
            key_str = ":".join(key_parts)
            if len(key_str) > 200:
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"{key_prefix or func.__name__}:{key_hash}"
            else:
                cache_key = key_str

            # 尝试从缓存获取
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    # 记录缓存命中
                    from monitoring.metrics import cache_hits
                    cache_hits.labels(function=func.__name__).inc()
                    return json.loads(cached)
                else:
                    # 记录缓存未命中
                    from monitoring.metrics import cache_misses
                    cache_misses.labels(function=func.__name__).inc()
            except Exception as e:
                # 缓存失败不影响业务
                from monitoring.metrics import cache_errors
                cache_errors.labels(operation='get').inc()
                logger.error(f"Cache get error: {e}")

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            try:
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
            except Exception as e:
                # 缓存失败不影响业务
                from monitoring.metrics import cache_errors
                cache_errors.labels(operation='set').inc()
                logger.error(f"Cache set error: {e}")

            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    清除匹配模式的缓存（使用SCAN非阻塞方式）

    Args:
        pattern: Redis键模式（如 "agent:*"）
    """
    try:
        cursor = 0
        keys_to_delete = []

        # 使用SCAN代替KEYS，避免阻塞Redis
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                keys_to_delete.extend(keys)
            if cursor == 0:
                break

        # 批量删除
        deleted_count = 0
        if keys_to_delete:
            for i in range(0, len(keys_to_delete), 100):
                batch = keys_to_delete[i:i+100]
                deleted_count += redis_client.delete(*batch)

        if deleted_count > 0:
            logger.info(f"Invalidated {deleted_count} keys matching '{pattern}'")

        return deleted_count
    except Exception as e:
        from monitoring.metrics import cache_errors
        cache_errors.labels(operation='invalidate').inc()
        logger.error(f"Cache invalidate error: {e}")
        return 0

def get_cache_stats():
    """
    获取缓存统计信息

    Returns:
        dict: 缓存统计数据
    """
    try:
        info = redis_client.info('stats')
        return {
            'total_connections': info.get('total_connections_received', 0),
            'total_commands': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': round(
                info.get('keyspace_hits', 0) /
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                2
            )
        }
    except Exception as e:
        logger.error(f"Get cache stats error: {e}")
        return {}

def health_check():
    """
    检查Redis连接健康状态

    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
