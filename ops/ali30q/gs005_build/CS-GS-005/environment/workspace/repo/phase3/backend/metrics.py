"""
Prometheus metrics endpoint for Nautilus API.
"""
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

task_operations_total = Counter(
    'task_operations_total',
    'Total task operations',
    ['operation', 'status']
)

agent_operations_total = Counter(
    'agent_operations_total',
    'Total agent operations',
    ['operation', 'status']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)


@router.get("")
async def metrics():
    """
    Expose Prometheus metrics endpoint.

    Returns:
        Response: Prometheus metrics in text format
    """
    logger.debug("Metrics endpoint accessed")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def increment_request_counter(method: str, endpoint: str, status: int):
    """Increment HTTP request counter."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()


def observe_request_duration(method: str, endpoint: str, duration: float):
    """Observe HTTP request duration."""
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def set_active_connections(count: int):
    """Set active connections gauge."""
    active_connections.set(count)


def increment_task_operation(operation: str, status: str):
    """Increment task operation counter."""
    task_operations_total.labels(operation=operation, status=status).inc()


def increment_agent_operation(operation: str, status: str):
    """Increment agent operation counter."""
    agent_operations_total.labels(operation=operation, status=status).inc()


def observe_database_query(query_type: str, duration: float):
    """Observe database query duration."""
    database_query_duration_seconds.labels(query_type=query_type).observe(duration)


def increment_cache_operation(operation: str, status: str):
    """Increment cache operation counter."""
    cache_operations_total.labels(operation=operation, status=status).inc()
