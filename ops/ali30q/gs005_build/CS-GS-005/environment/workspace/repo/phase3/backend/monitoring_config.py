"""
监控配置模块
提供Prometheus指标配置、自定义指标、区块链交易监控和Gas费用监控
"""
from prometheus_client import generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry
from typing import Optional, Dict, Any
import time
import logging
from functools import wraps
from utils.metrics_registry import get_metrics, init_metrics

logger = logging.getLogger(__name__)

# 初始化指标
init_metrics()
metrics = get_metrics()

# 获取已注册的指标
app_info = metrics.get('nautilus_app')
http_requests_total = metrics.get('nautilus_http_requests_total')
http_request_duration_seconds = metrics.get('nautilus_http_request_duration_seconds')
websocket_connections = metrics.get('nautilus_websocket_connections')
websocket_messages_total = metrics.get('nautilus_websocket_messages_total')
tasks_total = metrics.get('nautilus_tasks_total')
tasks_active = metrics.get('nautilus_tasks_active')
task_processing_duration_seconds = metrics.get('nautilus_task_processing_duration_seconds')
task_queue_size = metrics.get('nautilus_task_queue_size')
agents_total = metrics.get('nautilus_agents_total')
agents_active = metrics.get('nautilus_agents_active')
agent_tasks_completed = metrics.get('nautilus_agent_tasks_completed')
agent_reputation = metrics.get('nautilus_agent_reputation')
database_connections = metrics.get('nautilus_database_connections')
database_query_duration_seconds = metrics.get('nautilus_database_query_duration_seconds')
database_errors_total = metrics.get('nautilus_database_errors_total')
blockchain_transactions_total = metrics.get('nautilus_blockchain_transactions_total')
blockchain_transaction_duration_seconds = metrics.get('nautilus_blockchain_transaction_duration_seconds')
blockchain_gas_used = metrics.get('nautilus_blockchain_gas_used')
blockchain_gas_price_gwei = metrics.get('nautilus_blockchain_gas_price_gwei')
blockchain_errors_total = metrics.get('nautilus_blockchain_errors_total')
cache_operations_total = metrics.get('nautilus_cache_operations_total')
cache_hits = metrics.get('nautilus_cache_hits')
cache_misses = metrics.get('nautilus_cache_misses')
cache_errors = metrics.get('nautilus_cache_errors')
api_key_usage_total = metrics.get('nautilus_api_key_usage_total')
security_events_total = metrics.get('nautilus_security_events_total')


