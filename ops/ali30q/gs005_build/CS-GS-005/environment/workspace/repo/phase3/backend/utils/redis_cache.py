"""
Redis缓存实现 - 高性能分布式缓存
支持多层缓存、缓存预热、智能失效等高级特性
"""
import redis
import json
import time
import logging
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import hashlib
import pickle
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis缓存管理器

    特性:
    - 支持多种数据类型 (string, hash, list, set)
    - 自动序列化/反序列化
    - TTL管理
    - 缓存统计
    - 连接池管理
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """
        初始化Redis缓存

        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: 密码
            max_connections: 最大连接数
            decode_responses: 是否解码响应
        """
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        self.client = redis.Redis(connection_pool=self.pool)

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0

        logger.info(f"Redis cache initialized: {host}:{port}/{db}")

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        try:
            value = self.client.get(key)
            if value is not None:
                self._hits += 1
                # 尝试JSON反序列化
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                self._misses += 1
                return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._misses += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置

        Returns:
            是否设置成功
        """
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, default=str)
            elif not isinstance(value, (str, bytes, int, float)):
                value = pickle.dumps(value)

            result = self.client.set(key, value, ex=ttl, nx=nx, xx=xx)
            if result:
                self._sets += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, *keys: str) -> int:
        """
        删除缓存键

        Args:
            keys: 要删除的键

        Returns:
            删除的键数量
        """
        try:
            count = self.client.delete(*keys)
            self._deletes += count
            return count
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        检查键是否存在

        Args:
            keys: 要检查的键

        Returns:
            存在的键数量
        """
        try:
            return self.client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 缓存键
            seconds: 过期秒数

        Returns:
            是否设置成功
        """
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，-1表示永久，-2表示不存在
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error for key {key}: {e}")
            return -2

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增计数器

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            递增后的值
        """
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递减计数器

        Args:
            key: 缓存键
            amount: 递减量

        Returns:
            递减后的值
        """
        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis decr error for key {key}: {e}")
            return None

    def hget(self, name: str, key: str) -> Optional[Any]:
        """
        获取哈希表字段值

        Args:
            name: 哈希表名
            key: 字段名

        Returns:
            字段值
        """
        try:
            value = self.client.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis hget error for {name}.{key}: {e}")
            return None

    def hset(self, name: str, key: str, value: Any) -> bool:
        """
        设置哈希表字段值

        Args:
            name: 哈希表名
            key: 字段名
            value: 字段值

        Returns:
            是否设置成功
        """
        try:
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, default=str)
            return bool(self.client.hset(name, key, value))
        except Exception as e:
            logger.error(f"Redis hset error for {name}.{key}: {e}")
            return False

    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        获取哈希表所有字段

        Args:
            name: 哈希表名

        Returns:
            字段字典
        """
        try:
            data = self.client.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis hgetall error for {name}: {e}")
            return {}

    def lpush(self, key: str, *values: Any) -> Optional[int]:
        """
        从列表左侧推入元素

        Args:
            key: 列表键
            values: 要推入的值

        Returns:
            列表长度
        """
        try:
            serialized = [
                json.dumps(v, default=str) if isinstance(v, (dict, list, tuple)) else v
                for v in values
            ]
            return self.client.lpush(key, *serialized)
        except Exception as e:
            logger.error(f"Redis lpush error for key {key}: {e}")
            return None

    def rpush(self, key: str, *values: Any) -> Optional[int]:
        """
        从列表右侧推入元素

        Args:
            key: 列表键
            values: 要推入的值

        Returns:
            列表长度
        """
        try:
            serialized = [
                json.dumps(v, default=str) if isinstance(v, (dict, list, tuple)) else v
                for v in values
            ]
            return self.client.rpush(key, *serialized)
        except Exception as e:
            logger.error(f"Redis rpush error for key {key}: {e}")
            return None

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        获取列表范围元素

        Args:
            key: 列表键
            start: 起始索引
            end: 结束索引

        Returns:
            元素列表
        """
        try:
            values = self.client.lrange(key, start, end)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            return result
        except Exception as e:
            logger.error(f"Redis lrange error for key {key}: {e}")
            return []

    def sadd(self, key: str, *members: Any) -> Optional[int]:
        """
        向集合添加成员

        Args:
            key: 集合键
            members: 要添加的成员

        Returns:
            添加的成员数量
        """
        try:
            serialized = [
                json.dumps(m, default=str) if isinstance(m, (dict, list, tuple)) else m
                for m in members
            ]
            return self.client.sadd(key, *serialized)
        except Exception as e:
            logger.error(f"Redis sadd error for key {key}: {e}")
            return None

    def smembers(self, key: str) -> set:
        """
        获取集合所有成员

        Args:
            key: 集合键

        Returns:
            成员集合
        """
        try:
            members = self.client.smembers(key)
            result = set()
            for member in members:
                try:
                    result.add(json.loads(member))
                except (json.JSONDecodeError, TypeError):
                    result.add(member)
            return result
        except Exception as e:
            logger.error(f"Redis smembers error for key {key}: {e}")
            return set()

    def keys(self, pattern: str = '*') -> List[str]:
        """
        查找匹配模式的键

        Args:
            pattern: 匹配模式

        Returns:
            键列表
        """
        try:
            return [key.decode() if isinstance(key, bytes) else key
                    for key in self.client.keys(pattern)]
        except Exception as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []

    def flushdb(self) -> bool:
        """
        清空当前数据库

        Returns:
            是否成功
        """
        try:
            return bool(self.client.flushdb())
        except Exception as e:
            logger.error(f"Redis flushdb error: {e}")
            return False

    def ping(self) -> bool:
        """
        检查连接是否正常

        Returns:
            是否连接正常
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        try:
            info = self.client.info()
            return {
                "hits": self._hits,
                "misses": self._misses,
                "sets": self._sets,
                "deletes": self._deletes,
                "hit_rate": f"{hit_rate:.2f}%",
                "total_keys": self.client.dbsize(),
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_days": info.get('uptime_in_days', 0)
            }
        except Exception as e:
            logger.error(f"Redis get_stats error: {e}")
            return {
                "hits": self._hits,
                "misses": self._misses,
                "sets": self._sets,
                "deletes": self._deletes,
                "hit_rate": f"{hit_rate:.2f}%",
                "error": str(e)
            }

    def reset_stats(self):
        """重置统计信息"""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0


