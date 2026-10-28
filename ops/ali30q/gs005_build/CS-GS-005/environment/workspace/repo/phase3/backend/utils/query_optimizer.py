"""
数据库查询优化工具
提供查询性能分析、慢查询检测、索引建议等功能
"""
import time
import logging
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query, Session
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """
    查询性能监控器

    功能:
    - 记录慢查询
    - 统计查询次数
    - 分析查询模式
    - 提供优化建议
    """

    def __init__(self, slow_query_threshold: float = 0.5):
        """
        初始化监控器

        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.slow_queries: List[Dict[str, Any]] = []

    def record_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """
        记录查询

        Args:
            query: SQL查询语句
            duration: 执行时间（秒）
            params: 查询参数
        """
        # 标准化查询（移除参数）
        normalized_query = self._normalize_query(query)

        # 更新统计
        if normalized_query not in self.query_stats:
            self.query_stats[normalized_query] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'avg_time': 0.0
            }

        stats = self.query_stats[normalized_query]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        stats['avg_time'] = stats['total_time'] / stats['count']

        # 记录慢查询
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                'query': query,
                'normalized_query': normalized_query,
                'duration': duration,
                'params': params,
                'timestamp': time.time()
            })

            logger.warning(
                f"Slow query detected ({duration:.3f}s): {query[:200]}..."
            )

    def _normalize_query(self, query: str) -> str:
        """
        标准化查询语句

        Args:
            query: 原始查询

        Returns:
            标准化后的查询
        """
        # 移除多余空格
        query = ' '.join(query.split())

        # 替换参数占位符
        import re
        query = re.sub(r'\?|\$\d+|:\w+', '?', query)
        query = re.sub(r"'[^']*'", "'?'", query)
        query = re.sub(r'\d+', '?', query)

        return query

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取慢查询列表

        Args:
            limit: 返回数量限制

        Returns:
            慢查询列表
        """
        # 按执行时间排序
        sorted_queries = sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_top_queries(self, limit: int = 10, sort_by: str = 'total_time') -> List[Dict[str, Any]]:
        """
        获取热点查询

        Args:
            limit: 返回数量限制
            sort_by: 排序字段 (total_time, count, avg_time)

        Returns:
            查询统计列表
        """
        queries = [
            {
                'query': query,
                **stats
            }
            for query, stats in self.query_stats.items()
        ]

        sorted_queries = sorted(
            queries,
            key=lambda x: x[sort_by],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        获取优化建议

        Returns:
            优化建议列表
        """
        suggestions = []

        # 分析慢查询
        for query_info in self.get_slow_queries(limit=5):
            query = query_info['normalized_query']
            duration = query_info['duration']

            suggestion = {
                'query': query,
                'issue': f'Slow query ({duration:.3f}s)',
                'suggestions': []
            }

            # 检查是否缺少索引
            if 'WHERE' in query.upper() and 'INDEX' not in query.upper():
                suggestion['suggestions'].append(
                    'Consider adding index on WHERE clause columns'
                )

            # 检查是否使用SELECT *
            if 'SELECT *' in query.upper():
                suggestion['suggestions'].append(
                    'Avoid SELECT *, specify only needed columns'
                )

            # 检查是否有JOIN
            if 'JOIN' in query.upper():
                suggestion['suggestions'].append(
                    'Ensure JOIN columns are indexed'
                )

            # 检查是否有ORDER BY
            if 'ORDER BY' in query.upper():
                suggestion['suggestions'].append(
                    'Consider adding index on ORDER BY columns'
                )

            if suggestion['suggestions']:
                suggestions.append(suggestion)

        # 分析高频查询
        for query_info in self.get_top_queries(limit=5, sort_by='count'):
            if query_info['count'] > 100:
                suggestions.append({
                    'query': query_info['query'],
                    'issue': f"High frequency query ({query_info['count']} times)",
                    'suggestions': [
                        'Consider caching this query result',
                        'Review if this query can be optimized or batched'
                    ]
                })

        return suggestions

    def reset_stats(self):
        """重置统计信息"""
        self.query_stats.clear()
        self.slow_queries.clear()

    def get_report(self) -> Dict[str, Any]:
        """
        生成性能报告

        Returns:
            性能报告
        """
        total_queries = sum(stats['count'] for stats in self.query_stats.values())
        total_time = sum(stats['total_time'] for stats in self.query_stats.values())
        avg_time = total_time / total_queries if total_queries > 0 else 0

        return {
            'summary': {
                'total_queries': total_queries,
                'unique_queries': len(self.query_stats),
                'total_time': f'{total_time:.3f}s',
                'avg_time': f'{avg_time*1000:.2f}ms',
                'slow_queries_count': len(self.slow_queries)
            },
            'top_queries_by_time': self.get_top_queries(limit=5, sort_by='total_time'),
            'top_queries_by_count': self.get_top_queries(limit=5, sort_by='count'),
            'slowest_queries': self.get_slow_queries(limit=5),
            'optimization_suggestions': self.get_optimization_suggestions()
        }


# 全局监控器实例
_query_monitor: Optional[QueryPerformanceMonitor] = None


def get_query_monitor() -> Optional[QueryPerformanceMonitor]:
    """获取全局查询监控器"""
    return _query_monitor


def init_query_monitor(engine: Engine, slow_query_threshold: float = 0.5):
    """
    初始化查询监控

    Args:
        engine: SQLAlchemy引擎
        slow_query_threshold: 慢查询阈值（秒）
    """
    global _query_monitor
    _query_monitor = QueryPerformanceMonitor(slow_query_threshold)

    # 注册事件监听器
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_time = time.time() - conn.info['query_start_time'].pop()
        _query_monitor.record_query(statement, total_time, parameters)

    logger.info(f"Query performance monitoring initialized (threshold: {slow_query_threshold}s)")


@contextmanager
def query_timer(description: str = "Query"):
    """
    查询计时上下文管理器

    Args:
        description: 查询描述

    Usage:
        with query_timer("Get user tasks"):
            tasks = db.query(Task).filter(Task.user_id == user_id).all()
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        if elapsed > 0.5:
            logger.warning(f"{description} took {elapsed:.3f}s")
        else:
            logger.debug(f"{description} took {elapsed:.3f}s")


def optimized_query(func: Callable):
    """
    查询优化装饰器

    自动添加查询监控和性能日志

    Usage:
        @optimized_query
        def get_tasks(db: Session, status: str):
            return db.query(Task).filter(Task.status == status).all()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            if elapsed > 0.5:
                logger.warning(
                    f"Slow query in {func.__name__}: {elapsed:.3f}s"
                )

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Query error in {func.__name__} after {elapsed:.3f}s: {e}"
            )
            raise

    return wrapper


class QueryOptimizer:
    """
    查询优化器

    提供查询优化建议和自动优化功能
    """

    @staticmethod
    def add_eager_loading(query: Query, *relationships) -> Query:
        """
        添加预加载关系

        Args:
            query: SQLAlchemy查询
            relationships: 要预加载的关系

        Returns:
            优化后的查询
        """
        from sqlalchemy.orm import joinedload

        for rel in relationships:
            query = query.options(joinedload(rel))

        return query

    @staticmethod
    def add_pagination(query: Query, page: int = 1, per_page: int = 50) -> Query:
        """
        添加分页

        Args:
            query: SQLAlchemy查询
            page: 页码（从1开始）
            per_page: 每页数量

        Returns:
            分页后的查询
        """
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page)

    @staticmethod
    def optimize_count_query(query: Query) -> int:
        """
        优化计数查询

        Args:
            query: SQLAlchemy查询

        Returns:
            记录数量
        """
        from sqlalchemy import func

        # 使用子查询优化COUNT
        count_query = query.statement.with_only_columns([func.count()]).order_by(None)
        return query.session.execute(count_query).scalar()

    @staticmethod
    def batch_load(session: Session, model, ids: List[int], batch_size: int = 100):
        """
        批量加载记录

        Args:
            session: 数据库会话
            model: 模型类
            ids: ID列表
            batch_size: 批次大小

        Returns:
            记录列表
        """
        results = []

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_results = session.query(model).filter(
                model.id.in_(batch_ids)
            ).all()
            results.extend(batch_results)

        return results


def analyze_query_plan(session: Session, query: Query) -> Dict[str, Any]:
    """
    分析查询执行计划

    Args:
        session: 数据库会话
        query: SQLAlchemy查询

    Returns:
        执行计划分析结果
    """
    # 获取SQL语句
    sql = str(query.statement.compile(
        compile_kwargs={"literal_binds": True}
    ))

    # 执行EXPLAIN
    try:
        # PostgreSQL
        explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE) {sql}"
        result = session.execute(text(explain_query))
        plan = result.fetchone()[0]

        return {
            'sql': sql,
            'plan': plan,
            'database': 'postgresql'
        }
    except Exception as e:
        try:
            # SQLite
            explain_query = f"EXPLAIN QUERY PLAN {sql}"
            result = session.execute(text(explain_query))
            plan = [dict(row) for row in result]

            return {
                'sql': sql,
                'plan': plan,
                'database': 'sqlite'
            }
        except Exception as e2:
            logger.error(f"Failed to analyze query plan: {e2}")
            return {
                'sql': sql,
                'error': str(e2)
            }


def suggest_indexes(session: Session, model) -> List[Dict[str, Any]]:
    """
    建议索引

    Args:
        session: 数据库会话
        model: 模型类

    Returns:
        索引建议列表
    """
    suggestions = []

    # 获取表名
    table_name = model.__tablename__

    # 检查现有索引
    try:
        # PostgreSQL
        query = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = :table_name
        """)
        result = session.execute(query, {'table_name': table_name})
        existing_indexes = {row[0]: row[1] for row in result}
    except Exception:
        try:
            # SQLite
            query = text(f"PRAGMA index_list({table_name})")
            result = session.execute(query)
            existing_indexes = {row[1]: None for row in result}
        except Exception as e:
            logger.error(f"Failed to get existing indexes: {e}")
            existing_indexes = {}

    # 分析模型列
    for column in model.__table__.columns:
        column_name = column.name

        # 检查是否已有索引
        has_index = any(column_name in idx for idx in existing_indexes.keys())

        if not has_index:
            # 建议为外键添加索引
            if column.foreign_keys:
                suggestions.append({
                    'table': table_name,
                    'column': column_name,
                    'reason': 'Foreign key without index',
                    'sql': f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name})"
                })

            # 建议为常用过滤列添加索引
            if column_name in ['status', 'type', 'created_at', 'updated_at']:
                suggestions.append({
                    'table': table_name,
                    'column': column_name,
                    'reason': 'Commonly filtered column',
                    'sql': f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name})"
                })

    return suggestions


# 导出工具函数
__all__ = [
    'QueryPerformanceMonitor',
    'get_query_monitor',
    'init_query_monitor',
    'query_timer',
    'optimized_query',
    'QueryOptimizer',
    'analyze_query_plan',
    'suggest_indexes'
]
