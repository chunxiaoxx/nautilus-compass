from utils.metrics_registry import get_or_create_counter, get_or_create_gauge, get_or_create_histogram

# 缓存指标
cache_hits = get_or_create_counter('cache_hits_total', 'Cache hits', ['function'])
cache_misses = get_or_create_counter('cache_misses_total', 'Cache misses', ['function'])
cache_errors = get_or_create_counter('cache_errors_total', 'Cache errors', ['operation'])

# 性能指标
request_duration = get_or_create_histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# 业务指标
signature_verifications = get_or_create_counter(
    'signature_verifications_total',
    'Total signature verifications',
    ['status']
)

agent_queries = get_or_create_counter(
    'agent_queries_total',
    'Total agent queries',
    ['cached']
)

task_queries = get_or_create_counter(
    'task_queries_total',
    'Total task queries',
    ['cached']
)

# 系统指标
active_connections = get_or_create_gauge(
    'active_connections',
    'Number of active connections'
)

redis_connection_pool_size = get_or_create_gauge(
    'redis_connection_pool_size',
    'Redis connection pool size'
)
