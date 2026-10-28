"""
Utility script to check database query performance and explain query plans.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from utils.database import engine
from logging_config import get_logger

logger = get_logger(__name__)


def explain_query(query: str, params: dict = None):
    """
    Explain a SQL query to see execution plan.

    WARNING: This function uses raw SQL with text(). It should only be used
    for administrative/debugging purposes with predefined queries.
    Never pass user input directly to this function.
    """
    with engine.connect() as conn:
        try:
            # For SQLite - using predefined query structure
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            result = conn.execute(text(explain_query), params or {})

            print(f"\nQuery: {query}")
            if params:
                print(f"Params: {params}")
            print("\nExecution Plan:")
            print("-" * 60)

            for row in result:
                print(row)

            print("-" * 60)

        except Exception as e:
            logger.error(f"Failed to explain query: {e}")


def check_common_queries():
    """Check execution plans for common queries."""

    print("="*80)
    print("DATABASE QUERY PERFORMANCE ANALYSIS")
    print("="*80)

    queries = [
        # List tasks with status filter
        (
            "SELECT * FROM tasks WHERE status = :status ORDER BY created_at DESC LIMIT 50",
            {"status": "Open"},
            "List tasks with status filter"
        ),

        # List tasks with type filter
        (
            "SELECT * FROM tasks WHERE task_type = :task_type ORDER BY created_at DESC LIMIT 50",
            {"task_type": "CODE"},
            "List tasks with type filter"
        ),

        # Get agent tasks
        (
            "SELECT * FROM tasks WHERE agent = :agent ORDER BY created_at DESC LIMIT 50",
            {"agent": "0x1234567890123456789012345678901234567890"},
            "Get agent tasks"
        ),

        # Get reward balance (aggregation)
        (
            "SELECT SUM(amount) FROM rewards WHERE agent = :agent AND status = :status",
            {"agent": "0x1234567890123456789012345678901234567890", "status": "Distributed"},
            "Get reward balance"
        ),

        # Get reward history
        (
            "SELECT * FROM rewards WHERE agent = :agent ORDER BY distributed_at DESC LIMIT 50",
            {"agent": "0x1234567890123456789012345678901234567890"},
            "Get reward history"
        ),

        # List agents by reputation
        (
            "SELECT * FROM agents ORDER BY reputation DESC LIMIT 50",
            None,
            "List agents by reputation"
        ),

        # API key lookup
        (
            "SELECT * FROM api_keys WHERE key = :key AND is_active = :is_active",
            {"key": "test_key", "is_active": True},
            "API key authentication"
        ),
    ]

    for query, params, description in queries:
        print(f"\n{'='*80}")
        print(f"Query: {description}")
        print('='*80)
        explain_query(query, params)


def check_indexes():
    """Check what indexes exist on tables."""

    print("\n" + "="*80)
    print("EXISTING INDEXES")
    print("="*80)

    with engine.connect() as conn:
        try:
            # SQLite query
            result = conn.execute(text("""
                SELECT
                    m.name as table_name,
                    il.name as index_name,
                    GROUP_CONCAT(ii.name) as columns
                FROM sqlite_master AS m,
                     pragma_index_list(m.name) AS il,
                     pragma_index_info(il.name) AS ii
                WHERE m.type = 'table'
                GROUP BY m.name, il.name
                ORDER BY m.name, il.name
            """))

            current_table = None
            for table_name, index_name, columns in result:
                if table_name != current_table:
                    print(f"\n{table_name}:")
                    current_table = table_name
                print(f"  - {index_name}: {columns}")

        except Exception as e:
            logger.error(f"Failed to check indexes: {e}")


def check_table_stats():
    """Check table statistics."""

    print("\n" + "="*80)
    print("TABLE STATISTICS")
    print("="*80)

    tables = ['tasks', 'agents', 'rewards', 'api_keys', 'users', 'verification_logs']

    with engine.connect() as conn:
        print(f"\n{'Table':<20} {'Row Count':<15}")
        print("-" * 40)

        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"{table:<20} {count:<15}")
            except Exception as e:
                print(f"{table:<20} ERROR: {e}")


def analyze_slow_queries():
    """Provide recommendations for slow queries."""

    print("\n" + "="*80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("="*80)

    recommendations = [
        {
            "query": "List tasks with filters",
            "issue": "Full table scan without proper indexes",
            "solution": "Add composite index on (status, created_at) and (task_type, created_at)",
            "index": "CREATE INDEX idx_task_status_created ON tasks(status, created_at DESC)"
        },
        {
            "query": "Get agent tasks",
            "issue": "Filtering by agent without composite index",
            "solution": "Add composite index on (agent, status, created_at)",
            "index": "CREATE INDEX idx_task_agent_status ON tasks(agent, status, created_at DESC)"
        },
        {
            "query": "Reward balance aggregation",
            "issue": "Aggregation without proper filtering index",
            "solution": "Add composite index on (agent, status)",
            "index": "CREATE INDEX idx_reward_agent_status ON rewards(agent, status)"
        },
        {
            "query": "Reward history",
            "issue": "Ordering by distributed_at without index",
            "solution": "Add index on distributed_at",
            "index": "CREATE INDEX idx_reward_distributed_at ON rewards(distributed_at DESC)"
        },
        {
            "query": "API key authentication",
            "issue": "Checking is_active without index",
            "solution": "Add composite index on (key, is_active)",
            "index": "CREATE INDEX idx_apikey_key_active ON api_keys(key, is_active)"
        },
    ]

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['query']}")
        print(f"   Issue: {rec['issue']}")
        print(f"   Solution: {rec['solution']}")
        print(f"   SQL: {rec['index']}")


if __name__ == "__main__":
    check_table_stats()
    check_indexes()
    check_common_queries()
    analyze_slow_queries()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETED")
    print("="*80)
    print("\nTo apply optimizations:")
    print("  python add_performance_indexes.py")
    print("\nTo benchmark performance:")
    print("  python benchmark_performance.py")
    print("="*80)
