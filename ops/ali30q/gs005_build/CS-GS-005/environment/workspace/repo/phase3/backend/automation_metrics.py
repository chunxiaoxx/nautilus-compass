"""
Automation Monitoring Metrics

Tracks metrics for automated systems:
- Agent execution
- Task auto-assignment
- Blockchain events
- Nexus Protocol
"""
from utils.metrics_registry import get_or_create_counter, get_or_create_gauge, get_or_create_histogram
import logging

logger = logging.getLogger(__name__)

# Agent Execution Metrics
agent_tasks_executing = get_or_create_gauge(
    'agent_tasks_executing',
    'Number of tasks currently being executed by agents',
    ['agent_id']
)

agent_tasks_completed = get_or_create_counter(
    'agent_tasks_completed_total',
    'Total number of tasks completed by agents',
    ['agent_id', 'task_type']
)

agent_tasks_failed = get_or_create_counter(
    'agent_tasks_failed_total',
    'Total number of tasks failed by agents',
    ['agent_id', 'task_type', 'error_type']
)

agent_execution_duration = get_or_create_histogram(
    'agent_execution_duration_seconds',
    'Task execution duration in seconds',
    ['agent_id', 'task_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

# Task Auto-Assignment Metrics
tasks_auto_assigned = get_or_create_counter(
    'tasks_auto_assigned_total',
    'Total number of tasks automatically assigned',
    ['task_type']
)

tasks_assignment_failed = get_or_create_counter(
    'tasks_assignment_failed_total',
    'Total number of tasks that failed auto-assignment',
    ['reason']
)

agent_match_score = get_or_create_histogram(
    'agent_match_score',
    'Agent matching score distribution',
    ['task_type'],
    buckets=[0, 20, 40, 60, 80, 100]
)

# Blockchain Event Metrics
blockchain_events_received = get_or_create_counter(
    'blockchain_events_received_total',
    'Total number of blockchain events received',
    ['event_type']
)

blockchain_events_processed = get_or_create_counter(
    'blockchain_events_processed_total',
    'Total number of blockchain events successfully processed',
    ['event_type']
)

blockchain_events_failed = get_or_create_counter(
    'blockchain_events_failed_total',
    'Total number of blockchain events that failed processing',
    ['event_type', 'error_type']
)

blockchain_event_processing_duration = get_or_create_histogram(
    'blockchain_event_processing_duration_seconds',
    'Blockchain event processing duration',
    ['event_type'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Nexus Protocol Metrics
nexus_agents_online = get_or_create_gauge(
    'nexus_agents_online',
    'Number of agents currently online in Nexus Protocol'
)

nexus_messages_sent = get_or_create_counter(
    'nexus_messages_sent_total',
    'Total number of messages sent via Nexus Protocol',
    ['message_type']
)

nexus_messages_received = get_or_create_counter(
    'nexus_messages_received_total',
    'Total number of messages received via Nexus Protocol',
    ['message_type']
)

nexus_message_queue_size = get_or_create_gauge(
    'nexus_message_queue_size',
    'Current size of Nexus message queue'
)

nexus_messages_dropped = get_or_create_counter(
    'nexus_messages_dropped_total',
    'Total number of messages dropped due to queue overflow'
)

# System Health Metrics
automation_system_health = get_or_create_gauge(
    'automation_system_health',
    'Health status of automation systems (1=healthy, 0=unhealthy)',
    ['system']
)

# Helper functions to update metrics

def record_task_execution_start(agent_id: int):
    """Record task execution start."""
    agent_tasks_executing.labels(agent_id=agent_id).inc()


def record_task_execution_complete(agent_id: int, task_type: str, duration: float):
    """Record successful task execution."""
    agent_tasks_executing.labels(agent_id=agent_id).dec()
    agent_tasks_completed.labels(agent_id=agent_id, task_type=task_type).inc()
    agent_execution_duration.labels(agent_id=agent_id, task_type=task_type).observe(duration)


def record_task_execution_failed(agent_id: int, task_type: str, error_type: str):
    """Record failed task execution."""
    agent_tasks_executing.labels(agent_id=agent_id).dec()
    agent_tasks_failed.labels(agent_id=agent_id, task_type=task_type, error_type=error_type).inc()


def record_task_auto_assigned(task_type: str, match_score: float):
    """Record successful task auto-assignment."""
    tasks_auto_assigned.labels(task_type=task_type).inc()
    agent_match_score.labels(task_type=task_type).observe(match_score)


def record_task_assignment_failed(reason: str):
    """Record failed task auto-assignment."""
    tasks_assignment_failed.labels(reason=reason).inc()


def record_blockchain_event(event_type: str, success: bool, duration: float, error_type: str = None):
    """Record blockchain event processing."""
    blockchain_events_received.labels(event_type=event_type).inc()

    if success:
        blockchain_events_processed.labels(event_type=event_type).inc()
    else:
        blockchain_events_failed.labels(event_type=event_type, error_type=error_type or "unknown").inc()

    blockchain_event_processing_duration.labels(event_type=event_type).observe(duration)


def update_nexus_metrics(agents_online: int, queue_size: int):
    """Update Nexus Protocol metrics."""
    nexus_agents_online.set(agents_online)
    nexus_message_queue_size.set(queue_size)


def record_nexus_message(message_type: str, sent: bool):
    """Record Nexus message."""
    if sent:
        nexus_messages_sent.labels(message_type=message_type).inc()
    else:
        nexus_messages_received.labels(message_type=message_type).inc()


def record_nexus_message_dropped():
    """Record dropped Nexus message."""
    nexus_messages_dropped.inc()


def update_system_health(system: str, healthy: bool):
    """Update system health status."""
    automation_system_health.labels(system=system).set(1 if healthy else 0)


# Initialize system health metrics
def initialize_automation_metrics():
    """Initialize automation metrics."""
    logger.info("Initializing automation metrics...")

    # Set initial health status
    update_system_health("agent_executor", True)
    update_system_health("task_matcher", True)
    update_system_health("blockchain_listener", True)
    update_system_health("nexus_protocol", True)

    logger.info("✅ Automation metrics initialized")
