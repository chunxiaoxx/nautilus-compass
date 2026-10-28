"""
统一的Prometheus指标注册模块
解决重复注册问题
"""
from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY
from prometheus_client.core import CollectorRegistry
import logging

logger = logging.getLogger(__name__)

# 使用全局标志防止重复注册
_metrics_registered = False
_metrics = {}


def _find_existing_collector(name):
    """Find an existing collector by name in the registry."""
    try:
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
    except Exception:
        pass
    return None


def get_or_create_counter(name, description, labelnames=None):
    """获取或创建Counter指标"""
    global _metrics
    if name not in _metrics:
        try:
            _metrics[name] = Counter(name, description, labelnames or [])
        except ValueError:
            existing = _find_existing_collector(name)
            if existing:
                _metrics[name] = existing
            else:
                logger.warning(f"Metric {name}: could not create or find, using no-op")
                _metrics[name] = Counter(f"_noop_{name}", description, labelnames or [])
    return _metrics[name]


def get_or_create_histogram(name, description, labelnames=None, buckets=None):
    """获取或创建Histogram指标"""
    global _metrics
    if name not in _metrics:
        try:
            kwargs = {'name': name, 'documentation': description}
            if labelnames:
                kwargs['labelnames'] = labelnames
            if buckets:
                kwargs['buckets'] = buckets
            _metrics[name] = Histogram(**kwargs)
        except ValueError:
            existing = _find_existing_collector(name)
            if existing:
                _metrics[name] = existing
            else:
                _metrics[name] = Histogram(f"_noop_{name}", description, labelnames or [])
    return _metrics[name]


def get_or_create_gauge(name, description, labelnames=None):
    """获取或创建Gauge指标"""
    global _metrics
    if name not in _metrics:
        try:
            _metrics[name] = Gauge(name, description, labelnames or [])
        except ValueError:
            existing = _find_existing_collector(name)
            if existing:
                _metrics[name] = existing
            else:
                _metrics[name] = Gauge(f"_noop_{name}", description, labelnames or [])
    return _metrics[name]


def get_or_create_info(name, description, labelnames=None):
    """获取或创建Info指标"""
    global _metrics
    if name not in _metrics:
        try:
            # Info指标不需要labelnames，但如果提供了就忽略
            _metrics[name] = Info(name, description)
        except ValueError as e:
            logger.warning(f"Metric {name} already exists, retrieving from registry")
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name') and collector._name == name:
                    _metrics[name] = collector
                    break
        except Exception as e:
            logger.error(f"Failed to create Info metric {name}: {e}")
            # 创建一个空的占位符
            _metrics[name] = None
    return _metrics[name]


# 预定义的应用指标
def init_metrics():
    """初始化所有指标（只调用一次）"""
    global _metrics_registered

    if _metrics_registered:
        logger.info("Metrics already registered, skipping")
        return _metrics

    logger.info("Initializing Prometheus metrics")

    # 应用信息
    get_or_create_info('nautilus_app', 'Nautilus Phase 3 Backend Application Info')

    # HTTP请求指标
    get_or_create_counter(
        'nautilus_http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )

    get_or_create_histogram(
        'nautilus_http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
    )

    # WebSocket连接指标
    get_or_create_gauge(
        'nautilus_websocket_connections',
        'Current number of WebSocket connections'
    )

    get_or_create_counter(
        'nautilus_websocket_messages_total',
        'Total WebSocket messages',
        ['event_type', 'direction']
    )

    # 任务相关指标
    get_or_create_counter(
        'nautilus_tasks_total',
        'Total number of tasks',
        ['status']
    )

    get_or_create_gauge(
        'nautilus_tasks_active',
        'Number of active tasks'
    )

    # Agent相关指标
    get_or_create_counter(
        'nautilus_agents_total',
        'Total number of agents',
        ['status']
    )

    get_or_create_gauge(
        'nautilus_agents_active',
        'Number of active agents'
    )

    # 数据库指标
    get_or_create_histogram(
        'nautilus_database_query_duration_seconds',
        'Database query duration in seconds',
        ['query_type'],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
    )

    get_or_create_counter(
        'nautilus_database_errors_total',
        'Total database errors',
        ['error_type']
    )

    _metrics_registered = True
    logger.info("Metrics initialization completed")

    return _metrics


def get_metrics():
    """获取所有已注册的指标"""
    if not _metrics_registered:
        init_metrics()
    return _metrics


def reset_metrics():
    """重置指标（仅用于测试）"""
    global _metrics_registered, _metrics
    _metrics_registered = False
    _metrics = {}
    logger.info("Metrics reset")