def get_prometheus_metrics():
    """
    获取Prometheus指标数据

    Returns:
        bytes: Prometheus格式的指标数据
    """
    return generate_latest(REGISTRY)


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    记录HTTP请求指标

    Args:
        method: HTTP方法
        endpoint: 端点路径
        status_code: 状态码
        duration: 请求耗时（秒）
    """
    try:
        if http_requests_total:
            http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
        if http_request_duration_seconds:
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    except Exception as e:
        logger.error(f"Failed to record HTTP request metrics: {e}")


def record_websocket_connection(action: str):
    """
    记录WebSocket连接指标

    Args:
        action: 'connect' or 'disconnect'
    """
    try:
        if websocket_connections:
            if action == 'connect':
                websocket_connections.inc()
            elif action == 'disconnect':
                websocket_connections.dec()
    except Exception as e:
        logger.error(f"Failed to record WebSocket connection: {e}")


def record_websocket_message(direction: str, message_type: str):
    """
    记录WebSocket消息指标

    Args:
        direction: 'sent' or 'received'
        message_type: 消息类型
    """
    try:
        if websocket_messages_total:
            websocket_messages_total.labels(direction=direction, type=message_type).inc()
    except Exception as e:
        logger.error(f"Failed to record WebSocket message: {e}")


def record_task_operation(status: str):
    """
    记录任务操作指标

    Args:
        status: 任务状态
    """
    try:
        if tasks_total:
            tasks_total.labels(status=status).inc()
    except Exception as e:
        logger.error(f"Failed to record task operation: {e}")


def record_task_processing(task_type: str, duration: float):
    """
    记录任务处理时间

    Args:
        task_type: 任务类型
        duration: 处理时间（秒）
    """
    try:
        if task_processing_duration_seconds:
            task_processing_duration_seconds.labels(task_type=task_type).observe(duration)
    except Exception as e:
        logger.error(f"Failed to record task processing: {e}")


def record_agent_operation(status: str):
    """
    记录Agent操作指标

    Args:
        status: Agent状态
    """
    try:
        if agents_total:
            agents_total.labels(status=status).inc()
    except Exception as e:
        logger.error(f"Failed to record agent operation: {e}")


def record_database_query(operation: str, duration: float):
    """
    记录数据库查询指标

    Args:
        operation: 操作类型
        duration: 查询耗时（秒）
    """
    try:
        if database_query_duration_seconds:
            database_query_duration_seconds.labels(operation=operation).observe(duration)
    except Exception as e:
        logger.error(f"Failed to record database query: {e}")


def record_database_error(error_type: str):
    """
    记录数据库错误

    Args:
        error_type: 错误类型
    """
    try:
        if database_errors_total:
            database_errors_total.labels(error_type=error_type).inc()
    except Exception as e:
        logger.error(f"Failed to record database error: {e}")


def record_blockchain_transaction(operation: str, status: str, duration: float = None, gas_used: int = None):
    """
    记录区块链交易指标

    Args:
        operation: 操作类型
        status: 交易状态
        duration: 交易耗时（秒）
        gas_used: Gas消耗量
    """
    try:
        if blockchain_transactions_total:
            blockchain_transactions_total.labels(operation=operation, status=status).inc()
        if duration and blockchain_transaction_duration_seconds:
            blockchain_transaction_duration_seconds.labels(operation=operation).observe(duration)
        if gas_used and blockchain_gas_used:
            blockchain_gas_used.labels(operation=operation).observe(gas_used)
    except Exception as e:
        logger.error(f"Failed to record blockchain transaction: {e}")


def record_blockchain_error(operation: str, error_type: str):
    """
    记录区块链错误

    Args:
        operation: 操作类型
        error_type: 错误类型
    """
    try:
        if blockchain_errors_total:
            blockchain_errors_total.labels(operation=operation, error_type=error_type).inc()
    except Exception as e:
        logger.error(f"Failed to record blockchain error: {e}")


def record_cache_operation(operation: str, status: str):
    """
    记录缓存操作指标

    Args:
        operation: 操作类型
        status: 操作状态
    """
    try:
        if cache_operations_total:
            cache_operations_total.labels(operation=operation, status=status).inc()
        if status == 'hit' and cache_hits:
            cache_hits.labels(operation=operation).inc()
        elif status == 'miss' and cache_misses:
            cache_misses.labels(operation=operation).inc()
        elif status == 'error' and cache_errors:
            cache_errors.labels(operation=operation).inc()
    except Exception as e:
        logger.error(f"Failed to record cache operation: {e}")


def record_api_key_usage(key_id: str, endpoint: str):
    """
    记录API密钥使用

    Args:
        key_id: API密钥ID
        endpoint: 端点路径
    """
    try:
        if api_key_usage_total:
            api_key_usage_total.labels(key_id=key_id, endpoint=endpoint).inc()
    except Exception as e:
        logger.error(f"Failed to record API key usage: {e}")


def record_security_event(event_type: str, severity: str):
    """
    记录安全事件

    Args:
        event_type: 事件类型
        severity: 严重程度
    """
    try:
        if security_events_total:
            security_events_total.labels(event_type=event_type, severity=severity).inc()
    except Exception as e:
        logger.error(f"Failed to record security event: {e}")


def record_login_attempt(username: str, success: bool):
    """
    记录登录尝试

    Args:
        username: 用户名
        success: 是否成功
    """
    try:
        status = 'success' if success else 'failed'
        if security_events_total:
            security_events_total.labels(event_type='login_attempt', severity='info').inc()
    except Exception as e:
        logger.error(f"Failed to record login attempt: {e}")


def initialize_app_info(version: str = "3.0.0", environment: str = "production"):
    """
    初始化应用信息指标

    Args:
        version: 应用版本
        environment: 运行环境
    """
    try:
        if app_info:
            app_info.labels(version=version, environment=environment).set(1)
    except Exception as e:
        logger.error(f"Failed to initialize app info: {e}")


async def check_database_health() -> dict:
    """检查数据库健康状态，返回结构化状态。"""
    import time
    try:
        from sqlalchemy import text, create_engine
        import os
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            return {"status": "unhealthy", "error": "DATABASE_URL not set"}
        # Use sync engine for health check (avoid async compatibility issues)
        sync_engine = create_engine(db_url)
        start = time.time()
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        elapsed = round(time.time() - start, 3)
        sync_engine.dispose()
        return {"status": "healthy", "response_time": elapsed}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_blockchain_health() -> dict:
    """检查区块链连接健康状态，返回结构化状态。"""
    import asyncio
    try:
        import os
        from web3 import Web3
        rpc_url = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")

        def _check():
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
            if w3.is_connected():
                return {"status": "healthy", "connected": True, "chain_id": w3.eth.chain_id}
            return {"status": "unhealthy", "connected": False, "rpc": rpc_url[:50]}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _check)
    except Exception as e:
        logger.error(f"Blockchain health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_redis_health() -> dict:
    """检查Redis连接健康状态，返回结构化状态。"""
    try:
        from utils.cache import get_cache
        cache = get_cache()
        if cache and hasattr(cache, 'ping'):
            await cache.ping()
            return {"status": "healthy", "connected": True}
        return {"status": "healthy", "connected": False, "note": "cache not configured"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def get_metrics() -> Dict[str, Any]:
    """
    获取所有指标对象

    Returns:
        Dict[str, Any]: 指标字典
    """
    return metrics


def monitor_execution_time(metric_name: str = None):
    """
    装饰器：监控函数执行时间

    Args:
        metric_name: 指标名称（可选）
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise

        # 判断是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 导出所有记录函数
__all__ = [
    'get_prometheus_metrics',
    'get_metrics',
    'record_http_request',
    'record_websocket_connection',
    'record_websocket_message',
    'record_task_operation',
    'record_task_processing',
    'record_agent_operation',
    'record_database_query',
    'record_database_error',
    'record_blockchain_transaction',
    'record_blockchain_error',
    'record_cache_operation',
    'record_api_key_usage',
    'record_security_event',
    'record_login_attempt',
    'initialize_app_info',
    'check_database_health',
    'check_blockchain_health',
    'check_redis_health',
    'monitor_execution_time',
]