# 全局Redis缓存实例
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> Optional[RedisCache]:
    """获取全局Redis缓存实例"""
    return _redis_cache


def init_redis_cache(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    max_connections: int = 50
) -> RedisCache:
    """
    初始化全局Redis缓存

    Args:
        host: Redis服务器地址
        port: Redis端口
        db: 数据库编号
        password: 密码
        max_connections: 最大连接数

    Returns:
        Redis缓存实例
    """
    global _redis_cache
    _redis_cache = RedisCache(
        host=host,
        port=port,
        db=db,
        password=password,
        max_connections=max_connections
    )
    return _redis_cache


def redis_cached(ttl: int = 300, key_prefix: str = ""):
    """
    Redis缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀

    Usage:
        @redis_cached(ttl=60, key_prefix="agent")
        def get_agent(agent_id: int):
            return db.query(Agent).filter(Agent.id == agent_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_redis_cache()
            if cache is None:
                # Redis不可用，直接调用函数
                return await func(*args, **kwargs)

            # 生成缓存键
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Redis cache hit: {cache_key}")
                return cached_value

            # 调用函数并缓存结果
            logger.debug(f"Redis cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_redis_cache()
            if cache is None:
                return func(*args, **kwargs)

            # 生成缓存键
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Redis cache hit: {cache_key}")
                return cached_value

            # 调用函数并缓存结果
            logger.debug(f"Redis cache miss: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        # 返回适当的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def invalidate_redis_cache(key_prefix: str):
    """
    使Redis缓存失效

    Args:
        key_prefix: 缓存键前缀，删除所有匹配的键
    """
    cache = get_redis_cache()
    if cache is None:
        return

    pattern = f"{key_prefix}:*"
    keys = cache.keys(pattern)
    if keys:
        cache.delete(*keys)
        logger.info(f"Invalidated {len(keys)} Redis cache entries with prefix '{key_prefix}'")
