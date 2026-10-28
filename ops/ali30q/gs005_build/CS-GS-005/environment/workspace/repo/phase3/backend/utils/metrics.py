"""
Prometheus metrics collection for API monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Helper function to get or create metrics (avoid duplicates)
def get_or_create_metric(metric_class, name, description, labelnames=None, **kwargs):
    """Get existing metric or create new one."""
    try:
        # Try to get existing metric from registry
        existing = REGISTRY._names_to_collectors.get(name)
        if existing:
            return existing
    except Exception:
        pass

    # Create new metric
    try:
        if labelnames:
            return metric_class(name, description, labelnames, **kwargs)
        else:
            return metric_class(name, description, **kwargs)
    except ValueError as e:
        # Metric already exists, try to retrieve it
        if "Duplicated timeseries" in str(e) or "already registered" in str(e):
            return REGISTRY._names_to_collectors.get(name)
        raise

# API request metrics
http_requests_total = get_or_create_metric(
    Counter,
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = get_or_create_metric(
    Histogram,
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_in_progress = get_or_create_metric(
    Gauge,
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Cache metrics
cache_hits_total = get_or_create_metric(
    Counter,
    'cache_hits_total',
    'Total cache hits',
    ['cache_key']
)

cache_misses_total = get_or_create_metric(
    Counter,
    'cache_misses_total',
    'Total cache misses',
    ['cache_key']
)

cache_hit_rate = get_or_create_metric(
    Gauge,
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    ['cache_key']
)

# Database metrics
db_query_duration_seconds = get_or_create_metric(
    Histogram,
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

db_connections_active = get_or_create_metric(
    Gauge,
    'db_connections_active',
    'Number of active database connections'
)

# Redis metrics
redis_operations_total = get_or_create_metric(
    Counter,
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

redis_operation_duration_seconds = get_or_create_metric(
    Histogram,
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)


async def prometheus_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to collect Prometheus metrics for each request.
    """
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    endpoint = request.url.path

    # Track in-progress requests
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    # Track request duration
    start_time = time.time()

    try:
        response = await call_next(request)
        status = response.status_code

        # Record metrics
        duration = time.time() - start_time
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

        return response

    except Exception as e:
        # Record error
        http_requests_total.labels(method=method, endpoint=endpoint, status=500).inc()
        raise

    finally:
        # Decrement in-progress counter
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def record_cache_hit(cache_key: str):
    """Record a cache hit."""
    cache_hits_total.labels(cache_key=cache_key).inc()
    _update_cache_hit_rate(cache_key)


def record_cache_miss(cache_key: str):
    """Record a cache miss."""
    cache_misses_total.labels(cache_key=cache_key).inc()
    _update_cache_hit_rate(cache_key)


def _update_cache_hit_rate(cache_key: str):
    """Update cache hit rate gauge."""
    try:
        hits = cache_hits_total.labels(cache_key=cache_key)._value.get()
        misses = cache_misses_total.labels(cache_key=cache_key)._value.get()
        total = hits + misses

        if total > 0:
            hit_rate = hits / total
            cache_hit_rate.labels(cache_key=cache_key).set(hit_rate)
    except Exception as e:
        logger.error(f"Failed to update cache hit rate: {e}")


def record_db_query(query_type: str, duration: float):
    """Record database query metrics."""
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_redis_operation(operation: str, duration: float, status: str = "success"):
    """Record Redis operation metrics."""
    redis_operations_total.labels(operation=operation, status=status).inc()
    redis_operation_duration_seconds.labels(operation=operation).observe(duration)


async def metrics_endpoint() -> FastAPIResponse:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return FastAPIResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
